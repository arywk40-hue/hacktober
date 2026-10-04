import atexit
import os
import shutil
import subprocess
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import StaleDataError

from study.assessment import generate_quiz
from study.config import Settings
from study.db import Database, Record, public
from study.ingest import ingest_pdf
from study.models import ModelError, Models
from study.schemas import ChatRequest, QuizRequest, Schema
from study.tracing import Tracing, quiz_rejections
from study.tutor import answer

STATIC = Path(__file__).parent / "static"


class SubjectRequest(Schema):
    title: str = Field(min_length=1, max_length=120)


def create_app(settings=None, model_client=None, tracing_client=None):
    settings = settings or Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    db = Database(settings.database_url)
    models = model_client or Models(settings)
    tracing = tracing_client or Tracing(settings)
    operation_lock = threading.Lock()

    @contextmanager
    def study_operation():
        if not operation_lock.acquire(blocking=False):
            raise HTTPException(409, "A study request is already running; please wait for it to finish")
        try:
            yield
        finally:
            operation_lock.release()

    @asynccontextmanager
    async def lifespan(app):
        db.create()
        yield
        if model_client is None:
            models.close()
        db.engine.dispose()
        tracing.close()

    app = FastAPI(title="CiteTutor", version="0.2.0", lifespan=lifespan)
    app.state.db, app.state.models = db, models
    app.state.tracing = tracing
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    @app.exception_handler(LookupError)
    async def missing(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.exception_handler(ModelError)
    async def unavailable(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=503)

    @app.exception_handler(StaleDataError)
    @app.exception_handler(IntegrityError)
    async def conflict(request, exc):
        return JSONResponse({"detail": "Concurrent update; refresh and retry"}, status_code=409)

    @app.get("/")
    def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "models": models.health(), "storage": "SQLite", "processing": "in-process",
                "tracing": {"status": tracing.status, "content_capture": False}}

    @app.get("/api/subjects")
    def subjects():
        with db.transaction() as session:
            return [{**public(s), "document_count": len(db.find(session, "source", s.id))}
                    for s in db.find(session, "course")]

    @app.post("/api/subjects", status_code=201)
    def new_subject(request: SubjectRequest):
        with db.transaction() as session:
            return public(db.add(session, "course", "local", {"title": request.title}))

    @app.get("/api/subjects/{subject_id}/documents")
    def documents(subject_id: str):
        with db.transaction() as session:
            db.get(session, "course", subject_id)
            return [public(s) for s in db.find(session, "source", subject_id)]

    @app.post("/api/documents", status_code=201)
    def upload(subject_id: Annotated[str, Form()], file: Annotated[UploadFile, File()]):
        with study_operation():
            return ingest_pdf(db, models, settings, subject_id, file)

    @app.get("/api/documents/{document_id}/pages/{page}")
    def page_text(document_id: str, page: int):
        with db.transaction() as session:
            source = db.get(session, "source", document_id)
            stored = next((p for p in db.find(session, "page", document_id) if p.key == str(page)), None)
            if stored is None:
                raise LookupError("Page not found")
            return {"document_id": document_id, "title": source.payload["title"], **stored.payload}

    @app.delete("/api/documents/{document_id}")
    def remove_document(document_id: str):
        with study_operation():
            with db.transaction() as session:
                source = db.get(session, "source", document_id)
                session.execute(delete(Record).where(Record.scope == document_id))
                session.delete(source)
            shutil.rmtree(settings.data_dir / "sources" / document_id, ignore_errors=True)
        return {"deleted": document_id}

    @app.post("/api/chat")
    def chat(request: ChatRequest):
        with study_operation(), tracing.request("tutor") as span:
            result = answer(db, models, request, settings)
            span.set_data("citetutor.outcome", "refused" if result["declined"] else "answered")
            span.set_data("citetutor.attempts", result["attempts"])
            return result

    @app.post("/api/quizzes")
    def quiz(request: QuizRequest):
        with study_operation(), tracing.request("quiz") as span:
            result = generate_quiz(db, models, request, settings)
            span.set_data("citetutor.outcome", "completed")
            for key in ("requested", "accepted", "rejected"):
                span.set_data(f"citetutor.{key}", result[key])
            quiz_rejections(result)
            return result

    return app


def ensure_ollama(settings):
    def reachable():
        try:
            return httpx.get(settings.ollama_url + "/api/tags", timeout=2, trust_env=False).is_success
        except httpx.HTTPError:
            return False

    if reachable():
        return
    executable = shutil.which("ollama")
    if not executable:
        raise SystemExit("Install Ollama, pull the three models listed in README.md, then run again")
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    log = (settings.data_dir / "ollama.log").open("a")
    proc = subprocess.Popen([executable, "serve"], stdout=log, stderr=log,
                            env={**os.environ, "OLLAMA_HOST": settings.ollama_url, "OLLAMA_NO_CLOUD": "1"})
    atexit.register(proc.terminate)
    for _ in range(40):
        if reachable():
            log.close()
            return
        if proc.poll() is not None:
            break
        time.sleep(0.25)
    log.close()
    raise SystemExit("Ollama did not start; inspect data/ollama.log")


def run():
    import uvicorn

    settings = Settings()
    ensure_ollama(settings)
    models = Models(settings)
    try:
        status = models.health()
    finally:
        models.close()
    if not status["ready"]:
        for role in status["roles"].values():
            if not role["ready"]:
                print(role["error"])
        raise SystemExit("Install/configure the local weights first; see README.md")
    print("CiteTutor: http://127.0.0.1:8000 — local study help")
    uvicorn.run(create_app(settings), host="127.0.0.1", port=8000)
