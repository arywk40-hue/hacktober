"""Schema + quotes → independent retrieval → blind solve → support/agreement."""

from collections import Counter

from study.ingest import normalize, source_units
from study.models import StructuredOutputError
from study.retrieval import retrieve_evidence
from study.schemas import MCQQuestion, ShortQuestion, Solve, Verdict
from study.tracing import traced
from study.tutor import citation, evidence_payload


@traced("gen_ai.execute_tool", "Blind solve and support check")
def verify_candidate(models, question, supplied_units, retrieved):
    allowed = {u["id"]: u for u in supplied_units}
    if not set(question.source_unit_ids) <= set(allowed):
        return None, "Unknown source ID"
    for quote in question.supporting_quotes:
        if normalize(quote.quote) not in normalize(allowed[quote.source_unit_id]["text"]):
            return None, "Supporting quote is not present in the source"
    retrieved_ids = {u["id"] for u in retrieved}
    if not set(question.source_unit_ids) <= retrieved_ids:
        return None, "Independent retrieval did not recover supporting sources"
    # Key, rationale, quotes and generator annotations NEVER enter the blind solve payload.
    solved = models.structured("verifier", Solve,
        "Solve this question using only the retrieved evidence. For MCQ return exactly the correct option ID. "
        "For short answers give a concise answer. Set supported=false if it cannot be solved from evidence. "
        "Set unambiguous=false if the question has more than one defensible answer.",
        {"stem": question.stem, "type": question.type,
         "options": [{"id": o.id, "text": o.text} for o in question.options],
         "evidence": evidence_payload(retrieved)})
    if not solved.supported or not solved.unambiguous:
        return None, "Blind solver found insufficient evidence or ambiguity"
    if question.type == "mcq" and solved.answer.strip() != question.answer:
        return None, "Blind solver disagreed with the answer key"
    verdict = models.structured("verifier", Verdict,
        "Check that the proposed key and rationale are correct and entailed by the cited source quotes AND "
        "their source text. The independent blind answer must agree in meaning with the proposed key, "
        "including for short answers. Reject invented facts, missing assumptions, irrelevant quotes and ambiguity.",
        {"question": question.model_dump(), "blind_answer": solved.answer,
         "evidence": evidence_payload([allowed[i] for i in question.source_unit_ids])})
    if not verdict.supported:
        return None, "Key, rationale, or short-answer agreement failed the support check"
    return {"blind_solve": "pass", "source_support": "pass", "quotes": "exact after whitespace normalization",
            "generator": models.roles["generator"], "verifier": models.roles["verifier"]}, None


def generate_quiz(db, models, request, settings):
    units = source_units(db, request.subject_id, [request.document_id])
    with db.transaction() as session:
        source = db.get(session, "source", request.document_id)
        if request.page_end > source.payload["page_count"]:
            raise ValueError("Page range exceeds this PDF's page count")
    units = [u for u in units if request.page_start <= u["locator"]["page"] <= request.page_end]
    if not units:
        raise ValueError("This page range contains no selectable source text")
    accepted, rejected, stems = [], [], []
    for index in range(request.count):
        kind = request.types[index % len(request.types)]
        # Rotate small windows through the range rather than truncating one enormous model prompt.
        offset = index % len(units)
        supplied = (units[offset:] + units[:offset])[:1]
        aliases = {f"C{i + 1}": u["id"] for i, u in enumerate(supplied)}
        prompt_units = [{**u, "id": alias} for alias, u in zip(aliases, supplied, strict=True)]
        try:
            question = models.structured("generator", MCQQuestion if kind == "mcq" else ShortQuestion,
                "Generate ONE unambiguous study question using only supplied evidence. Use the requested type. "
                "The stem must be an actual question, never a source ID or a quote. "
                "For MCQ provide exactly four distinct options A, B, C, D and one correct answer ID. "
                "Ask for the best answer; distractors must contradict the source, not state partial truths. "
                "For short answer use options=[] and a concise answer. Include exact source IDs and a literal "
                "supporting quote (12–500 characters) for every cited source. Do not invent quotes. "
                "Keep the question, answer, and rationale concise. Avoid previous question stems.",
                {"type": kind, "evidence": evidence_payload(prompt_units), "avoid_stems": stems})
            if not set(question.source_unit_ids) <= set(aliases):
                rejected.append({"candidate": index + 1, "reason": "Unknown source ID"})
                continue
            question = question.model_copy(update={
                "source_unit_ids": [aliases[i] for i in question.source_unit_ids],
                "supporting_quotes": [q.model_copy(update={"source_unit_id": aliases[q.source_unit_id]})
                                      for q in question.supporting_quotes],
            })
            if question.type != kind:
                rejected.append({"candidate": index + 1, "reason": "Wrong question type"})
                continue
            if normalize(question.stem).casefold() in {normalize(s).casefold() for s in stems}:
                rejected.append({"candidate": index + 1, "reason": "Duplicate question"})
                continue
            # Fail unknown IDs and fabricated quotes before a blind model call or query embedding.
            supplied_ids = {u["id"]: u for u in supplied}
            if not set(question.source_unit_ids) <= set(supplied_ids):
                rejected.append({"candidate": index + 1, "reason": "Unknown source ID"})
                continue
            if any(normalize(q.quote) not in normalize(supplied_ids[q.source_unit_id]["text"])
                   for q in question.supporting_quotes):
                rejected.append({"candidate": index + 1, "reason": "Supporting quote is not present in the source"})
                continue
            query = question.stem + " " + " ".join(o.text for o in question.options)
            retrieved = retrieve_evidence(units, query, models, settings)
            verification, reason = verify_candidate(models, question, supplied, retrieved)
            if not verification:
                rejected.append({"candidate": index + 1, "reason": reason})
                continue
            references = [{**citation(supplied_ids[q.source_unit_id]), "quote": q.quote}
                          for q in question.supporting_quotes]
            accepted.append({**question.model_dump(), "citations": references, "verification": verification})
            stems.append(question.stem)
        except StructuredOutputError:
            rejected.append({"candidate": index + 1, "reason": "Invalid question or verifier schema"})
    result = {"requested": request.count, "accepted": len(accepted), "rejected": len(rejected),
              "questions": accepted, "rejections": rejected,
              "rejection_summary": dict(Counter(r["reason"] for r in rejected))}
    with db.transaction() as session:
        db.add(session, "quiz_run", request.subject_id, {"request": request.model_dump(), "result": result})
    return result
