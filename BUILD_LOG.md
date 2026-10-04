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
