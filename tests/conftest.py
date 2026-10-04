import pymupdf
import pytest
from fastapi.testclient import TestClient

from study.config import Settings
from study.main import create_app
from study.models import StructuredOutputError
from study.schemas import Draft, NumericalDraft, Question, Solve, Verdict


def pdf_bytes(*texts):
    with pymupdf.open() as doc:
        for text in texts:
            page = doc.new_page()
            page.insert_textbox((50, 50, 550, 750), text, fontsize=12)
        return doc.tobytes()


class FakeModels:
    """Deterministic boundary fixture. Never used for production or quality evaluation."""
    roles = {"generator": "gemma3:1b", "verifier": "qwen2.5:3b", "embedding": "nomic-embed-text"}

    def __init__(self, settings):
        self.settings = settings
        self.calls = []
        self.reject = False
        self.bad_citation = False
        self.bad_quote = False
        self.invalid_draft = False
        self.disagree = False
        self.embed_error = False
        self.counter = 0
        self.bad_quiz_source = False
        self.roles = dict(self.roles)

    def health(self):
        return {"ready": True, "roles": {r: {"ready": True, "model": m} for r, m in self.roles.items()}}

    def embed(self, texts, *, query=False):
        if self.embed_error:
            raise RuntimeError("Fixture embedding outage")
        return [[1.0, 0.5] for _ in texts]

    def structured(self, role, schema, instruction, context):
        self.calls.append((role, schema, context))
        if issubclass(schema, Draft):
            if "pizza" in context["query"].lower():
                return Draft(answerable=False)
            if self.invalid_draft:
                raise StructuredOutputError("Fixture invalid schema")
            segments = [{"text": "Force equals mass times acceleration.",
                         "citations": ["unknown" if self.bad_citation else context["evidence"][0]["id"]]}]
            return schema(answerable=True, segments=segments,
                          **({"quantity": None} if schema is NumericalDraft else {}))
        if schema is Verdict:
            return Verdict(supported=not self.reject, reason="Fixture verdict")
        if schema is Solve:
            assert not {"answer", "rationale", "supporting_quotes", "source_unit_ids"} & context.keys()
            return Solve(answer="B" if self.disagree else "A" if context["type"] == "mcq"
                         else "Force equals mass times acceleration.",
                         supported=True, unambiguous=True, reason="Fixture solution")
        if issubclass(schema, Question):
            self.counter += 1
            evidence = dict(context["evidence"][0])
            if self.bad_quiz_source:
                evidence["id"] = "unknown"
            quote = "This invented quote is absent" if self.bad_quote else evidence["text"][:200]
            kind = context["type"]
            return schema(type=kind, stem=f"What defines force? Version {self.counter}",
                            options=[{"id": "A", "text": "Mass times acceleration"},
                                     {"id": "B", "text": "Mass over acceleration"},
                                     {"id": "C", "text": "Speed only"},
                                     {"id": "D", "text": "Distance only"}] if kind == "mcq" else [],
                            answer="A" if kind == "mcq" else "Force equals mass times acceleration.",
                            rationale="The document states the relationship.",
                            source_unit_ids=[evidence["id"]],
                            supporting_quotes=[{"source_unit_id": evidence["id"], "quote": quote}])
        raise AssertionError(schema)


@pytest.fixture
def context(tmp_path):
    settings = Settings(_env_file=None, data_dir=tmp_path)
    models = FakeModels(settings)
    app = create_app(settings, models)
    with TestClient(app) as client:
        subject = client.post("/api/subjects", json={"title": "Physics"}).json()["id"]
        document = client.post("/api/documents", data={"subject_id": subject},
                               files={"file": ("notes.pdf", pdf_bytes(
                                   "Force equals mass times acceleration.",
                                   "Kinetic energy is half mass times speed squared."), "application/pdf")}).json()
        yield client, models, subject, document, app
