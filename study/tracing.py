"""Opt-in Sentry AI traces. Only fixed labels and numerical metadata may leave the laptop."""

import math
import re
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import wraps

import sentry_sdk
from sentry_sdk.envelope import Envelope
from sentry_sdk.transport import HttpTransport, Transport

_active = ContextVar("citetutor_trace_active", default=False)
NAMES = {
    "CiteTutor tutor", "CiteTutor quiz", "Ollama structured output", "Ollama embeddings",
    "Hybrid retrieval", "Blind solve and support check", "Draft rejected",
    "Quiz candidate rejected",
}
OPS = {"gen_ai.invoke_agent", "gen_ai.chat", "gen_ai.embeddings", "gen_ai.execute_tool"}
LABELS = {
    "gen_ai.system": {"ollama"},
    "gen_ai.provider.name": {"ollama"},
    "gen_ai.operation.name": {"invoke_agent", "chat", "embeddings", "execute_tool"},
    "gen_ai.agent.name": {"CiteTutor"},
    "gen_ai.tool.name": {"Hybrid retrieval", "Blind solve and support check",
                         "Draft rejected", "Quiz candidate rejected"},
    "gen_ai.request.model": {"gemma3:4b", "gemma3:1b", "qwen2.5:3b", "qwen2.5:1.5b",
                             "nomic-embed-text", "local-custom-model"},
    "citetutor.role": {"generator", "verifier", "embedding"},
    "citetutor.schema": {"Draft", "NumericalDraft", "Verdict", "MCQQuestion", "ShortQuestion", "Solve"},
    "citetutor.outcome": {"answered", "refused", "completed", "error"},
    "citetutor.rejection": {"generator_declined", "missing_quantity", "invalid_citation",
                           "unsupported_quantity", "unsupported_answer", "invalid_schema",
                           "unknown_source", "fabricated_quote", "missing_retrieved_source",
                           "ambiguous_or_unsupported", "key_disagreement", "unsupported_key",
                           "wrong_type", "duplicate", "other"},
}
COUNTS = {
    "gen_ai.usage.input_tokens", "gen_ai.usage.output_tokens", "citetutor.attempt",
    "citetutor.attempts", "citetutor.accepted", "citetutor.rejected", "citetutor.requested",
    "citetutor.input_count", "citetutor.retrieved_count",
}


def safe_data(data):
    result = {}
    for key, value in (data or {}).items():
        if key in LABELS and isinstance(value, str) and value in LABELS[key]:
            result[key] = value
        elif key in COUNTS and type(value) is int and 0 <= value <= 1_000_000_000:
            result[key] = value
    return result


def safe_span(span):
    """Rebuild, rather than redact: unknown fields and free text cannot cross this boundary."""
    if span.get("op") not in OPS or span.get("description") not in NAMES:
        return None
    result = {"op": span["op"], "description": span["description"], "data": safe_data(span.get("data"))}
    for key in ("trace_id", "span_id", "parent_span_id"):
        value = span.get(key, "")
        if isinstance(value, str) and re.fullmatch(r"[0-9a-f]{16}|[0-9a-f]{32}", value):
            result[key] = value
    for key in ("start_timestamp", "timestamp"):
        value = span.get(key)
        if type(value) in (int, float) and math.isfinite(value):
            result[key] = value
        elif isinstance(value, str) and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", value):
            result[key] = value
    if span.get("status") in {"ok", "internal_error", "unknown_error"}:
        result["status"] = span["status"]
    return result


def safe_transaction(event, hint):
    if event.get("transaction") not in {"CiteTutor tutor", "CiteTutor quiz"}:
        return None
    trace = event.get("contexts", {}).get("trace", {})
    cleaned = safe_span({**trace, "description": event["transaction"],
                         "start_timestamp": event.get("start_timestamp"), "timestamp": event.get("timestamp")})
    if cleaned is None:
        return None
    result = {
        "type": "transaction", "transaction": event["transaction"],
        "transaction_info": {"source": "custom"}, "platform": "python",
        "start_timestamp": cleaned.pop("start_timestamp", None),
        "timestamp": cleaned.pop("timestamp", None),
        "contexts": {"trace": cleaned},
        "spans": [s for span in event.get("spans", []) if (s := safe_span(span)) is not None],
    }
    event_id = event.get("event_id", "")
    if isinstance(event_id, str) and re.fullmatch(r"[0-9a-f]{32}", event_id):
        result["event_id"] = event_id
    return result


class NullSpan:
    def set_data(self, key, value):
        pass

    def set_status(self, status):
        pass


class MetadataTransport(Transport):
    """Last outbound boundary: no attachments, errors, or inherited envelope headers."""
    def __init__(self, options, delegate=None):
        super().__init__(options)
        self.delegate = delegate or HttpTransport(options)

    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") != "transaction":
                continue
            event = safe_transaction(item.payload.json or {}, {})
            if event is not None:
                clean = Envelope(headers={"event_id": event.get("event_id")})
                clean.add_transaction(event)
                try:
                    self.delegate.capture_envelope(clean)
                except Exception:
                    pass

    def flush(self, timeout, callback=None):
        self.delegate.flush(timeout, callback)

    def kill(self):
        self.delegate.kill()


class Tracing:
    def __init__(self, settings, *, transport=None):
        self.client = None
        self.status = "disabled"
        self.last_trace_id = None
        dsn = settings.sentry_dsn.get_secret_value().strip()
        if not dsn:
            return  # Do not initialize the SDK or inherit a generic SENTRY_DSN.
        try:
            class GuardedTransport(MetadataTransport):
                def __init__(self, options):
                    super().__init__(options, transport)

            self.client = sentry_sdk.Client(
                dsn=dsn, transport=GuardedTransport, default_integrations=False, auto_enabling_integrations=False,
                traces_sample_rate=settings.sentry_traces_sample_rate, stream_gen_ai_spans=False,
                send_default_pii=False, max_breadcrumbs=0, max_request_body_size="never",
                include_local_variables=False, include_source_context=False, auto_session_tracking=False,
                send_client_reports=False, enable_logs=False, enable_metrics=False,
                enable_backpressure_handling=False, profiles_sample_rate=0,
                profile_session_sample_rate=0, propagate_traces=False,
                debug=False, spotlight=False,
                before_send=lambda event, hint: None, before_send_transaction=safe_transaction,
                server_name="citetutor-local", release="citetutor@0.2.0", environment="local",
            )
            self.status = "enabled"
        except Exception:
            # No DSN, exception text, or configuration contents in logs/HTTP responses.
            self.status = "unavailable"

    @contextmanager
    def request(self, kind):
        self.last_trace_id = None
        stack = ExitStack()
        span = NullSpan()
        if self.client is not None:
            try:
                scope = stack.enter_context(sentry_sdk.isolation_scope())
                scope.set_client(self.client)
                sentry_sdk.get_current_scope().set_client(self.client)
                span = stack.enter_context(sentry_sdk.start_transaction(
                    name=f"CiteTutor {kind}", op="gen_ai.invoke_agent"))
                span.set_data("gen_ai.agent.name", "CiteTutor")
                span.set_data("gen_ai.operation.name", "invoke_agent")
            except Exception:
                span = NullSpan()
        token = _active.set(self.client is not None and not isinstance(span, NullSpan))
        try:
            yield span
        except Exception:
            span.set_data("citetutor.outcome", "error")
            span.set_status("internal_error")
            raise
        finally:
            if not isinstance(span, NullSpan) and getattr(span, "sampled", False):
                self.last_trace_id = span.trace_id
            _active.reset(token)
            try:
                stack.close()
            except Exception:
                pass  # Offline/failed telemetry must never alter a study result.

    def close(self):
        if self.client is not None:
            try:
                self.client.close(timeout=2)
            except Exception:
                pass


@contextmanager
def stage(op, name):
    stack = ExitStack()
    span = NullSpan()
    if _active.get():
        try:
            span = stack.enter_context(sentry_sdk.start_span(op=op, name=name))
            span.set_data("gen_ai.operation.name", op.split(".")[-1])
            if op == "gen_ai.execute_tool":
                span.set_data("gen_ai.tool.name", name)
        except Exception:
            span = NullSpan()
    try:
        yield span
    except Exception:
        span.set_data("citetutor.outcome", "error")
        span.set_status("internal_error")
        raise
    finally:
        try:
            stack.close()
        except Exception:
            pass


def traced(op, name):
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            with stage(op, name):
                return function(*args, **kwargs)
        return wrapped
    return decorate


def record(**data):
    if _active.get():
        span = sentry_sdk.get_current_span()
        if span is not None:
            for key, value in safe_data(data).items():
                span.set_data(key, value)


def model_metadata(role, tag, schema=None):
    record(**{"citetutor.role": role,
              "gen_ai.request.model": tag if tag in LABELS["gen_ai.request.model"] else "local-custom-model",
              "gen_ai.system": "ollama", "gen_ai.provider.name": "ollama",
              "citetutor.schema": schema})


def rejection(code, attempt):
    with stage("gen_ai.execute_tool", "Draft rejected") as span:
        for key, value in safe_data({"citetutor.rejection": code, "citetutor.attempt": attempt}).items():
            span.set_data(key, value)


REJECTIONS = {
    "Unknown source ID": "unknown_source",
    "Supporting quote is not present in the source": "fabricated_quote",
    "Independent retrieval did not recover supporting sources": "missing_retrieved_source",
    "Blind solver found insufficient evidence or ambiguity": "ambiguous_or_unsupported",
    "Blind solver disagreed with the answer key": "key_disagreement",
    "Key, rationale, or short-answer agreement failed the support check": "unsupported_key",
    "Wrong question type": "wrong_type", "Duplicate question": "duplicate",
    "Invalid question or verifier schema": "invalid_schema",
}


def quiz_rejections(result):
    for item in result["rejections"]:
        with stage("gen_ai.execute_tool", "Quiz candidate rejected") as span:
            span.set_data("citetutor.rejection", REJECTIONS.get(item["reason"], "other"))
            span.set_data("citetutor.attempt", item["candidate"])
