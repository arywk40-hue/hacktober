# CiteTutor build log

This log records development before and after the published branch's history cleanup. Earlier commit IDs refer to the backed-up history, not the ancestry of the current snapshot.

## 2026-10-04 — Step 1: Re-scope the existing project

- The user chose to adapt the existing Course Companion code instead of starting fresh. Removed the empty nested repository created before that decision; no implementation was present there.
- Preserved the original Git history. The latest inherited commit is `ce6b082`, dated September 30. No commits were backdated, squashed, or invented.
- Checked the [official challenge page](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01): theme is Build for a Friend; window starts October 2 at 02:00 UTC and ends October 5 at 06:59 UTC (12:29 PM IST). Its FAQ excludes old projects and requires repositories to start within the window. This repo cannot honestly be described as eligible under that rule.
- Replaced the stale multimodal/15-day README. Archived earlier planning and submission documents so they cannot be mistaken for the current guide.
- Retain and simplify existing citation-validation, verifier, blind-solve, hybrid retrieval, and SQLite record code. New weekend work will be recorded in separate commits.
- Target runtime: one PDF; SQLite; in-process calls; Ollama-only local embeddings, Gemma generator, Qwen verifier. Drop workers, remote providers, visual ingestion, course graphs, learner records, and adaptive assessments.
- Recipient: the user replied “yes” to the friend-theme question but has not supplied a real person or need. No person, feedback, or handover story will be fabricated.
- Environment issue: `ollama` is installed but the server is not running. No live inference or quality claim is made yet.
- Verification for this documentation-only step: reviewed current history and official FAQ; no application behavior changed. Runtime/run-test instructions will follow with Step 2.

## 2026-10-04 — Step 2: Local college study backend

- User expanded scope from one PDF to college study help: multiple PDFs grouped by subject. A friend in college is the intended recipient; their subject and specific difficulty remain unspecified.
- Changed this checkout's `origin` from `Multimodal-2026` to `https://github.com/arywk40-hue/hacktober.git`, preserving all history. This does not reset provenance or solve the eligibility issue recorded above.
- Started local Ollama and installed Gemma 3 4B, Qwen 2.5 3B, and nomic-embed-text. Actual `/api/show` metadata confirms generator family `gemma`, verifier `qwen`, embedding `nomic-bert`; all local roles report ready.
- Reduced dependencies to FastAPI, PyMuPDF, SQLite/SQLAlchemy, HTTPX and Pydantic. Removed video/slides, queues, vector/DB servers, adaptive assessments and Docker orchestration. Reused and simplified inherited SQL records, BM25-like lexical ranks, reciprocal-rank fusion, draft verification and blind solving.
- Page text and overlapping chunks are persisted with document IDs. Indexing is atomic: failed extraction/embeddings leave no partial document. Exact-byte duplicate uploads reuse the original record within a subject.
- Tutor uses a sufficiency gate, at most three draft calls, exact chunk-ID checks, and per-segment independent support checks. Invalid drafts are retried at the pipeline level, with no hidden gateway retries. All failures produce the required visible refusal; unavailable inference is a separate 503 error.
- Quiz candidates need exact quotes after whitespace normalization. Independent retrieval feeds a blind solver without keys or rationales, then a separate support/agreement check. Only accepted questions enter the result. Counts/reasons are persisted in SQLite `quiz_run` records.
- Test fixtures deliberately rejected unknown citations, unsupported claims, malformed drafts, invented quotes and disagreeing quiz keys. These are contract tests, not live quality results.
- Validation: 27 tests passed; Ruff passed; actual installed model metadata checked. PyMuPDF/Starlette emitted dependency deprecation notices but checks passed.
- Run backend: `uv run --offline citetutor`, open `/docs`. Test: `uv run --offline python -m pytest -q`. Full study interface follows in Step 3.

## 2026-10-04 — Step 3: Subject-based study interface

- Built three views: Your material, Study together, Practice. Multiple uploads are indexed sequentially; documents can be chosen individually or studied together within one subject.
- Explanation/hint controls change presentation only. Citation chips include both document title and physical page and open full extracted page text. Quiz answers are revealed after a practice attempt or by opening the supporting-evidence section; short answers use transparent self-review rather than an unverified auto-grading claim.
- Practice displays accepted and rejected totals and rejection reasons, with no rejected questions. User input and PDF text are escaped or inserted as text. No CDN, remote fonts, telemetry, or model API in the browser.
- The console-script launch check exposed an editable-import issue in this Python environment. Added a module entry point and `./run.sh`, which changes to the repo and runs `uv run --offline python -m study`. It starts/checks local Ollama and does not download anything. The one-command launch now succeeds.
- Verified in Chrome: desktop library layout, all-models-ready status, subject dialog and successful subject creation. The user is actively using the browser, so further live evaluation uses an isolated temporary database. Full page-text and tutor/quiz contract behavior is also covered through the API tests.
- Validation: JavaScript syntax check passed; 27 core tests and Ruff passed. The app is running at http://127.0.0.1:8000.
- Run: `./run.sh` after setup. Test: `uv run --offline python -m pytest -q`. UI flow: create subject → add PDFs → Study together → Practice.

## 2026-10-04 — Step 4: Fix live false refusals and laptop defaults

- The first real evaluation took 1,245.5 seconds and refused all seven supported questions. It correctly refused all three out-of-scope questions, accepted one short-answer quiz item, and rejected one candidate for invalid question/verifier schema. Preserved the complete failed run in `eval/reports/baseline.json`. These results are not presented as success.
- A stage probe showed Qwen's preliminary coverage classifier calling an explicitly stated 8 N example “partial.” This extra classifier was a false-negative bottleneck; removed it and returned to the requested retrieve → structured draft → citation checks → independent verifier pipeline.
- The independent verifier now checks each segment against its own cited evidence in one structured response, validates the exact returned segment IDs, and separately checks completeness of the requested answer. A formula without a requested numerical value is incomplete and triggers a retry. No partially verified draft is displayed.
- Added short, per-request chunk aliases (C1…C4/C5), losslessly mapped to authoritative SQLite IDs. Unknown aliases still fail. Quiz aliases are resolved before source validation and independent retrieval, so retrieval order never changes citation identity.
- The machine is an 8 GB Apple M1; the larger models were slow under its active workload. Installed Gemma 3 1B and Qwen 2.5 1.5B as laptop defaults, with a 4,096-token context and immediate model unloading. The initially installed 4B/3B models remain available as optional choices.
- Added tests for incomplete answers, invalid verifier segment IDs, and a two-segment draft with one unsupported claim. Validation: 30 tests passed, plus Ruff.
- Run/test commands remain `./run.sh` and `uv run --offline python -m pytest -q`. A new live evaluation with the lighter defaults is in progress; final measured results follow in Step 5.

## 2026-10-04 — Step 5: Trace and remove unsupported draft padding

- The first lighter run still refused supported questions; its partial checkpoint is preserved in `eval/reports/lighter-first.partial.json`. Stopped that run to diagnose rather than repeatedly run the full suite without an explanation.
- An isolated trace showed Gemma correctly answering “8 N,” then adding an unsupported subtraction-based derivation and a gravity claim. The batch verifier also mismatched segment IDs/claims and returned a contradictory completeness flag. Such a pass could not be trusted.
- Constrained laptop Q&A drafts to one concise paragraph with one supporting chunk. This limits wide multi-chunk synthesis but avoids padding a correct answer with invented extra facts. Restored straightforward per-segment support/relevance checks with Qwen 2.5 3B. The smaller 1.5B verifier is installed but is not the default.
- The corrected real-model probe passed on its first draft: “The net force on the 2 kg body is 8 N.” with `sample.pdf [p. 1]`; independent Qwen support check passed. The exact stored page and quote were inspected.
- Replaced batch-specific tests with unknown quiz-ID rejection before blind solving, empty-subject refusal without inference, and embedding-model swap detection. Validation: 30 contract tests and Ruff pass.
- Final defaults: Gemma 3 1B, Qwen 2.5 3B, nomic-embed-text; 4,096-token context. Installed alternatives remain available locally. No cloud fallback or relaxed source checks.
- Run: `./run.sh`; test: `uv run --offline python -m pytest -q`. Final ten-question evaluation follows.

## 2026-10-04 — Step 6: Numerical completeness and usable quiz schemas

- The complete concise 1B/3B run answered five of seven supported questions correctly, cited all seven answers on the expected pages, and refused all three out-of-scope questions. Two answers gave only formulas despite explicit requests for a value and unit. Both quiz candidates were rejected for invalid schema. Preserved this run in `eval/reports/concise-first.json` rather than hiding it.
- Added a deterministic format guard for explicit “value and unit” requests: formula-only drafts without a number retry, and three failures refuse. Hints may omit the solution. This does not establish numerical correctness; independent factual verification still applies.
- Split MCQ and short-answer generation schemas. MCQ options are required and the key is constrained to A–D. Rotate one source chunk per candidate to keep the generation task focused, while independently retrieving source evidence for blind solving.
- A 1B trace still produced a poor MCQ and a statement in place of a short-answer question. The installed Gemma 4B generated a real MCQ with an exact quote; Qwen independently solved it as C and separately confirmed source support. Restored Gemma 4B as the recommended generator. Qwen 3B remains the verifier; nomic remains the embedding model. All installed smaller alternatives remain available.
- Added guidance against partially true MCQ distractors. No quote, citation, blind-solve or support gate was relaxed to increase acceptance.
- Validation: 32 contract tests and Ruff pass. Added cases for formula-only retries and a hint that legitimately omits the numerical solution.
- Run: `./run.sh`; test: `uv run --offline python -m pytest -q`. A final live ten-question run with the revised pipeline and defaults will supply the final measured results.

## 2026-10-04 — Step 7: Reproducible real-model evaluation

- Added an original three-page mechanics PDF, its authoring script, and ten explicit gold-labelled questions: seven supported and three out of scope. No college friend's material or response is included in evaluation artifacts.
- The evaluator indexes in an isolated temporary SQLite workspace and calls the production API handlers with installed models. Reports contain complete answers, citation-page checks, quiz rejections, token/latency counts, revision/start-worktree status and fixture hashes. Gold regex scoring is explicitly a heuristic, not a semantic proof.
- The revised type-specific-schema Gemma 4B probe produced both an MCQ and a short-answer candidate that passed exact-quote checks, independent Qwen blind solving and separate support checks. This is a focused probe; the complete final evaluation is the next recorded result.
- Preserved the failed baseline, interrupted lighter run and complete concise 1B run. Moved the prior project's adaptive simulation into the historical archive so it cannot be presented as a CiteTutor evaluation.
- Run full evaluation: `uv run --offline python -m scripts.evaluate`. Run app: `./run.sh`. Core tests remain 32 passing; Ruff and JavaScript syntax checks pass.

## 2026-10-04 — Step 8: Close the numerical format/citation gap

- Stopped the larger-model evaluation after its first five cases. Four answers matched the gold patterns, but the force answer still gave only a formula: the digit check incorrectly counted the exponent in `m/s^2`. The momentum answer also cited page 1 instead of its actual page 2 source; Qwen missed this. Retained the checkpoint in `eval/reports/larger-format.partial.json`.
- Replaced digit detection with a typed numerical draft containing result and unit. That result is appended to the answer BEFORE independent support verification, never afterward.
- Explicit “value and unit” requests also require a matching result/unit pair in their cited chunk. This prevents a wrong-page numerical citation from passing merely because the verifier knows the formula. It deliberately refuses new calculations not stated as worked results in the document. This limitation is documented.
- Added tests proving that the numerical result enters the verifier payload and that an absent worked result cannot pass even when the test verifier would otherwise approve.
- Validation: 34 tests pass; Ruff passes. Run/test/evaluation commands remain `./run.sh`, `uv run --offline python -m pytest -q`, and `uv run --offline python -m scripts.evaluate`.

## 2026-10-04 — Step 9: Final measured results and handover

- Completed the ten-question production-handler evaluation with real installed Gemma 4B, Qwen 3B and nomic, starting from clean revision `90bb37e`. Full outputs and fixture hashes are in `eval/reports/local.json`; a readable summary is in `eval/RESULTS.md`.
- Four of seven supported questions were answered correctly: first law, 8 N force, 6 kg m/s momentum and 30 J work. All four returned answers cited their correct physical pages. Three supported questions were falsely refused: third law, 9 J kinetic energy and 5 W power. All three out-of-scope questions were refused. Do not describe this as 100% question success.
- The final mixed quiz accepted two candidates and rejected zero. Its third-law MCQ key C and kinetic-energy short answer 9 J passed exact quotes, independent retrieval, blind Qwen solving and separate support checks. Manually compared their complete keys, rationales and quotes with pages 1 and 2. Earlier invalid-schema rejections remain in the preserved baseline/concise reports; failed source and disagreement gates are also covered by contract tests.
- Total evaluation time was 857.9 seconds. Returned-answer median was 52.0 seconds; the slowest refused request took 180.1 seconds. There were 27 chat-model calls with 23,100 input and 1,673 output tokens. These measurements reflect this small fixture and laptop, not a broad benchmark.
- Restarted the main app with the committed guards; existing subjects and uploaded PDFs remain saved. The one-command launcher succeeds, and all installed model roles report ready at loopback.
- Attempted a new screenshot using an isolated original-fixture workspace, without exposing the user's study material. Native UI tooling failed with a Sky startup error and then `cgWindowNotFound`; no screenshot or completed screen recording is claimed. Stopped the isolated demo server. The DEV draft provides an honest walkthrough and still needs a real image/recording and actual friend feedback before claiming them.
- Final checks: 34 pytest contract tests passed, Ruff and JavaScript syntax passed, and Git diff whitespace checks passed. Dependency deprecation notices remain non-failing. No physical network-disconnection test or challenge eligibility approval is claimed.
- Run: `./run.sh`, then open http://127.0.0.1:8000. Test: `uv run --offline python -m pytest -q`. Evaluate: `uv run --offline python -m scripts.evaluate`.

## 2026-10-04 — History cleanup requested by the author

- The author requested replacing imported history with one current snapshot while keeping the working project. This is a repository history cleanup, not a claim that the underlying code was newly built.
- Verified a complete Git bundle backup at `/private/tmp/citetutor-history-backup.dv5XrR/history.bundle` before replacing the published branch. The previously published tip was `b17814e88152c4b21f33aebe11334ad07c841215`.
- Abhishek's older change was fully reverted: the file-tree diff from `102b372` to `ce6b082` is empty. His author entries persisted because the imported history included his original, revert and merge commits. No retained code is being reassigned to a different author.
- Kept current source, tests, local study data and historical evaluation reports. Updated documentation to distinguish the current snapshot from the backed-up history. Report revisions continue to identify the actual code used for those runs.
- The snapshot uses the configured author and real current timestamp. Publication uses an explicit force-with-lease against the verified old tip, preventing an unexpected remote change from being overwritten.

## 2026-10-04 — Document the meaningful Gemma integration

- The author asked which partner technologies the project actually uses and to choose one prize category. Checked the current official weekend challenge page: local Gemma inference is a featured Best Use of Gemma route ($200 for its winner). Sentry Agent Tracing, Entire and ElevenLabs are separate $100 partner categories.
- Verified the running app's `/api/health`: Gemma 3 4B generator, Qwen 2.5 3B verifier, nomic-embed-text embedding model; all installed local roles report ready.
- Selected Gemma as the technology category target because it generates both tutor answers and quiz candidates in production. Added a component/role table to the README and specific code/runtime/report evidence to the DEV draft.
- No additional service or telemetry was added. Local token/latency records and BUILD_LOG are not presented as a Sentry or Entire integration. Narration from ElevenLabs is not claimed.
- This documentation change neither establishes overall eligibility for the adapted project nor promises a prize. The prior-work disclosure and measured quality limitations remain.
- Validation: reviewed the actual generator call sites, running model metadata and official category requirements; checked diff whitespace. Application code is unchanged, so the existing 34-test results remain applicable. Run and test commands remain `./run.sh` and `uv run --offline python -m pytest -q`.

## 2026-10-04 — Add optional Sentry Agent Tracing

- The author clarified that a Sentry or ElevenLabs integration must actually be added. Chose Sentry because the tutor's draft/verify/retry/refusal loop and independent quiz checks provide meaningful agent tracing. Gemma remains the local generation engine.
- Added and locked Sentry Python SDK 2.71.0. It initializes only with `CITETUTOR_SENTRY_DSN`; a generic `SENTRY_DSN` cannot enable it accidentally. Sampling is configurable and tracing defaults to off.
- Instrumented tutor and quiz transactions, hybrid retrieval, local embedding/chat calls, blind solving/support checks, draft rejections and quiz rejection counts/codes. Input/output tokens come from Ollama responses; missing counts and local hardware costs are not invented.
- Privacy is an outgoing allowlist, not just a PII flag: fixed labels, counters, timestamps and random trace IDs only. Automatic integrations, error/log/body capture, session tracking, profiles and AI span streaming are disabled. A final transport guard drops attachments and inherited envelope headers. Model/PDF content, filenames, source IDs and verifier explanations remain local. Custom model names are replaced with a fixed label.
- Added an enabled/disabled health indicator and a UI notice when Sentry metadata sharing is on. All inference remains loopback-only. A failed telemetry transport preserves the verified study answer.
- Problem hit: rebuilding SDK transactions without their event ID caused them to be discarded; timestamps arrive as ISO strings rather than numbers. Kept validated IDs/timestamps and proved a complete envelope is emitted. The SDK's per-span hook applies to streaming mode; this integration instead sanitizes the entire transaction and transport envelope.
- Added six real-SDK, in-memory-transport tests. They check no initialization when disabled, removal of private canary content/attachments, genuine gateway token counts, three refused/rejected tutor attempts, two quiz key disagreements and transport failure without changing answer behavior. These rejected counts use deterministic fixtures and are not claimed as model-quality measurements.
- Validation: all 40 tests passed; Ruff, JavaScript syntax and whitespace checks passed. Run with `./run.sh`; test with `uv run --offline python -m pytest -q`.
- Added `docs/SENTRY.md` and `scripts.trace_demo`: a temporary sample-PDF library exercises real local models; `--preview` uses an in-memory SDK transport and sends no events to Sentry. In the current preview, the supported force question passed on attempt one and a question outside the document's worked results refused after three attempts. The quiz is still running at this point; final metadata observations will be recorded separately.
- Created an ignored local `.env` template, with DSN blank. The author is creating the Sentry project using manual Python/FastAPI setup. A real project DSN and confirmed dashboard trace are still required before claiming live delivery or Sentry partner evidence. README and the DEV draft disclose that status.

## 2026-10-04 — Complete the real-model trace preview

- The local-only sample demonstration completed using Gemma 4B, Qwen 3B and nomic embeddings. Preserved the three sanitized SDK transactions in `eval/traces/local-preview.json`; these were captured in memory, not sent to Sentry. This run exercised the integration while its final configuration/docs were being completed, and is separate from the earlier ten-question quality evaluation.
- Supported force answer: accepted on attempt one, 140.85 seconds, two chat calls, 1,685 input tokens and 150 output tokens. The independent verifier ran before acceptance.
- Outside worked evidence: refused after three drafts, 465.02 seconds, three generator calls, 3,591 input tokens and 335 output tokens. All three rejection spans carry `unsupported_quantity`: the numerical result was absent from cited text. The deterministic source guard rejected each draft before an unnecessary Qwen support call. None was displayed.
- Mixed quiz: two accepted, zero rejected, 298.92 seconds, six chat calls, 4,966 input tokens and 660 output tokens. The span tree shows generation, independent retrieval, blind `Solve`, then `Verdict` for each candidate. Zero rejected here is an actual result; the disagreement/rejection path is covered by fixture tests rather than invented live failures.
- These chat token totals exclude embedding usage. These timings show substantial laptop latency and retry cost; they are not evidence of a tracing speed improvement and should not replace the earlier evaluation's results.
- Verified each exported transaction equals the current outgoing allowlist transformation. No questions, answers, PDF text, filenames, source identifiers, DSN or account credentials are included.
- Restarted the existing local server with the committed code; health reports all local models ready and Sentry disabled because the project DSN is still blank. Existing notes/library are retained. Core integration commit: `d32ebf2`.
- To generate live traces after configuration: `uv run --offline python -m scripts.trace_demo`. Confirm ingestion in the Sentry dashboard and capture the actual trace screenshot/link before completing the partner-category claim.

## 2026-10-04 — Configure and verify the live Sentry project

- The author provided the new project's DSN. Stored it only in ignored, permission-restricted `.env`, preserving other settings; no DSN or account credential is committed. Kept PII, automatic error capture and model input/output capture disabled rather than copying the generic onboarding snippet's permissive settings.
- Restarted the local app: all models ready, local-only inference true, Sentry enabled, content capture false. A content-free SDK transaction was accepted with HTTP 200 and visibly appeared in Sentry Traces.
- The first real-model demo returned a local-model HTTP 503 after about four minutes. Its received Agents trace showed the long generation stage and only embedding token usage. This is a failed model run, not a successful answer; it remains part of the observations.
- A focused real-model retry on the original sample PDF succeeded with one citation and one draft attempt. Used only a temporary library, a 600-second local-call timeout and a 256-token output cap. Production defaults and user study data remain unchanged.
- Successful trace: `66ca5eb26d1a46708f0497e55d9757ff`; tutor and Sentry transport both returned HTTP 200. Inspected it in the actual Sentry Agents timeline: five spans, hybrid retrieval, nomic embeddings, Gemma 4B chat, Qwen 3B chat, and no input text in the model panel. A real screenshot was captured in this session. Sanitized payload/delivery evidence is committed as `eval/traces/live-delivery.json`.
- Timing: 251.61 seconds overall; Gemma generation 227.15 seconds, Qwen support verification 23.74 seconds, embeddings/retrieval about 0.46 seconds. Gemma tokens 1,049 input/77 output, Qwen 469/27, embeddings 13 input. Generation dominates latency on this laptop; Sentry's automatic monetary estimates are not measured local hardware costs.
- Issue found through the failed trace: exception paths finished spans without an error status. Added fixed `internal_error` status/outcome for failed model/stage/request spans while continuing to drop exception text, error events and local variables. Added a privacy regression test for those paths.
- Validation after the fix: 41 tests passed, Ruff and whitespace checks passed. Run with `./run.sh`; test with `uv run --offline python -m pytest -q`. README and DEV draft now distinguish verified live delivery from earlier local-only captures and still disclose the failed/slow runs.

## 2026-10-04 — Check PDF and handwriting support status

- The author asked whether handwritten/whiteboard PDFs had also been tested. They have not been tested for recognition: the current extractor uses selectable text only and has no OCR path.
- Re-inspected the three uploaded PDFs locally without printing their text: 13 pages total, all with selectable text, 25 indexed chunks, and no embedded raster images. Successful indexing of these files does not demonstrate handwritten-note recognition or evaluated answer correctness on their contents.
- Created an image-only PDF by rendering one page of the original mechanics fixture to a raster image and embedding that image in a new PDF. It had one embedded image and zero selectable characters. Extraction correctly rejected it with `No selectable text found. Scan-only PDFs need OCR before upload`. This tests the scan rejection boundary, not real handwriting transcription.
- Real-model answer/quiz evaluation remains the authored text-PDF fixture: four of seven supported questions answered correctly, three false refusals, all three out-of-scope questions refused, and two verified quiz candidates. Handwritten scans, whiteboard photos, diagrams and OCR accuracy are not covered by those results.
- No OCR model was installed and no production behavior changed. Supporting image-only handwritten notes still requires a separate local recognition step and evaluation against actual handwriting samples.

## 2026-10-04 — Add local scan transcription and a review boundary

- Reused installed Gemma 3 4B vision weights through Ollama's base64-image chat API. Local metadata confirms `vision`; text-only or remote weights fail closed. No additional inference service or automatic downloads.
- Scanned pages are rendered locally with PyMuPDF, capped at 1,600 pixels on the longer edge. Uploads with scans persist as `needs_review` with zero indexed chunks, including mixed text/scan documents. At most 20 scanned pages per PDF. An explicit force-scan option handles poor existing text layers.
- OCR is one on-demand call per page, with a separate 600-second timeout and bounded output. The transcription prompt forbids guessing, explaining or obeying instructions in the image, and requests `[unclear]` markers. Truncated output is rejected. This does not guarantee recognition accuracy.
- Added original-page image, page transcription and whole-document approval endpoints. Approval requires every scanned physical page exactly once; unresolved `[unclear]` markers and all-empty documents cannot be indexed. Unreadable lines/pages may be excluded by leaving their reviewed text blank. Embedding failure preserves pending review without a partial index.
- Text and images stay local. The new OCR role/schema are explicitly allowlisted for metadata-only spans; image bodies and OCR content are excluded. Existing tutor/quiz verification operates only after review.
- Validation: 52 tests passed, including scan/mixed-page review, page identity, pending retrieval exclusion, incomplete/duplicate/unclear reviews, atomic embedding failure, vision capability enforcement and truncation. Ruff and whitespace checks passed. Rasterized test fixtures cover behavior only; real handwriting accuracy has not yet been measured.
- Run: `./run.sh`. API scan flow: upload PDF, `GET /api/documents/{id}/review`, `POST /api/documents/{id}/pages/{page}/ocr`, then `POST /api/documents/{id}/review` with version and corrected page text. Test: `uv run --offline python -m pytest -q`.

## 2026-10-04 — Add the scan review screen and test actual notes

- Added a side-by-side original-page image and editable draft, a page selector, local transcription button, explicit page checks and whole-document approval. Pending PDFs have a Review scans action and are excluded from study/practice selectors. Citation dialogs show scan provenance and original images after approval.
- The author supplied `CS212-Lec10.pdf`: five image-only handwritten pages about matrix-chain multiplication. Uploaded it into the existing local library as pending, zero chunks. Original PDF and raw draft outputs are ignored/private; they are not published as repository fixtures.
- Inspected the review screen in the real Chrome app and captured its current layout. Page images and controls render without overlap. Existing subjects and PDFs are retained.
- Gemma 4B first-page OCR failed completeness: only three matrix labels, 10 characters, 116.92 seconds. Page two hit the output limit after 562.66 seconds and was rejected, not indexed. Stopped the remaining Gemma run rather than treating these outputs as useful transcription. Testing Qwen2.5-VL 3B local weights next; no recognition accuracy is claimed yet.
- Validation: all 52 tests passed; Ruff, JavaScript syntax and whitespace checks passed. Run `./run.sh`, upload the PDF, click Review scans. Test `uv run --offline python -m pytest -q` and `node --check study/static/app.js`.

## 2026-10-04 — Use dedicated local OCR and retain recognition failures

- Qwen2.5-VL 3B full-page inference stalled on the 8 GB laptop and was cancelled without a completed result. Upgraded local Ollama from 0.13 to 0.35.1 and pulled GLM-OCR q8 (about 1.6 GB). No cloud recognition service or fallback was added. GLM-OCR is now the independent scan role; Gemma remains the tutor/quiz generator.
- Used the model's native `Text Recognition:` generate endpoint. Initial outputs repeated until the token cap. End-of-text stop tokens alone did not fix our runs; a Markdown-fence stop and repetition penalty produced more useful drafts. The fence can omit code and is explicitly disclosed. Longer GLM responses remain partial review drafts; exact repeated blocks are trimmed without interpreting or repairing text. Generic chat-JSON truncation still fails closed.
- Actual lecture-page runs: pages 1/3/4/5 took 24.52/29.11/28.23/26.30 seconds; page 2 took 99.99 seconds and was partial. Visible errors included a missing dimension zero, omitted highlighted content, misread array name and infinity symbols, and broken pseudocode/subscripts. Page 5 was mostly blank. No accuracy percentage is claimed.
- Added a private draft-check CLI, partial warnings, content-free OCR transaction metadata, and tests ensuring images/base64/transcription cannot enter Sentry envelopes. Original PDFs and drafts remain ignored under `data/`.
- The production library was separately approved while testing was underway: only page 1 had text and pages 2–5 were blank. This test did not perform that approval. Added Review again, which preserves originals/text and atomically removes derived chunks until reapproval; stale versions fail.

## 2026-10-04 — Test source relevance and glassboard reading

- Prepared a temporary library with visually corrected readable lecture text, explicitly marked as Codex corrections rather than user approval. Initial tutor output answered matrix dimensions correctly but accepted initialization instead of the requested array-cell meaning. Both quiz candidates passed independent blind solving and literal-source checks, with zero rejected; the unrelated question refused. Retained the wrong tutor answer and its passing verifier verdict privately.
- Added independent blind source reading before tutor draft agreement/support checks. The verifier sees no draft, key or learner style during that reading. Unsupported/ambiguous readings reject the attempt; the existing three-draft limit/refusal remains. The revised real-model smoke test answered the array purpose on page 4 (34.66 s), dimensions on page 1 (43.26 s), and refused an unrelated question (16.97 s). This is not a ten-question benchmark.
- Tested a public glassboard-style photo directly through local GLM-OCR: four visible text/formula items matched visual inspection in 48.15 s, with 4,072 input and 87 output tokens. No indexing or diagram understanding claimed. Attribution: [Learning Physics](https://commons.wikimedia.org/wiki/File:Learning_Physics.jpg), Preply.com Images / preply.com, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).
- Published aggregate observations in `eval/SCAN_RESULTS.md`; full private outputs/errors remain in `data/handwriting-check/RESULTS.md` and JSON records. Updated the earlier ten-question report's description to identify its older pipeline.
- Validation: 56 contract tests passed, Ruff, JavaScript syntax and whitespace checks passed. Run `./run.sh`; test `uv run --offline python -m pytest -q`; capture local drafts with `uv run --offline python -m scripts.check_scans /path/to/notes.pdf`.

## 2026-10-04 — Evaluate the revised pipeline and restart the app

- Committed the tested dedicated OCR, partial-draft/review handling and blind tutor reading as `e9b43e4`. Started the ten-case original mechanics evaluation from a clean worktree against installed local weights, with Sentry disabled and an isolated temporary library. Preserved earlier reports.
- Full results: seven of seven supported answers matched the gold patterns and visual source comparison; seven of seven citations pointed to the expected document/pages. All three out-of-scope questions returned the exact refusal. Zero false refusals in this run. One answer retains a raw C1 alias in its prose despite a valid page citation.
- The mixed quiz accepted one short answer (9 J kinetic energy, page 2), whose key/rationale/quote matched the fixture. It rejected one MCQ for `Blind solver disagreed with the answer key`; the item was dropped. This gate outcome does not prove which model was wrong. The report retains actual counts and reasons, not an invented rejection example.
- Total 478.99 seconds; returned tutor median 44.5 seconds (34.3–57.6 range). 29 chat calls, 22,677 input and 2,009 output tokens, excluding embeddings. Ollama/runtime and prompts changed since the older 4/7 run, and model output varies; no isolated-cause improvement or broad accuracy claim.
- Report: `eval/reports/blind-reading.json`; readable comparison: `eval/RESULTS.md`. Reproduce with `CITETUTOR_SENTRY_DSN= uv run --offline python -m scripts.evaluate --output eval/reports/new-run.json`.
- Restarted `./run.sh` and verified all four local model roles ready, content capture off, and Review again route loaded. The original scan approval/text remained unchanged (page 1 included, pages 2–5 empty). Browser showed CRV.pdf selected for a matrix-multiplication question; the correct document must be selected. The prior scan-review UI was visually inspected; a later refresh lost its Chrome window, so no final re-review action or new screenshot is claimed.
- Existing code checks remain 56 passing tests, Ruff, JavaScript syntax and whitespace checks. Documentation/report changes are reviewed separately. Eligibility of reused pre-window code remains unresolved; no submission or prize eligibility is claimed.

## 2026-10-04 — Prepare the recording and partner evidence

- Rechecked the official weekend page and template: the DEV post is the entry, Demo asks for a deployed link or video, and Sentry requires traces/screenshots plus performance/debugging findings. Added `docs/DEMO.md` with a three-minute shot list, exact sample prompts, narration, component responsibilities, a local-data/metadata diagram, screenshot captions and publication requirements. Linked it from README and the unpublished submission draft.
- Gemma is the central tutor/quiz draft generator; Qwen independently verifies; GLM-OCR reads images locally. Sentry observes token/timing/count metadata and does not recognize images or enforce source support. The recording guide makes these roles explicit, shows actual verification/rejection evidence, and labels shortened inference waits.
- Extended `scripts.trace_demo` with focused tutor, quiz and OCR modes, preserving the existing default tutor/refusal/quiz run. OCR accepts an explicit local demo-image path, prints only counts/status/trace ID, and never approves or indexes the image. Preview mode sends nothing to Sentry.
- A real GLM-OCR preview of the public glassboard photo took 60.18 seconds, with 4,072 input and 87 output tokens. Inspected the SDK envelope: no image, base64 body, filename or recognized text. Preserved sanitized evidence in `eval/traces/ocr-preview.json`; it is a local SDK capture, not a live dashboard screenshot. Photo credit: Preply.com Images / preply.com, Learning Physics on Wikimedia Commons, CC BY 2.0.
- The first permission review for the local rehearsal timed out before process start. Retried once as permitted, and it completed; no unsafe-action finding or remaining approval block. Browser capture attempts met active window changes/closure; no fresh screenshot or finished video is claimed. A live OCR trace generation follows separately.
- Run: `uv run --offline python -m scripts.trace_demo --preview --case ocr --ocr-image /path/to/public-demo-image.jpg`; omit preview only for configured Sentry metadata delivery. Ruff and whitespace checks passed. Video export/upload, actual screenshots and eligibility clarification remain before publication.

- Subsequent live OCR run completed and the exact trace `9dd839e0c7304be8b77640221506af80` was inspected in Sentry Traces and Agents. Model 59.07 s, root 59.09 s, 4,072 input / 87 output tokens, no indexing. Agent Activity says No input for this span. Captured a real clean-window screenshot in this chat; it has not been saved to a repository PNG. Recorded content-free verification evidence in `eval/traces/ocr-live.json`. All 56 contract tests still pass; Ruff and whitespace checks pass. No finished video or published DEV entry is claimed.

- Focused current tutor rehearsal completed using only the original mechanics fixture. Supported request: first-attempt answer, exact trace `08998f10d6f341e9a9a95454c5de60ba`, root 45.73 s. Inspected Gemma NumericalDraft (24.84 s, 1,215/79 tokens), Qwen blind Solve (9.68 s, 490/78), and following support-check span (10.80 s, 633 total displayed tokens) in Agents. The outside-worked-evidence request refused after three attempts, exact trace `e67e9be1c0db41d2b5fba5d2f9e24ae6`, root 1.66 min. Three rejection spans are visible; the first code is unsupported_quantity. These source-guard rejections precede Qwen, so they are not described as Qwen verdict failures.
- Captured clean-window actual Gemma/privacy and rejection screenshots in chat. Preserved content-free timing/count/trace-link observations in `eval/traces/current-tutor-live.json`; screenshots are not yet repository PNG files. This provides live evidence of the current pipeline rather than relying on the older single-verdict trace. User study data was not modified; recording/export/upload and the eligibility clarification remain outstanding.

## 2026-10-04 — Review published submissions and improve the write-up

- Enumerated 199 unique posts from the public hf26challenge feed; page 3 was empty in this snapshot. Read selected problem/testing/handover passages across all 199 and closely compared 26 relevant write-ups (18 in the snapshot and eight older related-page posts). Article text was available through 180 API responses plus 19 HTML recoveries. This is not an exhaustive audit of every submission, repository, demo or testimonial. Full downloaded article bodies remain in a temporary research directory, outside the repository.
- Added docs/SUBMISSION_REVIEW.md with source links, subjective scores, comparison lessons and bounded priorities. Added docs/SUBMISSION_COVERAGE.csv distinguishing selected-passage screening from close comparison. Reactions and partner mentions were not treated as proof of quality or prize odds. No competitor code was copied.
- The author reported that one college friend tried their own course chapter and found CiteTutor useful but a little slow. Added that reported feedback to submission.md without inventing a direct quote, course, question, learning gain or timing.
- Rewrote the unpublished draft around verification before display and shortened it from 1,778 to 1,149 words. Replaced repetitive historical tracing descriptions with the current supported/refused/OCR table, preserving linked historical results. Explicitly separated Gemma generation, Qwen verification, GLM-OCR image reading and Sentry observation.
- The review rated overall submission readiness about 7/10, with unfinished video/screenshots and a small evaluation limiting presentation/reliability evidence. Source grounding is common among study entries; CiteTutor should show its blind checks and rejected candidates rather than add features.
- Earlier-code eligibility remains unresolved. The review contains an organiser question for the author to send; no message or DEV publication was sent. A repository/history reset is not evidence of fresh code. Actual media export, another chapter evaluation and the appropriate scan re-review remain outstanding.
- Validation: whitespace check, local Markdown links, CSV uniqueness/counts and trace/evaluation claims checked against existing records and source. Documentation only; no runtime changes, new benchmark, model downloads or user study-data changes. Run remains ./run.sh; prior runtime test results are unchanged.


## 2026-10-04 — Fill the official DEV template

- Added the official challenge attribution, a clear pending-video placeholder and the optional My Agent Session section to submission.md, preserving the template order. Disclosed Codex assistance and linked the actual build log without claiming it is an exported DevRelay transcript.
- Kept reported friend feedback, real measured results, partner roles, scan-review limits and earlier-code provenance. No video, screenshot export, agent-session upload, external message or DEV publication was invented or performed.
- Validation: template headings/order, local links and whitespace checked. Documentation-only change; run remains ./run.sh and no runtime tests were rerun.
