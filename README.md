# CiteTutor

**Local college study help, grounded in your own material.** Create a subject, add several PDFs, ask for explanations or hints, and practise with independently checked questions. Built to help a friend in college study from their notes and textbook chapters.

Open-weight models make the app work: **Gemma** drafts explanations and questions, **Qwen** verifies them, and **nomic-embed-text** powers semantic retrieval. All inference runs on your laptop through Ollama. No cloud API fallback.

| Component | Actual role |
|---|---|
| `gemma3:4b` | Generate structured tutor answers, MCQs and short-answer questions |
| `qwen2.5:3b` | Blindly answer tutor/quiz questions and independently check source support |
| `nomic-embed-text` | Embed document chunks and study queries for local retrieval |
| `glm-ocr:q8_0` | Draft scan transcriptions for review, including handwritten notes |
| Ollama | Run all model roles locally |
| FastAPI, PyMuPDF, SQLite | Serve the UI, extract PDF text and store local study material |

**Technology category target: Best Use of Gemma.** Gemma powers both generation paths; its installed model tag appears in `/api/health` and the live evaluation report. The [current category rules](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) include running Gemma locally. Optional **Sentry Agent Tracing** is implemented for timing, tokens, retries and rejections; live delivery and the Gemma/Qwen spans have been confirmed in Sentry’s Agents view. This technology fit does not establish overall challenge eligibility or guarantee a prize. Entire and ElevenLabs are not integrated.

## Setup

Requirements: Python **3.11–3.13**, [uv](https://docs.astral.sh/uv/), and a current [Ollama](https://ollama.com/) (scan path tested with 0.35.1). Install dependencies and pull local weights once while online:

```sh
git clone https://github.com/arywk40-hue/hacktober.git
cd hacktober
uv sync --frozen --extra dev
ollama serve
```

Leave `ollama serve` running and, in another terminal, pull the laptop defaults:

```sh
ollama pull gemma3:4b
ollama pull qwen2.5:3b
ollama pull nomic-embed-text
# For handwritten/image-only pages:
ollama pull glm-ocr:q8_0
```

If the Ollama desktop app already runs its server, skip `ollama serve`. These defaults were checked on an 8 GB Apple M1. Calls run serially and unload weights to limit memory use. Allow time for generation and verification; the faster 1B generator struggled with quiz quality and is not the recommended default.

## Run with one command

```sh
./run.sh
```

Open **http://127.0.0.1:8000**. The launcher starts local Ollama if needed, verifies the installed weights and distinct model families, and starts the app on loopback. `uv run --offline` prevents dependency downloads at launch. Missing weights produce setup instructions; the app never pulls models automatically.

1. Create a subject, such as Engineering Physics or Design of Algorithms.
2. Add PDFs. Selectable text is indexed in-process. Handwritten/image-only pages stay pending until review: click **Review scans**, then **Read this page locally** for each page. Compare the draft with its image, correct mistakes, and check each page before **Approve all scans & index**. Remove unreadable lines or leave a page blank to exclude it. For a poor existing text layer, select **Read all pages as scans** at upload.
3. Open **Study together**. Choose all subject PDFs or one document, then ask a complete question. Explanation style changes wording only.
4. Click a citation such as **[p. 2] notes.pdf** to read the full extracted page text. Reviewed scans also show the original page image.
5. Open **Practice**. Pick a PDF, an inclusive physical page range, and MCQ/short-answer types. Only verified questions appear; accepted/rejected counts and rejection reasons are shown.
6. Answer MCQs for exact checking, or compare your short answer with the verified source answer and quote.

Try [eval/sample.pdf](eval/sample.pdf), an original three-page mechanics fixture. Ask “What is the net force on a 2 kg body accelerating at 4 m/s²?” and then an unrelated question to inspect the refusal path.

## How evidence is checked

PDF pages → overlapping chunks with document/page identity → local embeddings in SQLite → keyword + cosine retrieval with reciprocal-rank fusion.

**Tutor:** retrieve → structured segments with short chunk aliases → reject missing/unknown citations → another model independently answers the question from cited text without seeing the draft → check draft support and agreement with that blind reading. Concise answers currently use one paragraph and one supporting chunk to prevent unnecessary padding by the small generator. Aliases are resolved to authoritative stored chunks; models never choose page numbers. At most three complete drafts are attempted. Unverified drafts and partial passes are never streamed or displayed. If none passes:

> Not enough evidence in this document

**Quiz:** schema + source-ID validation → literal quote validation → independently retrieve evidence for the question → blind solve by a different model family, without the proposed key, rationale or quotes → check key agreement and source support. MCQ keys must match exactly; short answers need agreement in meaning. Rejected candidates are counted and omitted. Small rotating source windows keep page ranges within laptop context limits.

## Why open-source AI

- **Offline:** after dependency/model setup, retrieval, generation and verification need only SQLite and loopback Ollama requests. The UI has no CDN or remote fonts. Optional Sentry tracing is disabled by default; leave its DSN blank for fully offline operation.
- **Private:** PDFs, extracted text, embeddings, answers and verifier audits stay under local `data/`.
- **No paid inference API:** there are no tokens billed by a cloud provider. Hardware, storage and electricity still have costs.
- **Swappable:** generator, verifier and embedding tags are configurable. Ollama metadata must confirm distinct generator/verifier families and local weights. Changing the embedding model requires deleting and re-uploading documents to rebuild the embedding space.
- **Inspectible:** source IDs, page text, supporting quotes, rejection reasons and evaluation outputs are available to inspect. Open components are the retrieval and reasoning engines, not a decorative integration.

Gemma is open-weight. Model and dependency licenses apply; “open-weight” does not mean every model has an OSI-approved open-source license.

## Configuration

Defaults work without `.env`. To customise, copy `.env.example` to `.env` and edit `CITETUTOR_GENERATOR_MODEL`, `CITETUTOR_VERIFIER_MODEL`, or `CITETUTOR_EMBEDDING_MODEL`. Pull chosen tags explicitly first. `CITETUTOR_OLLAMA_URL` must be an HTTP loopback address; remote endpoints and cloud model tags are rejected.

`CITETUTOR_OCR_MODEL` defaults to `glm-ocr:q8_0`, independently of the tutor generator. Pull its weights before reading scans; ordinary text PDFs need only the three study models. OCR requires the model's local `vision` capability. `CITETUTOR_OCR_TIMEOUT` defaults to 600 seconds per page. Drafts are not evidence: the entire document stays out of retrieval until all scanned pages are reviewed. Approval builds its index atomically. **Review again** keeps the PDF/text and removes its derived index until reapproval. The factual verifier checks approved text, not the image; recognition mistakes can survive unless corrected during review.

Gemma 3 4B and Qwen 2.5 3B are the defaults after the smaller generator/verifier proved unreliable in our traces. Local model calls are serialised and weights unload after each call to limit RAM use. Requests can take time on laptops; the UI shows retrieval/verification progress. Only one study operation runs at a time; a concurrent operation gets a visible retry message.

## Optional Sentry Agent Tracing

Create a Python/FastAPI project in [Sentry](https://sentry.io/), copy its project DSN to `.env` as
`CITETUTOR_SENTRY_DSN`, and restart `./run.sh`. See the [step-by-step setup and demo](docs/SENTRY.md).
Tracing records retrieval, Ollama generation/verification calls, token counts reported by Ollama,
tutor attempts/refusals and quiz rejection counts/codes. These metadata leave the laptop when enabled.
Document text, filenames, source IDs, prompts, answers and verifier reasons are excluded by an outgoing
allowlist; automatic error/log/body capture is disabled. All model inference stays local. Failed telemetry
does not block study requests.

```sh
# Real models; save sanitized SDK envelopes locally, without a Sentry account or network telemetry:
uv run --offline python -m scripts.trace_demo --preview
# After configuring your Sentry DSN, generate traces and verify them in the Sentry UI:
uv run --offline python -m scripts.trace_demo
```

The demo uses only `eval/sample.pdf` in a temporary library. Live Sentry delivery has been confirmed for a verified sample answer; see
[the sanitized trace evidence](eval/traces/live-delivery.json). Save the actual trace screenshot
from the Agents view for the DEV post. Earlier local preview captures remain separate evidence.

## Tests and evaluation

```sh
uv run --offline python -m pytest -q
uv run --offline ruff check study tests scripts
node --check study/static/app.js
uv run --offline python -m scripts.evaluate
```

The **56 contract tests** cover chunk/page preservation, citation parsing, document scope, atomic indexing failures, bounded retries, guarded verification, blind solving, fabricated quotes, model-family enforcement, local-only configuration, scan review before retrieval, OCR capability/partial-draft checks and Sentry privacy/transport boundaries. Test doubles validate boundaries; they do not establish model accuracy.

The evaluation runs **10 questions against real local models**: seven supported mechanics questions and three out-of-scope questions. It also generates a two-question mixed quiz. It reports gold-pattern answer correctness, in-scope success/refusal rates, citation accuracy against expected document/pages, out-of-scope refusal rate, quiz rejection counts, latency and token counts. See [eval/README.md](eval/README.md). Gold regex checks are a transparent heuristic; inspect the complete responses and source pages.

The revised ten-question run correctly answered **7/7 supported questions**, with expected-page citations for all seven, and refused **3/3 out-of-scope questions**. The mixed quiz accepted one question and rejected one for blind-solver/key disagreement. The run took 479 seconds; returned-answer median was 44.5 seconds. See [measured results](eval/RESULTS.md) and [the complete report](eval/reports/blind-reading.json). This small fixture is not an across-subject accuracy claim. The earlier run's three false refusals and other failures remain preserved; runtime and prompts also changed, so these runs do not isolate the effect of a single change.

Handwriting check: a real five-page college lecture PDF exposed omissions, misread subscripts/array names and repeated OCR output. Gemma was incomplete and Qwen-VL stalled; GLM-OCR produced usable review drafts with an explicit stop workaround. Long outputs remain clearly marked partial. After visual transcription corrections, the current tutor returned two supported answers with the expected pages and refused one unrelated question; two quiz candidates passed independent verification. A separate public glassboard photo yielded four visually matching text/formula items. See [scan test observations](eval/SCAN_RESULTS.md), including the earlier incorrect accepted answer. These are assisted transcription observations, not a measured handwriting accuracy score. Run a private check with:

```sh
uv run --offline python -m scripts.check_scans /path/to/notes.pdf
```

The output is saved under ignored `data/scan-check.json`, contains private note text, and is never automatically indexed. Compare every page with its original image. GLM-OCR can omit code after Markdown fences; enter missing readable lines or exclude them.

The failed initial baseline is preserved in [eval/reports/baseline.json](eval/reports/baseline.json). Decisions, rejected candidates and earlier failures are recorded in [BUILD_LOG.md](BUILD_LOG.md).

## Limits

PDFs are limited to 30 MB, 300 pages, at most 20 scanned pages and 1,200 chunks each; split very large textbooks into chapters. Local scan transcription is an assisted review workflow, not reliable automatic handwriting recognition. Handwriting, diagrams, equations, layout and notation can be omitted or misread; inspect each original page and correct the text. No PPTX, video, auth, adaptive learning or dashboard. Quizzes use at most 20 pages and eight candidates per request and may return fewer questions after rejection. Short-answer practice is self-review. Q&A is stateless; ask complete questions rather than relying on pronouns from earlier turns.

Questions needing synthesis across several chunks may be refused; ask a narrower question. Explicit “value and unit” requests use typed numerical fields and require the result/unit to occur in the cited text, before independent verification. New numerical calculations outside the document's worked results are refused. Verification can miss errors, especially with small models. Inspect the cited evidence. The three-page evaluation is a smoke check, not a claim of measured performance across college subjects. Network disconnection has not been physically tested; application inference is restricted to installed local models and loopback HTTP.

## Project provenance and challenge status

At the author's request, CiteTutor adapts the existing **Course Companion** repository, which had code dated September 30. The published branch starts with one current snapshot; the earlier history is backed up separately and development decisions remain in `BUILD_LOG.md`. This history cleanup does not make the reused code new work. The [official Hacktoberfest weekend FAQ](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) excludes old projects and requires projects/repositories to start within the challenge window; **we do not claim this adapted repository satisfies that requirement**.

The weekend theme is **Build for a Friend**. The author identified a friend in college as the intended recipient; no handover feedback is claimed. Submission deadline: **October 5, 2026, 12:29 PM IST**. This repo contains an honest technical build and [DEV post draft](submission.md), not a published or eligibility-approved entry. Earlier multimodal and 15-day plans are historical documents under [docs/archive/](docs/archive/).
