"""Evaluate live local inference against ten authored gold cases; never use fixtures."""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from scripts.create_sample import create_sample
from study.config import Settings
from study.main import create_app
from study.models import Models
from study.tutor import REFUSAL


def fraction(numerator, denominator):
    return round(numerator / denominator, 4) if denominator else None


def evaluate(output, pdf, questions, quiz_count=2):
    cases = json.loads(questions.read_text())
    if len(cases) != 10:
        raise ValueError("Evaluation expects exactly ten gold-labelled cases")
    if not pdf.exists():
        if pdf != Path("eval/sample.pdf"):
            raise FileNotFoundError(pdf)
        create_sample(pdf)
    started = time.monotonic()
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    rows = []
    with tempfile.TemporaryDirectory(prefix="citetutor-eval-") as tmp:
        settings = Settings(data_dir=Path(tmp))
        models = Models(settings)
        try:
            status = models.health()
            if not status["ready"]:
                raise RuntimeError("Local models not ready: " + json.dumps(status))
            with TestClient(create_app(settings, models)) as client:
                subject = client.post("/api/subjects", json={"title": "Evaluation / Mechanics"}).json()["id"]
                with pdf.open("rb") as file:
                    upload = client.post("/api/documents", data={"subject_id": subject},
                                         files={"file": (pdf.name, file, "application/pdf")})
                upload.raise_for_status()
                document = upload.json()
                print(f"Indexed {document['page_count']} pages with real {models.roles['embedding']} embeddings.",
                      flush=True)
                for index, case in enumerate(cases):
                    start = time.monotonic()
                    response = client.post("/api/chat", json={"subject_id": subject, "message": case["question"]})
                    response.raise_for_status()
                    result = response.json()
                    # Gold regex matching is a transparent heuristic, not an independent semantic judge.
                    text = " ".join(segment["text"] for segment in result["segments"])
                    citations = [c for s in result["segments"] for c in s["citations"]]
                    correct = not result["declined"] and all(re.search(pattern, text, re.I)
                                                              for pattern in case["answer_patterns"])
                    if not case["in_scope"]:
                        correct = result["declined"] and result["answer"] == REFUSAL
                    valid = sum(c["document_id"] == document["id"] and c["page"] in case["expected_pages"]
                                and client.get(c["url"]).is_success for c in citations)
                    row = {**case, "correct_by_gold_patterns": correct, "result": result,
                           "citation_count": len(citations), "gold_page_citations": valid,
                           "seconds": round(time.monotonic() - start, 3)}
                    rows.append(row)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.with_suffix(".partial.json").write_text(json.dumps(rows, indent=2))
                    print(f"{index + 1}/10 {case['id']}: {'PASS' if correct else 'REVIEW'} "
                          f"· {'refused' if result['declined'] else 'answered'} · {row['seconds']}s", flush=True)
                quiz_response = client.post("/api/quizzes", json={"subject_id": subject,
                    "document_id": document["id"], "page_start": 1, "page_end": min(20, document["page_count"]),
                    "count": quiz_count, "types": ["mcq", "short"]})
                quiz_response.raise_for_status()
                quiz = quiz_response.json()
        finally:
            models.close()
    in_scope = [r for r in rows if r["in_scope"]]
    out_of_scope = [r for r in rows if not r["in_scope"]]
    answered = [r for r in in_scope if not r["result"]["declined"]]
    all_citations = sum(r["citation_count"] for r in rows)
    metrics = {
        "in_scope_answer_correctness": fraction(sum(r["correct_by_gold_patterns"] for r in answered), len(answered)),
        "in_scope_success_rate": fraction(sum(r["correct_by_gold_patterns"] for r in in_scope), len(in_scope)),
        "citation_accuracy_against_gold_pages": fraction(sum(r["gold_page_citations"] for r in rows), all_citations),
        "citation_coverage_for_answers": fraction(sum(r["citation_count"] > 0 for r in answered), len(answered)),
        "out_of_scope_refusal_rate": fraction(sum(r["result"]["declined"] for r in out_of_scope), len(out_of_scope)),
        "in_scope_refusal_rate": fraction(sum(r["result"]["declined"] for r in in_scope), len(in_scope)),
        "questions": len(rows), "in_scope": len(in_scope), "out_of_scope": len(out_of_scope),
        "quiz_accepted": quiz["accepted"], "quiz_rejected": quiz["rejected"],
    }
    report = {"generated_at": datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
              "git_revision": revision, "dirty_worktree": dirty,
              "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
              "questions_sha256": hashlib.sha256(questions.read_bytes()).hexdigest(),
              "models": status, "seconds": round(time.monotonic() - started, 3),
              "method": "Gold regex correctness and document/page citation checks; manually review all rows. "
                        "Gold-labelled in-scope and out-of-scope cases. No fake models or cloud calls.",
              "metrics": metrics, "questions": rows, "quiz": quiz, "model_calls": models.calls}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    output.with_suffix(".partial.json").unlink(missing_ok=True)
    print(json.dumps(metrics, indent=2), flush=True)
    print(f"Full answers, citations, verifier rejections and timings: {output}", flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("eval/reports/local.json"))
    parser.add_argument("--pdf", type=Path, default=Path("eval/sample.pdf"))
    parser.add_argument("--questions", type=Path, default=Path("eval/questions.json"))
    parser.add_argument("--quiz-count", type=int, default=2, choices=range(1, 9))
    args = parser.parse_args()
    evaluate(args.output, args.pdf, args.questions, args.quiz_count)
