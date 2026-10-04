from io import BytesIO

import pytest
from conftest import pdf_bytes
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from study.ingest import chunk_text, extract_pdf, ingest_pdf
from study.retrieval import cosine, fuse, lexical_ranking
from study.schemas import Question
from study.tutor import REFUSAL, parse_page_citations


def ask(context, **overrides):
    client, _, subject, _, _ = context
    return client.post("/api/chat", json={"subject_id": subject, "message": "What defines force?", **overrides})


def quiz(context, **overrides):
    client, _, subject, document, _ = context
    return client.post("/api/quizzes", json={"subject_id": subject, "document_id": document["id"],
                                           "page_start": 1, "page_end": 1, "count": 1,
                                           "types": ["mcq"], **overrides})


def test_chunks_bound_length_and_preserve_words():
    words = [f"word{i}" for i in range(900)]
    chunks = list(chunk_text(" ".join(words)))
    assert len(chunks) > 1 and all(len(c) <= 1600 for c in chunks)
    combined = " ".join(chunks)
    assert all(word in combined for word in words)
    assert set(chunks[0].split()) & set(chunks[1].split())


def test_empty_chunk_and_invalid_overlap():
    assert list(chunk_text("  \n ")) == []
    with pytest.raises(ValueError):
        list(chunk_text("text", size=100, overlap=100))


def test_extraction_preserves_physical_pages_including_blank(tmp_path):
    path = tmp_path / "pages.pdf"
    path.write_bytes(pdf_bytes("First page", "", "Third page"))
    pages = extract_pdf(path)
    assert [p["page"] for p in pages] == [1, 2, 3]
    assert pages[1]["text"] == "" and "Third" in pages[2]["text"]


def test_scanned_or_empty_text_pdf_refuses_extraction(tmp_path):
    path = tmp_path / "blank.pdf"
    path.write_bytes(pdf_bytes(""))
    with pytest.raises(ValueError, match="OCR"):
        extract_pdf(path)


def test_citation_parser():
    assert parse_page_citations("notes.pdf [p. 12] and [p. 3]") == [12, 3]
    assert parse_page_citations("[p. 0] [p. -1] [page 12] [p. two]") == []


def test_answer_has_verified_citations_and_page_text(context):
    client, models, _, document, _ = context
    response = ask(context)
    assert response.status_code == 200
    result = response.json()
    assert not result["declined"] and parse_page_citations(result["answer"])
    for segment in result["segments"]:
        for citation in segment["citations"]:
            assert citation["document_id"] == document["id"]
            assert citation["document_title"] == "notes.pdf"
            assert client.get(citation["url"]).json()["page"] == citation["page"]
    assert any(role == "verifier" and schema.__name__ == "Verdict" for role, schema, _ in models.calls)


def test_out_of_scope_refusal(context):
    response = ask(context, message="What pizza should I order?").json()
    assert response["declined"] and response["answer"] == REFUSAL and response["segments"] == []


def test_formula_alone_retries_then_refuses_explicit_value_request(context):
    _, models, _, _, _ = context
    result = ask(context, message="Calculate the force. Give the value and unit.").json()
    assert result["declined"] and result["attempts"] == 3 and not result["segments"]
    drafts = [p for _, schema, p in models.calls if schema.__name__ == "NumericalDraft"]
    assert len(drafts) == 3 and "numerical result" in drafts[1]["previous_failures"][0]


def test_hint_can_omit_requested_solution_value(context):
    result = ask(context, message="Calculate the force. Give the value and unit.", mode="hint").json()
    assert not result["declined"] and result["segments"]


def test_numeric_result_is_verified_before_display(context, monkeypatch):
    from study.schemas import NumericalDraft, Verdict
    client, models, subject, _, _ = context
    document = client.post("/api/documents", data={"subject_id": subject},
        files={"file": ("worked.pdf", pdf_bytes("A 2 kg body accelerating at 4 m/s^2 has net force 8 N."))}).json()
    original = models.structured

    def structured(role, schema, instruction, payload):
        if schema is NumericalDraft:
            return NumericalDraft(answerable=True, segments=[{"text": "Using F = m a.",
                "citations": [payload["evidence"][0]["id"]]}], quantity={"value": 8, "unit": "N"})
        if schema is Verdict:
            assert "Result: 8 N." in payload["answer"]
        return original(role, schema, instruction, payload)

    monkeypatch.setattr(models, "structured", structured)
    result = ask(context, message="Calculate the force. Give the value and unit.",
                 document_ids=[document["id"]]).json()
    assert not result["declined"] and "Result: 8 N." in result["answer"]


def test_tutor_blind_read_never_sees_draft_or_learner_style_and_can_block(context, monkeypatch):
    from study.schemas import Solve

    _, models, _, _, _ = context
    original = models.structured
    seen = []

    def structured(role, schema, instruction, payload):
        if schema is Solve:
            assert role == "verifier"
            assert not {"answer", "blind_answer", "explanation_style", "segments"} & payload.keys()
            seen.append(payload)
            return Solve(answer="", supported=False, unambiguous=False, reason="Cannot answer this question")
        return original(role, schema, instruction, payload)

    monkeypatch.setattr(models, "structured", structured)
    result = ask(context).json()
    assert result["declined"] and result["segments"] == [] and len(seen) == 3
    assert not any(schema.__name__ == "Verdict" for _, schema, _ in models.calls)


def test_numeric_result_missing_from_cited_source_never_passes(context, monkeypatch):
    from study.schemas import NumericalDraft
    _, models, _, _, _ = context
    original = models.structured

    def structured(role, schema, instruction, payload):
        if schema is NumericalDraft:
            return NumericalDraft(answerable=True, segments=[{"text": "The momentum is 6 kg m/s.",
                "citations": [payload["evidence"][0]["id"]]}], quantity={"value": 6, "unit": "kg m/s"})
        return original(role, schema, instruction, payload)

    monkeypatch.setattr(models, "structured", structured)
    result = ask(context, message="Calculate momentum. Give the value and unit.").json()
    assert result["declined"] and result["attempts"] == 3 and result["segments"] == []


@pytest.mark.parametrize("failure", ["bad_citation", "reject", "invalid_draft"])
def test_max_three_drafts_and_no_partial_display(context, failure):
    _, models, _, _, _ = context
    setattr(models, failure, True)
    result = ask(context).json()
    assert result["declined"] and result["attempts"] == 3 and result["segments"] == []
    assert sum(schema.__name__ == "Draft" for _, schema, _ in models.calls) == 3


def test_explanation_style_never_enters_verifier_evidence(context):
    _, models, _, _, _ = context
    ask(context, style="detailed", mode="explain")
    verdict_calls = [payload for _, schema, payload in models.calls if schema.__name__ == "Verdict"]
    assert verdict_calls and all("explanation_style" not in p for p in verdict_calls)


def test_multiple_pdfs_and_cross_subject_document_rejected(context):
    client, _, subject, _, _ = context
    second = client.post("/api/documents", data={"subject_id": subject},
                         files={"file": ("chapter.pdf", pdf_bytes("Momentum equals mass times velocity."))})
    assert second.status_code == 201
    assert len(client.get(f"/api/subjects/{subject}/documents").json()) == 2
    other = client.post("/api/subjects", json={"title": "Chemistry"}).json()["id"]
    result = client.post("/api/chat", json={"subject_id": other, "message": "Force?",
                                          "document_ids": [second.json()["id"]]})
    assert result.status_code == 400


def test_deduplicated_upload_and_delete(context):
    client, _, subject, document, _ = context
    result = client.post("/api/documents", data={"subject_id": subject}, files={"file": (
        "renamed.pdf", pdf_bytes("Force equals mass times acceleration.",
                                 "Kinetic energy is half mass times speed squared."))})
    # PDFs contain random document IDs, so use the stored original for exact byte deduplication.
    app = context[4]
    original = (app.state.models.settings.data_dir / "sources" / document["id"] / "original.pdf").read_bytes()
    same = client.post("/api/documents", data={"subject_id": subject}, files={"file": ("same.pdf", original)})
    assert result.status_code == 201 and same.json()["id"] == document["id"]
    assert client.delete(f"/api/documents/{document['id']}").status_code == 200
    assert client.get(f"/api/documents/{document['id']}/pages/1").status_code == 404


def test_failed_index_leaves_no_source_or_file(context):
    _, models, subject, _, app = context
    models.embed_error = True
    upload = UploadFile(file=BytesIO(pdf_bytes("A new source on electric charge.")), filename="new.pdf")
    before = list((models.settings.data_dir / "sources").iterdir())
    with pytest.raises(RuntimeError, match="outage"):
        ingest_pdf(app.state.db, models, models.settings, subject, upload)
    assert list((models.settings.data_dir / "sources").iterdir()) == before
    assert upload.file.closed


def test_verified_quiz_has_exact_quotes_and_blind_payload(context):
    _, models, _, _, _ = context
    result = quiz(context).json()
    assert result["accepted"] == 1 and result["rejected"] == 0
    assert result["questions"][0]["citations"][0]["quote"]
    solve = [p for _, schema, p in models.calls if schema.__name__ == "Solve"]
    assert len(solve) == 1 and not {"answer", "rationale", "supporting_quotes"} & solve[0].keys()


@pytest.mark.parametrize("failure,reason", [("bad_quote", "quote"), ("disagree", "disagreed"),
                                           ("reject", "support check")])
def test_rejected_quiz_never_displayed_and_counted(context, failure, reason):
    _, models, _, _, _ = context
    setattr(models, failure, True)
    result = quiz(context).json()
    assert result["questions"] == [] and result["rejected"] == 1 and result["accepted"] == 0
    assert reason in result["rejections"][0]["reason"]


def test_quiz_scope_and_range(context):
    assert quiz(context, page_end=50).status_code == 422
    assert quiz(context, page_end=3).status_code == 400
    assert quiz(context, types=["short"]).json()["accepted"] == 1


def test_hybrid_ranking_and_embedding_change():
    units = [{"id": "a", "text": "force mass acceleration"}, {"id": "b", "text": "chemistry atoms"}]
    assert lexical_ranking(units, "force")[0][0] == "a"
    assert fuse(units, [[("stale", 1), ("a", 0.2)]], 3)[0]["id"] == "a"
    with pytest.raises(ValueError, match="embedding model changed"):
        cosine([1, 0], [1])


def test_question_rejects_invalid_mcq_and_missing_quote():
    with pytest.raises(ValidationError):
        Question(type="mcq", stem="Question?", options=[], answer="Z", rationale="Unsupported",
                 source_unit_ids=["one"], supporting_quotes=[])


def test_unknown_quiz_source_rejected_before_blind_solve(context):
    _, models, _, _, _ = context
    models.bad_quiz_source = True
    result = quiz(context).json()
    assert result["rejected"] == 1 and result["questions"] == []
    assert not any(schema.__name__ == "Solve" for _, schema, _ in models.calls)


def test_empty_subject_refuses_without_inference(context):
    client, models, _, _, _ = context
    subject = client.post("/api/subjects", json={"title": "Empty"}).json()["id"]
    before = len(models.calls)
    result = client.post("/api/chat", json={"subject_id": subject, "message": "Explain something"}).json()
    assert result["declined"] and result["answer"] == REFUSAL and len(models.calls) == before


def test_embedding_model_swap_requires_reindex(context):
    _, models, _, _, _ = context
    models.roles["embedding"] = "new-embedding-model"
    result = ask(context)
    assert result.status_code == 503 and "Re-upload" in result.json()["detail"]
