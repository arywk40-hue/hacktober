import json

import httpx
import sentry_sdk
from conftest import FakeModels, pdf_bytes
from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from study.config import Settings
from study.main import create_app
from study.models import Models
from study.schemas import Verdict
from study.tracing import Tracing, stage

CANARY = "PRIVATE-NOTES-DO-NOT-SEND"
TEST_DSN = "https://public@example.invalid/1"


class MemoryTransport(Transport):
    def __init__(self):
        super().__init__()
        self.envelopes = []

    def capture_envelope(self, envelope):
        self.envelopes.append(envelope)

    @property
    def events(self):
        return [item.payload.json for envelope in self.envelopes for item in envelope.items]


def traced_app(tmp_path, monkeypatch, transport):
    # Inject only an in-memory transport: this exercises the real SDK without network access.
    monkeypatch.setattr("study.main.Tracing", lambda settings: Tracing(settings, transport=transport))
    settings = Settings(_env_file=None, data_dir=tmp_path, sentry_dsn=TEST_DSN)
    models = FakeModels(settings)
    app = create_app(settings, models)
    return app, models


def upload(client):
    subject = client.post("/api/subjects", json={"title": CANARY}).json()["id"]
    document = client.post("/api/documents", data={"subject_id": subject},
                           files={"file": (CANARY + ".pdf", pdf_bytes(
                               "Force equals mass times acceleration. " + CANARY), "application/pdf")}).json()
    return subject, document


def test_disabled_tracing_never_initializes_even_with_generic_sentry_dsn(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", TEST_DSN)
    monkeypatch.setattr(sentry_sdk, "Client", lambda **kw: (_ for _ in ()).throw(AssertionError("SDK init")))
    tracing = Tracing(Settings(_env_file=None, sentry_dsn=""))
    with tracing.request("tutor") as span:
        span.set_data("citetutor.outcome", "answered")
    assert tracing.status == "disabled" and tracing.client is None


def test_sdk_payload_allowlist_removes_content_scope_and_unexpected_spans():
    transport = MemoryTransport()
    tracing = Tracing(Settings(_env_file=None, sentry_dsn=TEST_DSN), transport=transport)
    try:
        with tracing.request("tutor") as span:
            sentry_sdk.set_user({"email": CANARY})
            sentry_sdk.set_context("private", {"text": CANARY})
            sentry_sdk.set_extra("answer", CANARY)
            sentry_sdk.set_tag("filename", CANARY)
            sentry_sdk.add_breadcrumb(message=CANARY)
            sentry_sdk.add_attachment(bytes=CANARY.encode(), filename=CANARY, add_to_transactions=True)
            sentry_sdk.capture_message(CANARY)
            span.set_data("citetutor.outcome", "answered")
            span.set_data("gen_ai.input.messages", CANARY)
            span.set_data("citetutor.attempts", CANARY)
            with stage("gen_ai.chat", "Ollama structured output") as child:
                child.set_data("gen_ai.usage.input_tokens", 12)
                child.set_data("gen_ai.output.messages", CANARY)
                child.set_data("gen_ai.request.model", CANARY)
            with sentry_sdk.start_span(op="http.client", name=CANARY):
                pass
        assert len(transport.events) == 1
        event = transport.events[0]
        assert CANARY not in "\n".join(e.serialize().decode() for e in transport.envelopes)
        assert set(event["contexts"]) == {"trace"}
        assert not {"user", "request", "extra", "tags", "breadcrumbs", "server_name"} & event.keys()
        assert len(event["spans"]) == 1
        assert event["spans"][0]["data"]["gen_ai.usage.input_tokens"] == 12
        assert event["start_timestamp"] and event["timestamp"] and event["event_id"]
    finally:
        tracing.close()


def test_actual_gateway_traces_token_usage_and_role_without_prompt_or_response():
    transport = MemoryTransport()
    tracing = Tracing(Settings(_env_file=None, sentry_dsn=TEST_DSN), transport=transport)
    models = Models(Settings(_env_file=None))

    def respond(request):
        if request.url.path == "/api/show":
            payload = json.loads(request.content)
            return httpx.Response(200, json={"model_info": {"general.architecture":
                                  "gemma3" if "gemma" in payload["model"] else "qwen2"}})
        return httpx.Response(200, json={"message": {"content": json.dumps(
            {"supported": True, "reason": CANARY})}, "prompt_eval_count": 321, "eval_count": 17})

    models.client.close()
    models.client = httpx.Client(base_url="http://127.0.0.1:11434", transport=httpx.MockTransport(respond))
    try:
        with tracing.request("tutor"):
            assert models.structured("verifier", Verdict, CANARY, {"evidence": CANARY}).supported
        child = transport.events[0]["spans"][0]
        assert child["data"]["gen_ai.usage.input_tokens"] == 321
        assert child["data"]["gen_ai.usage.output_tokens"] == 17
        assert child["data"]["citetutor.role"] == "verifier"
        assert CANARY not in transport.envelopes[0].serialize().decode()
    finally:
        models.close()
        tracing.close()


def test_refusal_trace_records_three_rejections_without_questions(tmp_path, monkeypatch):
    transport = MemoryTransport()
    app, models = traced_app(tmp_path, monkeypatch, transport)
    models.reject = True
    with TestClient(app) as client:
        subject, document = upload(client)
        result = client.post("/api/chat", json={"subject_id": subject, "document_ids": [document["id"]],
                                                "message": "Explain force " + CANARY}).json()
        assert result["declined"] and result["attempts"] == 3
        assert client.get("/api/health").json()["tracing"]["status"] == "enabled"
    event = transport.events[0]
    assert event["contexts"]["trace"]["data"]["citetutor.outcome"] == "refused"
    assert event["contexts"]["trace"]["data"]["citetutor.attempts"] == 3
    rejections = [s for s in event["spans"] if s["description"] == "Draft rejected"]
    assert [s["data"]["citetutor.attempt"] for s in rejections] == [1, 2, 3]
    assert all(s["data"]["citetutor.rejection"] == "unsupported_answer" for s in rejections)
    assert CANARY not in transport.envelopes[0].serialize().decode()


def test_quiz_trace_reports_disagreement_and_rejected_count(tmp_path, monkeypatch):
    transport = MemoryTransport()
    app, models = traced_app(tmp_path, monkeypatch, transport)
    models.disagree = True
    with TestClient(app) as client:
        subject, document = upload(client)
        result = client.post("/api/quizzes", json={"subject_id": subject, "document_id": document["id"],
            "page_start": 1, "page_end": 1, "count": 2, "types": ["mcq"]}).json()
    assert result["accepted"] == 0 and result["rejected"] == 2
    event = transport.events[0]
    assert event["contexts"]["trace"]["data"]["citetutor.rejected"] == 2
    assert len([s for s in event["spans"] if s["description"] == "Blind solve and support check"]) == 2
    assert len([s for s in event["spans"] if s["data"].get("citetutor.rejection") == "key_disagreement"]) == 2
    assert CANARY not in transport.envelopes[0].serialize().decode()


def test_failed_transport_preserves_answer_and_disabled_app_isolation(tmp_path, monkeypatch):
    class FailedTransport(Transport):
        def capture_envelope(self, envelope):
            raise RuntimeError("Network unavailable")

    app, _ = traced_app(tmp_path, monkeypatch, FailedTransport())
    with TestClient(app) as client:
        subject, _ = upload(client)
        result = client.post("/api/chat", json={"subject_id": subject, "message": "Explain force"}).json()
        assert not result["declined"] and result["segments"][0]["citations"]
    assert not sentry_sdk.get_client().is_active()
    disabled = Tracing(Settings(_env_file=None, sentry_dsn=""))
    with disabled.request("tutor"):
        assert not sentry_sdk.get_client().is_active()
