"""Exercise real local models on demo material, never the user's study library."""

import argparse
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from study.config import Settings
from study.main import create_app
from study.models import Models
from study.tracing import Tracing


class PreviewTransport(Transport):
    """Explicit local preview: real SDK envelopes, no Sentry network transport."""
    def __init__(self):
        super().__init__()
        self.events = []

    def capture_envelope(self, envelope):
        self.events.extend(item.payload.json for item in envelope.items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="Save metadata locally without sending to Sentry")
    parser.add_argument("--case", choices=["all", "tutor", "quiz", "ocr"], default="all",
                        help="Rehearse one stage, or tutor/refusal/quiz together")
    parser.add_argument("--ocr-image", type=Path, help="Local public/demo image; required for --case ocr")
    args = parser.parse_args()
    if args.case == "ocr" and (args.ocr_image is None or not args.ocr_image.is_file()):
        parser.error("--case ocr requires --ocr-image pointing to a local image")
    transport = PreviewTransport() if args.preview else None
    with tempfile.TemporaryDirectory(prefix="citetutor-trace-") as tmp:
        settings = Settings(data_dir=Path(tmp))
        if args.preview:
            settings.sentry_dsn = Settings(_env_file=None, sentry_dsn="https://preview@example.invalid/1").sentry_dsn
            settings.sentry_traces_sample_rate = 1
        if not settings.sentry_dsn.get_secret_value().strip():
            raise SystemExit("Set CITETUTOR_SENTRY_DSN in .env first, or use --preview for a local-only capture.")
        tracing = Tracing(settings, transport=transport)
        if tracing.status != "enabled":
            raise SystemExit("Tracing configuration unavailable; check the project DSN locally.")
        if args.case == "ocr":
            models = Models(settings)
            try:
                print("Reading a local demo image; only token/timing metadata may leave the laptop…", flush=True)
                with tracing.request("ocr") as span:
                    draft = models.transcribe(args.ocr_image.read_bytes())
                    span.set_data("citetutor.outcome", "completed")
                print(json.dumps({"case": "ocr", "model": settings.ocr_model,
                                  "draft_characters": len(draft.text), "incomplete": draft.incomplete,
                                  "indexed": False, "trace_id": tracing.last_trace_id}), flush=True)
            finally:
                models.close()
                tracing.close()
            save_preview(transport, args.case)
            return
        app = create_app(settings, tracing_client=tracing)
        with TestClient(app) as client:
            if not client.get("/api/health").json()["models"]["ready"]:
                raise SystemExit("Pull the three local model tags listed in README.md first.")
            subject = client.post("/api/subjects", json={"title": "Trace demo / Mechanics"}).json()["id"]
            with Path("eval/sample.pdf").open("rb") as pdf:
                upload = client.post("/api/documents", data={"subject_id": subject},
                                     files={"file": ("sample.pdf", pdf, "application/pdf")})
            upload.raise_for_status()
            document = upload.json()
            questions = [
                ("supported", "In the worked example, a 2 kg body accelerates at 4 m/s². "
                              "What is its net force? Give the value and unit."),
                ("outside worked evidence", "A 7 kg body accelerates at 3 m/s². What is its net force? "
                                           "Give the value and unit from a worked example in this document."),
            ]
            for label, question in questions if args.case in {"all", "tutor"} else []:
                print(f"Running {label} request with real local models…", flush=True)
                response = client.post("/api/chat", json={"subject_id": subject, "message": question})
                response.raise_for_status()
                result = response.json()
                print(json.dumps({"case": label, "declined": result["declined"], "attempts": result["attempts"],
                                  "trace_id": tracing.last_trace_id}), flush=True)
            if args.case in {"all", "quiz"}:
                print("Generating and verifying two quiz candidates…", flush=True)
                response = client.post("/api/quizzes", json={"subject_id": subject, "document_id": document["id"],
                    "page_start": 1, "page_end": document["page_count"], "count": 2, "types": ["mcq", "short"]})
                response.raise_for_status()
                result = response.json()
                print(json.dumps({"quiz_accepted": result["accepted"], "quiz_rejected": result["rejected"],
                                  "trace_id": tracing.last_trace_id}), flush=True)
        save_preview(transport, args.case)


def save_preview(transport, case):
    if transport is not None:
        output = Path("data/trace-preview.json" if case == "all" else f"data/trace-preview-{case}.json")
        output.parent.mkdir(exist_ok=True)
        output.write_text(json.dumps({"mode": "local preview; not delivered to Sentry",
                                      "events": transport.events}, indent=2) + "\n")
        print(f"Local metadata capture: {output}; no events sent to Sentry.")
    else:
        print("Trace IDs generated. Confirm ingestion in Sentry Traces/AI before claiming live verification.")


if __name__ == "__main__":
    main()
