from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class Transcription(Schema):
    text: str = Field(max_length=12000)


class ReviewedPage(Schema):
    page: int = Field(ge=1, le=300)
    text: str = Field(max_length=12000)


class ReviewRequest(Schema):
    version: int = Field(ge=1)
    pages: list[ReviewedPage] = Field(min_length=1, max_length=20)


class Segment(Schema):
    text: str = Field(min_length=1, max_length=2500)
    citations: list[str] = Field(min_length=1, max_length=1)


class Draft(Schema):
    answerable: bool
    segments: list[Segment] = Field(default_factory=list, max_length=1)


class Quantity(Schema):
    value: float
    unit: str = Field(min_length=1, max_length=30)


class NumericalDraft(Draft):
    quantity: Quantity | None


class Verdict(Schema):
    supported: bool
    reason: str = Field(min_length=1, max_length=600)


class ChatRequest(Schema):
    subject_id: str
    message: str = Field(min_length=1, max_length=2000)
    mode: Literal["ask", "explain", "hint"] = "ask"
    style: Literal["simple", "concise", "detailed"] = "simple"
    document_ids: list[str] = Field(default_factory=list, max_length=30)


class Option(Schema):
    id: str = Field(pattern="^[A-D]$")
    text: str = Field(min_length=1, max_length=500)


class Quote(Schema):
    source_unit_id: str
    quote: str = Field(min_length=12, max_length=500)


class Question(Schema):
    type: Literal["mcq", "short"]
    stem: str = Field(min_length=1, max_length=1000)
    options: list[Option] = Field(default_factory=list, max_length=4)
    answer: str = Field(min_length=1, max_length=1000)
    rationale: str = Field(min_length=1, max_length=1000)
    source_unit_ids: list[str] = Field(min_length=1, max_length=3)
    supporting_quotes: list[Quote] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def valid_key(self):
        if self.type == "mcq":
            ids = [o.id for o in self.options]
            if len(ids) != 4 or len(set(ids)) != 4 or self.answer not in ids:
                raise ValueError("MCQ requires four distinct options and one valid answer ID")
            if len({o.text.casefold() for o in self.options}) != len(ids):
                raise ValueError("Duplicate option text")
        elif self.options:
            raise ValueError("Short answers must have no options")
        if set(self.source_unit_ids) != {q.source_unit_id for q in self.supporting_quotes}:
            raise ValueError("Every cited source must have a supporting quote")
        return self


class Solve(Schema):
    answer: str = Field(max_length=1000)
    unambiguous: bool
    supported: bool
    reason: str = Field(min_length=1, max_length=600)


class MCQQuestion(Question):
    type: Literal["mcq"]
    options: list[Option] = Field(min_length=4, max_length=4)
    answer: Literal["A", "B", "C", "D"]


class ShortQuestion(Question):
    type: Literal["short"]
    options: list[Option] = Field(default_factory=list, max_length=0)


class QuizRequest(Schema):
    subject_id: str
    document_id: str
    page_start: int = Field(default=1, ge=1)
    page_end: int = Field(ge=1)
    count: int = Field(default=5, ge=1, le=8)
    types: list[Literal["mcq", "short"]] = Field(default=["mcq", "short"], min_length=1, max_length=2)

    @model_validator(mode="after")
    def valid_range(self):
        if self.page_end < self.page_start or self.page_end - self.page_start >= 20:
            raise ValueError("Choose an inclusive range of at most 20 pages")
        return self
