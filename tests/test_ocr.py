import base64
import json

import httpx
import pymupdf
import pytest
from conftest import pdf_bytes

from study.ingest import extract_pdf, source_units
from study.models import ModelError, Models, StructuredOutputError
from study.schemas import Transcription


def scanned_bytes(*, mixed=False, count=1):
    # Rasterized printed fixture tests the scan boundary, not handwriting accuracy.
    with pymupdf.open(stream=pdf_bytes("Force equals mass times acceleration."), filetype="pdf") as text:
        image = text[0].get_pixmap().tobytes("png")
    with pymupdf.open() as doc:
        if mixed:
            doc.new_page().insert_text((50, 50), "Selectable first page about physics.")
        for _ in range(count):
            page = doc.new_page()
            page.insert_image(page.rect, stream=image)
        return doc.tobytes()


def upload_scan(context, **kwargs):
    client, _, subject, _, _ = context
    response = client.post("/api/documents", data={"subject_id": subject},
                           files={"file": ("scan.pdf", scanned_bytes(**kwargs), "application/pdf")})
    assert response.status_code == 201
    return response.json()


def test_scan_stays_out_of_retrieval_until_all_pages_approved(context):
    client, models, subject, _, app = context
    doc = upload_scan(context, mixed=True)
    assert doc["status"] == "needs_review" and doc["unit_count"] == 0 and doc["ocr_pages"] == [2]
    assert not any(u["source_id"] == doc["id"] for u in source_units(app.state.db, subject))
    with pytest.raises(ValueError, match="Review"):
        source_units(app.state.db, subject, [doc["id"]])
    seen = []
    models.transcribe = lambda image: seen.append(image) or Transcription(text="Force equals mass times acceleration.")
    draft = client.post(f'/api/documents/{doc["id"]}/pages/2/ocr')
    assert draft.status_code == 200 and draft.json()["reviewed"] is False
    assert seen[0].startswith(b"\x89PNG")
    review = client.get(f'/api/documents/{doc["id"]}/review').json()
    assert len(review["pages"]) == 1 and review["pages"][0]["page"] == 2
    result = client.post(f'/api/documents/{doc["id"]}/review', json={
        "version": review["version"], "pages": [{"page": 2, "text": "Force equals mass times acceleration."}]})
    assert result.status_code == 200 and result.json()["status"] == "ready"
    units = source_units(app.state.db, subject, [doc["id"]])
    assert {u["locator"]["page"] for u in units} == {1, 2}
    page = client.get(f'/api/documents/{doc["id"]}/pages/2').json()
    assert page["review"] == "human_approved" and page["ocr_model"] == "gemma3:4b"
    chat = client.post("/api/chat", json={"subject_id": subject, "document_ids": [doc["id"]],
                                         "message": "What defines force?"}).json()
    assert not chat["declined"] and chat["segments"][0]["citations"][0]["page"] in {1, 2}
    assert client.post(f'/api/documents/{doc["id"]}/pages/2/ocr').status_code == 400
    image = client.get(f'/api/documents/{doc["id"]}/pages/2/image')
    assert image.status_code == 200 and image.headers["content-type"] == "image/png"
    assert client.get(f'/api/documents/{doc["id"]}/pages/0/image').status_code == 404


@pytest.mark.parametrize("pages", [[], [{"page": 1, "text": "[unclear]"}],
                                    [{"page": 2, "text": "Wrong physical page"}],
                                    [{"page": 1, "text": ""}],
                                    [{"page": 1, "text": "A"}, {"page": 1, "text": "B"}]])
def test_bad_or_empty_reviews_do_not_index(context, pages):
    client, _, subject, _, app = context
    doc = upload_scan(context)
    response = client.post(f'/api/documents/{doc["id"]}/review', json={"version": 1, "pages": pages})
    assert response.status_code in {400, 422}
    assert not any(u["source_id"] == doc["id"] for u in source_units(app.state.db, subject))
    assert client.get(f'/api/documents/{doc["id"]}/review').json()["document"]["status"] == "needs_review"


def test_failed_review_embeddings_preserve_pending_document(context):
    client, models, subject, _, app = context
    doc = upload_scan(context)
    models.embed_error = True
    with pytest.raises(RuntimeError, match="outage"):
        client.post(f'/api/documents/{doc["id"]}/review', json={
            "version": 1, "pages": [{"page": 1, "text": "Force equals mass times acceleration."}]})
    assert client.get(f'/api/documents/{doc["id"]}/review').json()["version"] == 1
    assert not any(u["source_id"] == doc["id"] for u in source_units(app.state.db, subject))


def test_scan_limit_and_explicit_ocr_for_text_layer(tmp_path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(scanned_bytes(count=21))
    with pytest.raises(ValueError, match="20 scanned"):
        extract_pdf(path, allow_scans=True)
    path.write_bytes(pdf_bytes("A poor existing OCR layer"))
    assert extract_pdf(path, allow_scans=True)[0]["reviewed"]
    assert not extract_pdf(path, allow_scans=True, force_scan=True)[0]["reviewed"]


@pytest.mark.parametrize("vision, truncated", [(True, False), (False, False), (True, True)])
def test_vision_gateway_capabilities_and_no_partial_transcription(context, vision, truncated):
    settings = context[1].settings
    models = Models(settings)
    calls = []

    def respond(request):
        body = json.loads(request.content)
        calls.append((request.url.path, body))
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"model_info": {"general.architecture": "gemma3"},
                                            "capabilities": ["vision"] if vision else ["completion"]})
        return httpx.Response(200, json={"message": {"content": '{"text":"A [unclear] equation"}'},
                                        "done_reason": "length" if truncated else "stop"})

    models.client.close()
    models.client = httpx.Client(base_url=settings.ollama_url, transport=httpx.MockTransport(respond))
    try:
        if not vision:
            with pytest.raises(ModelError, match="vision"):
                models.transcribe(b"private image")
            assert len(calls) == 1
        elif truncated:
            with pytest.raises(StructuredOutputError, match="truncated"):
                models.transcribe(b"private image")
        else:
            assert models.transcribe(b"private image").text == "A [unclear] equation"
            body = calls[-1][1]
            assert base64.b64decode(body["messages"][0]["images"][0]) == b"private image"
            assert body["stream"] is False and body["keep_alive"] == 0
    finally:
        models.close()
