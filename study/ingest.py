"""Page-preserving PDF extraction and atomic, in-process SQLite indexing."""

import hashlib
import re
import shutil

import pymupdf

from study.db import public, uid


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text, size=1600, overlap=200):
    if not 0 <= overlap < size or size < 100:
        raise ValueError("Chunk size must exceed overlap and be at least 100")
    text = text.strip()
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            boundary = max(text.rfind(" ", start + size // 2, end),
                           text.rfind("\n", start + size // 2, end))
            if boundary > start:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            yield chunk
        if end == len(text):
            break
        start = max(start + 1, end - overlap)


def extract_pdf(path):
    try:
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported")
            if not 1 <= len(doc) <= 300:
                raise ValueError("Choose a PDF with 1–300 pages")
            pages = [{"page": i + 1, "text": p.get_text("text", sort=True).strip()}
                     for i, p in enumerate(doc)]
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("This file could not be read as a PDF") from exc
    if not any(p["text"] for p in pages):
        raise ValueError("No selectable text found. Scan-only PDFs need OCR before upload")
    return pages


def ingest_pdf(db, models, settings, subject_id, upload):
    with db.transaction() as session:
        db.get(session, "course", subject_id)
    if not (upload.filename or "").lower().endswith(".pdf"):
        raise ValueError("Upload a PDF containing selectable text")
    source_id = uid()
    directory = settings.data_dir / "sources" / source_id
    directory.mkdir(parents=True)
    path = directory / "original.pdf"
    digest, total = hashlib.sha256(), 0
    committed = False
    try:
        with path.open("wb") as out:
            while block := upload.file.read(1024 * 1024):
                total += len(block)
                if total > settings.max_upload_mb * 1024 * 1024:
                    raise ValueError(f"PDF exceeds the {settings.max_upload_mb} MB upload limit")
                digest.update(block)
                out.write(block)
        if not total:
            raise ValueError("Empty PDF upload")
        with db.transaction() as session:
            existing = next((s for s in db.find(session, "source", subject_id)
                             if s.key == digest.hexdigest()), None)
            if existing:
                return public(existing)
        pages = extract_pdf(path)
        units = [{"id": uid(), "source_id": source_id, "text": text,
                  "locator": {"type": "page", "source_id": source_id, "page": page["page"]}}
                 for page in pages for text in chunk_text(page["text"])]
        if len(units) > 1200:
            raise ValueError("Document has more than 1,200 chunks; split it into smaller chapter PDFs")
        vectors = []
        for offset in range(0, len(units), 16):
            vectors.extend(models.embed([u["text"] for u in units[offset:offset + 16]]))
        with db.transaction() as session:
            db.get(session, "course", subject_id)
            source = db.add(session, "source", subject_id,
                            {"title": upload.filename, "status": "ready", "page_count": len(pages),
                             "unit_count": len(units), "sha256": digest.hexdigest(),
                             "blank_pages": [p["page"] for p in pages if not p["text"]]},
                            key=digest.hexdigest(), ident=source_id)
            for page in pages:
                db.add(session, "page", source_id, page, key=str(page["page"]))
            for unit, vector in zip(units, vectors, strict=True):
                db.add(session, "unit", source_id, {**unit, "embedding": vector,
                       "embedding_model": models.roles["embedding"]}, ident=unit["id"])
            result = public(source)
        committed = True
        return result
    finally:
        upload.file.close()
        if not committed:
            shutil.rmtree(directory, ignore_errors=True)


def source_units(db, subject_id, document_ids=None):
    with db.transaction() as session:
        db.get(session, "course", subject_id)
        sources = db.find(session, "source", subject_id)
        if document_ids and not set(document_ids) <= {s.id for s in sources}:
            raise ValueError("Selected documents must belong to this subject")
        return [{**public(u), "document_title": s.payload["title"]}
                for s in sources if s.payload["status"] == "ready"
                and (not document_ids or s.id in document_ids)
                for u in db.find(session, "unit", s.id)]
