"""Only complete, independently supported drafts reach the client."""

import re

from study.ingest import normalize, source_units
from study.models import StructuredOutputError
from study.retrieval import retrieve_evidence
from study.schemas import Draft, NumericalDraft, Solve, Verdict
from study.tracing import record, rejection

REFUSAL = "Not enough evidence in this document"


def evidence_payload(units):
    return [{"id": u["id"], "text": u["text"], "page": u["locator"]["page"],
             "document": u.get("document_title", "PDF")} for u in units]


def parse_page_citations(text):
    return [int(p) for p in re.findall(r"\[p\.\s*([1-9]\d*)\]", text)]


def source_contains_quantity(quantity, units):
    value = re.escape(f"{quantity.value:.15g}")
    pattern = rf"(?<![\d.]){value}(?:\.0+)?\s*{re.escape(normalize(quantity.unit))}(?!\w)"
    return any(re.search(pattern, normalize(u["text"]), re.I) for u in units)


def citation(unit):
    page = unit["locator"]["page"]
    return {"unit_id": unit.get("stored_id", unit["id"]), "document_id": unit["source_id"],
            "document_title": unit.get("document_title", "PDF"), "page": page,
            "label": f"[p. {page}]", "url": f"/api/documents/{unit['source_id']}/pages/{page}"}


def refuse(attempts=0, failures=None):
    return {"declined": True, "reason": REFUSAL, "answer": REFUSAL, "segments": [],
            "attempts": attempts, "verification_failures": failures or []}


def answer(db, models, request, settings=None):
    settings = settings or models.settings
    units = source_units(db, request.subject_id, request.document_ids)
    if not units:
        return refuse()
    retrieved = retrieve_evidence(units, request.message, models, settings)
    # Short per-request IDs are losslessly mapped to authoritative stored chunks.
    # They reduce model copying errors without letting a model invent citation targets.
    prompt_units = [{**u, "stored_id": u["id"], "id": f"C{i + 1}"} for i, u in enumerate(retrieved)]
    allowed = {u["id"]: u for u in prompt_units}
    context = {"evidence": evidence_payload(prompt_units), "query": request.message,
               "mode": request.mode, "explanation_style": request.style}
    failures = []
    numerical = request.mode != "hint" and bool(re.search(r"\bvalue\s+and\s+unit\b", request.message, re.I))
    for attempt in range(1, 4):
        record(**{"citetutor.attempt": attempt})
        try:
            draft = models.structured("generator", NumericalDraft if numerical else Draft,
                "Answer ALL requested parts using only evidence. If a value and unit are requested, explicitly "
                "copy the worked result and its literal unit from the cited source into the quantity fields. "
                "Numerical answers must be explicitly present in that source; do not perform new calculations. "
                "The quantity must be the requested result, not an input value. Use quantity=null when refusing. "
                "Return ONE concise answer paragraph, "
                "Start with the direct answer to the requested question, without extra facts or unrequested "
                "derivations. A definition/function question needs the meaning or purpose, not initialization. "
                "Cite the exact supplied "
                "chunk ID (C1, C2, etc.) of the SINGLE best supporting chunk in the citations list. "
                "Put source IDs only in the citations list, never in answer text. Do not write page labels in text. "
                "If evidence is insufficient, set answerable=false and segments=[]. "
                "Mode explain asks for an explanation, mode hint asks for a helpful hint rather than a solution. "
                "Explanation style changes wording only and is NEVER factual evidence.", context)
            if not draft.answerable or not draft.segments:
                rejection("generator_declined", attempt)
                return refuse(attempt, ["Generator declined to draft a supported answer"])
            failures = []
            if numerical and draft.quantity is None:
                rejection("missing_quantity", attempt)
                context["previous_failures"] = ["Include the numerical result and its unit, not just the formula"]
                continue
            for segment in draft.segments:
                if (not segment.citations or any(c not in allowed for c in segment.citations)
                        or "[p." in segment.text.casefold()):
                    rejection("invalid_citation", attempt)
                    failures.append("Use an exact supplied chunk ID; do not write page labels in text")
                    continue
                cited = [allowed[c] for c in dict.fromkeys(segment.citations)]
                if numerical and not source_contains_quantity(draft.quantity, cited):
                    rejection("unsupported_quantity", attempt)
                    failures.append("The result and unit are absent from the cited chunk. Cite the actual "
                                    "worked example or refuse if it is absent.")
                    continue
                # Include the typed result BEFORE checking support, never after verification.
                if numerical:
                    segment.text += f" Result: {draft.quantity.value:.15g} {draft.quantity.unit}."
                # Blind reading anchors relevance before this model sees the generator's draft.
                solved = models.structured("verifier", Solve,
                    "Answer this question using ONLY the evidence. No proposed answer is supplied. "
                    "Give the directly requested meaning, purpose or result, not a related fact. "
                    "For hint mode give a helpful hint. Set supported=false if evidence cannot answer it. "
                    "Set unambiguous=false if the evidence does not resolve the question.",
                    {"stem": request.message, "type": "short", "options": [],
                     "evidence": evidence_payload(cited), "mode": request.mode})
                if not solved.supported or not solved.unambiguous:
                    rejection("unsupported_answer", attempt)
                    failures.append("Independent source reading could not answer the requested question")
                    continue
                verdict = models.structured("verifier", Verdict,
                    "Check this answer using ONLY the cited evidence. supported=true requires EVERY claim "
                    "to follow from that evidence and the answer to respond to the question. Reject "
                    "contradictions, unsupported derivations, invented facts, and irrelevant answers. "
                    "Simple arithmetic from explicit source values is allowed. If the question asks for a "
                    "numerical value and unit, a formula alone is incomplete. For hint mode, a source-backed "
                    "hint is sufficient. The proposed answer must answer the SAME requested information "
                    "as the independent blind answer. A related fact or initialization in place of a meaning "
                    "or purpose is insufficient. Give a short reason in one sentence.",
                    {"evidence": evidence_payload(cited), "question": request.message,
                     "answer": segment.text, "blind_answer": solved.answer, "mode": request.mode})
                if not verdict.supported:
                    rejection("unsupported_answer", attempt)
                    failures.append(verdict.reason)
            if not failures:
                checked = [{"text": s.text, "citations": [citation(allowed[c])
                           for c in dict.fromkeys(s.citations)]} for s in draft.segments]
                text = "\n\n".join(s["text"] + " " + " ".join(
                    f"{c['document_title']} {c['label']}" for c in s["citations"]) for s in checked)
                result = {"declined": False, "segments": checked, "answer": text, "attempts": attempt,
                          "verification": "Independent local support check",
                          "generator": models.roles["generator"], "verifier": models.roles["verifier"]}
                with db.transaction() as session:
                    db.add(session, "chat", request.subject_id,
                           {"question": request.message, "result": result})
                return result
        except StructuredOutputError:
            rejection("invalid_schema", attempt)
            failures = ["Invalid structured draft or verification output"]
        context["previous_failures"] = failures
    return refuse(3, ["No complete, independently supported draft passed after three attempts"])
