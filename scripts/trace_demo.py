"""Exercise real local models on the original sample PDF, never the user's library."""

import argparse
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from sentry_sdk.transport import Transport

from study.config import Settings
from study.main import create_app
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
    args = parser.parse_args()
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
            for label, question in questions:
                print(f"Running {label} request with real local models…", flush=True)
                response = client.post("/api/chat", json={"subject_id": subject, "message": question})
                response.raise_for_status()
                result = response.json()
                print(json.dumps({"case": label, "declined": result["declined"], "attempts": result["attempts"],
                                  "trace_id": tracing.last_trace_id}), flush=True)
            print("Generating and verifying two quiz candidates…", flush=True)
            response = client.post("/api/quizzes", json={"subject_id": subject, "document_id": document["id"],
                "page_start": 1, "page_end": document["page_count"], "count": 2, "types": ["mcq", "short"]})
            response.raise_for_status()
            result = response.json()
            print(json.dumps({"quiz_accepted": result["accepted"], "quiz_rejected": result["rejected"],
                              "trace_id": tracing.last_trace_id}), flush=True)
        if transport is not None:
            output = Path("data/trace-preview.json")
            output.parent.mkdir(exist_ok=True)
            output.write_text(json.dumps({"mode": "local preview; not delivered to Sentry",
                                          "events": transport.events}, indent=2) + "\n")
            print(f"Local metadata capture: {output}; no events sent to Sentry.")
        else:
            print("Trace IDs generated. Confirm ingestion in Sentry Traces/AI before claiming live verification.")


if __name__ == "__main__":
    main()
