# Optional Sentry Agent Tracing

All embeddings, generation and verification remain in local Ollama. Sentry is optional telemetry;
when enabled, timing/token/count metadata travels to your Sentry project over the internet.
Leave `CITETUTOR_SENTRY_DSN` blank to keep tracing off. A failed telemetry transport does not prevent study requests.

## Create and connect a project

1. Sign in at [Sentry](https://sentry.io/) and create a project under your organisation.
2. Choose **Python / FastAPI**, name it `citetutor`, and create it. We already install and configure the SDK;
   use the DSN from the setup screen rather than adding the default generated integration snippet.
3. You can also find the DSN under **Settings → Projects → citetutor → Client Keys (DSN)**.
4. Copy `.env.example` to `.env` if you have no `.env` yet. Set these values locally:

```dotenv
CITETUTOR_SENTRY_DSN=https://YOUR_PUBLIC_KEY@YOUR_INGEST_HOST/YOUR_PROJECT_ID
CITETUTOR_SENTRY_TRACES_SAMPLE_RATE=1.0
```

Do not commit `.env`. No Sentry API token is needed to send traces.
Restart the running app with `./run.sh`. `/api/health` should report `tracing.status: enabled`.
That means the client is configured, **not** that Sentry ingestion has been confirmed.

## Capture a real demonstration

```sh
uv run --offline python -m scripts.trace_demo
```

This runs real local Gemma, Qwen and embedding calls using the original `eval/sample.pdf` in a temporary library.
It leaves your uploaded notes untouched. It prints trace IDs for a supported answer, a question outside the
document's worked results, and a mixed two-question quiz. Allow several minutes on an 8 GB laptop.
The models may refuse immediately or reject drafts; record what actually happens rather than promising a rejection.

In Sentry, open **Traces** or **AI**, select this project and the recent time range, and find `CiteTutor tutor`
and `CiteTutor quiz` (or search a printed trace ID). Capture the span waterfall and its metadata for the DEV post:

- `Hybrid retrieval`, local `Ollama embeddings`, and `Ollama structured output` spans;
- generator/verifier roles, schemas, elapsed time and Ollama-reported input/output token counts;
- tutor attempts/outcome and any `Draft rejected` spans with fixed rejection codes;
- `Blind solve and support check`, quiz accepted/rejected counts, and any candidate rejection codes.

The integration uses [Sentry's manual tracing API](https://getsentry.github.io/sentry-python/api.html)
and [AI attribute conventions](https://getsentry.github.io/sentry-conventions/attributes/gen_ai/).
Token attributes are recorded only when Ollama supplies counts; embedding output tokens are not invented.
No paid inference API is used; hardware/electricity costs are not measured and Sentry's inferred model costs
should not be presented as a measured laptop cost.

## Privacy and local validation

Automatic framework, HTTP, logging and error integrations are disabled. Error events, logs, profiles,
session reports, breadcrumbs, request bodies and stack locals are not captured. Before transmission,
each transaction is rebuilt from an allowlist: fixed stage names/model labels, numeric counts, timestamps
and random trace/span/event IDs. A final transport guard also removes attachments and inherited envelope
headers. Unknown attributes and spans are dropped. Custom model tags become
`local-custom-model`; subject/document identifiers and titles are omitted.

The SDK uses transaction envelopes with AI streaming disabled so every child span passes the same
outgoing allowlist. No model messages, notes, source quotes, questions, answers, filenames or verifier reasons
are sent. Network metadata, such as your connection's IP address, is still visible to Sentry's receiving server.

```sh
uv run --offline python -m pytest tests/test_tracing.py -q
uv run --offline python -m scripts.trace_demo --preview
```

`--preview` sends **nothing** to Sentry. It uses the real SDK and local models but captures sanitized envelopes
in ignored `data/trace-preview.json`. It validates instrumentation without a Sentry account; it does not
demonstrate live ingestion or establish a partner-category entry. Tests use in-memory transports and model
fixtures to verify privacy, token metadata, three rejected drafts, quiz disagreement, and offline transport failure.

An actual local-model preview is preserved in [eval/traces/local-preview.json](../eval/traces/local-preview.json).
It recorded a verified answer in 140.85 seconds, a refusal after three `unsupported_quantity` rejections
in 465.02 seconds, and two accepted quiz candidates in 298.92 seconds. These are SDK captures without
live Sentry delivery; they show significant laptop latency, not an improvement caused by tracing.
