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


def extract_pdf(path, *, allow_scans=False, force_scan=False):
    try:
        with pymupdf.open(path) as doc:
            if doc.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported")
            if not 1 <= len(doc) <= 300:
                raise ValueError("Choose a PDF with 1–300 pages")
            pages = []
            for i, page in enumerate(doc):
                text = page.get_text("text", sort=True).strip()
                has_visuals = bool(page.get_images() or page.get_drawings())
                scan = allow_scans and ((force_scan and (text or has_visuals))
                                        or (len(normalize(text)) < 80 and has_visuals))
                pages.append({"page": i + 1, "text": "" if scan else text,
                              "extraction": "local_ocr" if scan else "selectable_text",
                              "reviewed": not scan})
    except (pymupdf.FileDataError, RuntimeError) as exc:
        raise ValueError("This file could not be read as a PDF") from exc
    if not any(p["text"] or (allow_scans and not p["reviewed"]) for p in pages):
        raise ValueError("No selectable text found. Scan-only PDFs need OCR before upload")
    if sum(not p["reviewed"] for p in pages) > 20:
        raise ValueError("Split scanned notes into PDFs with at most 20 scanned pages")
    return pages


def page_image(path, page_number):
    with pymupdf.open(path) as doc:
        if not 1 <= page_number <= len(doc):
            raise LookupError("Page not found")
        page = doc[page_number - 1]
        zoom = min(2, 1600 / max(page.rect.width, page.rect.height))
        return page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), colorspace=pymupdf.csRGB,
                               alpha=False).tobytes("png")


def index_units(models, source_id, pages):
    units = [{"id": uid(), "source_id": source_id, "text": text,
              "locator": {"type": "page", "source_id": source_id, "page": page["page"]}}
             for page in pages for text in chunk_text(page["text"])]
    if len(units) > 1200:
        raise ValueError("Document has more than 1,200 chunks; split it into smaller chapter PDFs")
    if not units:
        raise ValueError("No readable text remains; exclude this document from study")
    vectors = []
    for offset in range(0, len(units), 16):
        vectors.extend(models.embed([u["text"] for u in units[offset:offset + 16]]))
    return [{**unit, "embedding": vector, "embedding_model": models.roles["embedding"]}
            for unit, vector in zip(units, vectors, strict=True)]


def ingest_pdf(db, models, settings, subject_id, upload, *, force_scan=False):
    with db.transaction() as session:
        db.get(session, "course", subject_id)
    if not (upload.filename or "").lower().endswith(".pdf"):
        raise ValueError("Upload notes or scans as a PDF")
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
        pages = extract_pdf(path, allow_scans=True, force_scan=force_scan)
        needs_review = any(not p["reviewed"] for p in pages)
        units = [] if needs_review else index_units(models, source_id, pages)
        with db.transaction() as session:
            db.get(session, "course", subject_id)
            source = db.add(session, "source", subject_id,
                            {"title": upload.filename, "status": "needs_review" if needs_review else "ready",
                             "page_count": len(pages), "ocr_pages": [p["page"] for p in pages if not p["reviewed"]],
                             "unit_count": len(units), "sha256": digest.hexdigest(),
                             "blank_pages": [p["page"] for p in pages if not p["text"]]},
                            key=digest.hexdigest(), ident=source_id)
            for page in pages:
                db.add(session, "page", source_id, page, key=str(page["page"]))
            for unit in units:
                db.add(session, "unit", source_id, unit, ident=unit["id"])
            result = public(source)
        committed = True
        return result
    finally:
        upload.file.close()
        if not committed:
            shutil.rmtree(directory, ignore_errors=True)


def review_document(db, models, document_id, request):
    """Index only human-approved scan text; embedding failures leave the review intact."""
    with db.transaction() as session:
        source = db.get(session, "source", document_id)
        if source.payload["status"] != "needs_review" or source.version != request.version:
            raise ValueError("Review changed or already approved; reopen the document")
        rows = db.find(session, "page", document_id)
        pages = [dict(p.payload) for p in rows]
        needed = {p["page"] for p in pages if not p["reviewed"]}
    supplied = {p.page: p.text for p in request.pages}
    if len(supplied) != len(request.pages) or set(supplied) != needed:
        raise ValueError("Review every scanned page exactly once; do not change selectable-text pages")
    if any("[unclear]" in text.casefold() for text in supplied.values()):
        raise ValueError("Correct [unclear] markers or remove unreadable lines before approval")
    for page in pages:
        if page["page"] in supplied:
            page.update(text=supplied[page["page"]], reviewed=True, review="approved")
    units = index_units(models, document_id, pages)
    with db.transaction() as session:
        source = db.get(session, "source", document_id)
        if source.version != request.version or source.payload["status"] != "needs_review":
            raise ValueError("Review changed; reopen the document")
        for row, payload in zip(db.find(session, "page", document_id), pages, strict=True):
            if row.payload["page"] != payload["page"]:
                raise ValueError("Page order changed; reopen the document")
            row.payload = payload
        for unit in units:
            db.add(session, "unit", document_id, unit, ident=unit["id"])
        source.payload = {**source.payload, "status": "ready", "unit_count": len(units),
                          "blank_pages": [p["page"] for p in pages if not p["text"]]}
        result = public(source)
    return result


def source_units(db, subject_id, document_ids=None):
    with db.transaction() as session:
        db.get(session, "course", subject_id)
        sources = db.find(session, "source", subject_id)
        if document_ids and not set(document_ids) <= {s.id for s in sources}:
            raise ValueError("Selected documents must belong to this subject")
        if document_ids and any(s.id in document_ids and s.payload["status"] != "ready" for s in sources):
            raise ValueError("Review and approve scanned text before studying this PDF")
        return [{**public(u), "document_title": s.payload["title"]}
                for s in sources if s.payload["status"] == "ready"
                and (not document_ids or s.id in document_ids)
                for u in db.find(session, "unit", s.id)]
