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

The scan-review endpoint also emits `CiteTutor ocr` with an `Ollama page transcription` span and reported token/timing metadata. Its image, base64 payload and draft text are excluded. OCR privacy is covered by SDK-envelope tests; the live trace evidence below predates scan support and tutor blind reading.

For the submission, follow [the recording/evidence guide](DEMO.md). `scripts.trace_demo --case tutor`, `--case quiz`, or `--case ocr --ocr-image /path/to/public-image.jpg` isolates each stage; add `--preview` to save metadata locally without network telemetry. The OCR rehearsal never indexes or approves the image, and prints no recognized text.

The integration uses [Sentry's manual tracing API](https://getsentry.github.io/sentry-python/api.html)
and [AI attribute conventions](https://getsentry.github.io/sentry-conventions/attributes/gen_ai/).
Token attributes are recorded only when Ollama supplies counts; embedding output tokens are not invented.
No paid inference API is used; hardware/electricity costs are not measured and Sentry's inferred model costs
should not be presented as a measured laptop cost.

## Live verification on October 4

The project DSN was configured in the ignored local `.env`; no DSN is committed. A content-free
delivery check returned HTTP 200 and appeared in Traces. A fresh, verified sample answer also
returned HTTP 200 from the tutor and Sentry transport, then appeared in **Agents → Traces** as
`66ca5eb26d1a46708f0497e55d9757ff`. The inspected timeline showed all five spans and Gemma's input
panel said **No input for this span**.

The run took 251.61 seconds: Gemma 227.15 seconds with 1,049 input/77 output tokens, Qwen 23.74
seconds with 469/27, and embeddings 0.46 seconds with 13 input tokens. A first live attempt
returned a local-model 503 after about four minutes. The focused successful retry used a 600-second
timeout and 256-token generation cap in a temporary library; production defaults remain unchanged.
This highlights slow local generation, not a measured tracing improvement.

The sanitized payload and HTTP delivery record are in
[eval/traces/live-delivery.json](../eval/traces/live-delivery.json). A real Agents timeline screenshot
was captured during setup; save/include that screen in the DEV post. The trace link requires your
Sentry account, so a screenshot is useful for judges who cannot access your project.

A newer scan-role trace was verified in both Traces and Agents: `9dd839e0c7304be8b77640221506af80`, using the credited public glassboard photo locally. GLM-OCR took 59.07 seconds with 4,072 input and 87 output tokens; root duration was 59.09 seconds. The inspected Agent Activity input panel says **No input for this span**. A clean-window dashboard screenshot was captured in chat; no PNG file is committed yet. See [the verified OCR metadata](../eval/traces/ocr-live.json) and the separate [local SDK preview](../eval/traces/ocr-preview.json).

The revised tutor was subsequently inspected live too: trace `08998f10d6f341e9a9a95454c5de60ba` shows retrieval, embeddings, Gemma NumericalDraft, Qwen blind Solve and support checking, with a 45.73-second root and first-attempt answer. Trace `e67e9be1c0db41d2b5fba5d2f9e24ae6` shows three rejected drafts before refusal, with the first code `unsupported_quantity`; source guards blocked it before Qwen. Actual clean-window screenshots of both were captured in chat. Timings, counts and account-gated links are preserved in [current-tutor-live.json](../eval/traces/current-tutor-live.json). These traces use the authored mechanics fixture, not private college notes.

The onboarding page's **Waiting for error** is independent of AI trace ingestion. This integration
intentionally drops error-event bodies and verifies tracing through Agents rather than injecting
a division-by-zero exception. Failed spans now carry an `internal_error` status and fixed outcome
metadata without transmitting exception text or stack locals.

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
