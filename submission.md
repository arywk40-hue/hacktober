---
title: "CiteTutor: a local Gemma tutor that verifies before it answers"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

<!-- Before publishing: replace the video placeholder. Actual Sentry dashboard captures are included below. Resolve eligibility with the organisers; this adapts code written before the challenge window. -->

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

I asked one college friend to try CiteTutor on a chapter from their own course material. Their feedback was that it worked well, but was a little slow.

They were right about the wait. In a separate measured mechanics-fixture request, Gemma spent 24.84 seconds drafting an answer, and two Qwen checks took another 20.48 seconds. CiteTutor displays an answer only after those checks pass.

That is the design choice at the centre of CiteTutor: **check the explanation before the learner starts studying from it.**

CiteTutor runs on a laptop. My friend can organise PDF notes and textbook chapters by subject, ask for explanations or hints, and generate practice questions from a chosen page range. A displayed tutor answer includes page citations that open the source text. Reviewed scans also retain their original page images.

Gemma writes the draft. Code checks its citation IDs. A different model family independently reads the evidence and checks factual support. Failed drafts stay hidden. After at most three attempts, the tutor either returns a cited answer or says:

> Not enough evidence in this document

These checks can still make mistakes. Their purpose is to give the learner an inspectable answer and a visible refusal when the pipeline cannot support one.

## Demo

**[ADD YOUR PUBLIC VIDEO LINK HERE]**

<!-- Record/export the video before publishing. Do not describe the shot list as a finished demo. -->

![Actual CiteTutor answer to the mechanics fixture's force question, showing 8 N, a page 1 citation and the separate-model check.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/app-verified-answer.png)

*Real local-app capture from October 5: the worked example returns 8 N with a clickable page citation. This rehearsal is separate from the ten-question evaluation below.*

The [recording guide](https://github.com/arywk40-hue/hacktober/blob/main/docs/DEMO.md) covers the complete path: upload a sample PDF, ask a supported question, open its citation, show an unrelated question refusing, generate a quiz, review a scan, and inspect the corresponding Sentry stages.

After the one-time dependency installation and model pulls:

```sh
./run.sh
```

Open http://127.0.0.1:8000. The [README](https://github.com/arywk40-hue/hacktober#setup) includes the setup commands.

## Code

[CiteTutor on GitHub](https://github.com/arywk40-hue/hacktober)

CiteTutor adapts my earlier Course Companion implementation, which predates the challenge window. The [build log](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md) records that provenance and the subsequent development. Eligibility for this adaptation still needs organiser clarification.

## How I Built It

The application is a local **retrieval-augmented generation (RAG)** pipeline: Python, uv, FastAPI, PyMuPDF, SQLite and a small HTML/JavaScript frontend. Ollama runs the models; the application makes in-process calls without a queue or database server.

| Model | Job |
|---|---|
| `gemma3:4b` | Generate structured explanations and quiz candidates |
| `qwen2.5:3b` | Independently solve and judge source support |
| `nomic-embed-text` | Embed document chunks and questions |
| `glm-ocr:q8_0` | Draft scan transcriptions for human review |

![CiteTutor architecture: local ingestion, reviewed OCR, hybrid retrieval, Gemma generation, citation guards, Qwen verification, and optional metadata-only Sentry tracing.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/assets/citetutor-architecture.png)

*Implemented architecture. Tutor answers and practice questions have separate acceptance gates; optional telemetry crosses a metadata-only boundary.*

### 1. Preserve the page before asking the model

A citation is useful only if it points back to the right material.

PyMuPDF extracts text per physical page. Chunks are at most 1,600 characters with 200-character overlap, and never cross page boundaries. SQLite stores their text, vectors, document identity and page number.

Retrieval combines **BM25-style keyword ranking** and **cosine similarity over nomic embeddings**, merged with **Reciprocal Rank Fusion**. Exact terminology and differently worded questions can therefore contribute to the ranking. The default budget is four chunks, restricted to the selected subject and documents.

This is a small local vector store: similarity is calculated in process. The embedding model's identity is stored so changing models cannot silently mix incompatible vectors.

![Actual source-page dialog opened from the answer citation, showing the original page 1 text and the 8 N worked example.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/app-source-page.png)

*Clicking the citation opens the stored source page, including the worked example used in this answer.*

### 2. Separate drafting from permission to display

Gemma receives the retrieved evidence and returns answer segments with supplied chunk IDs. Ollama receives a **Pydantic-derived JSON Schema**, and the application validates the returned JSON again.

Unknown or missing citations fail. Code resolves valid IDs to stored page numbers; the model cannot choose arbitrary citation targets.

The next step is a **blind Qwen solve**: it receives the question and cited evidence without Gemma's draft or the learner's explanation style. Only afterwards does a separate Qwen call inspect the draft for relevance, agreement with that reading, and source support for every claim.

```text
Retrieve → Gemma draft → schema and citation guards
         → blind Qwen solve → support check
         → display, retry, or refuse
```

This extra reading came from a real failure. An earlier handwritten-notes test returned array initialization when the question asked what an array cell meant. The earlier verifier accepted that related but irrelevant answer. I added blind source reading before draft agreement to make the requested meaning explicit.

The current prompt asks for one concise paragraph using the best supporting chunk. Learner context changes wording, never evidence. Explicit “value and unit” requests also require the worked quantity in the cited text, which can conservatively refuse a new calculation.

**Nothing is streamed before verification.** Different model families and separate calls reduce some failure modes; they do not make the judgment infallible.

### 3. Hide the quiz key from the solver

A question can quote a real sentence and still have the wrong key.

Gemma generates an MCQ or short-answer candidate with source IDs and supporting quotes. Code checks its schema and verifies the quotes are literal source substrings after whitespace normalization.

The application then retrieves evidence again using the stem and options. Qwen sees that evidence and the question, but **no proposed key, rationale or generator-supplied quote**.

MCQs require key agreement; short answers require semantic agreement. A separate support check also judges the proposed key and rationale against the source. Unsupported, ambiguous or disagreeing candidates are dropped, and the UI reports the rejected count.

![Actual practice screen showing one verified question and one rejection for blind-solver key disagreement, with the accepted 9 J answer, source quote and page 2 citation.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/app-verified-quiz.png)

*Fresh October 5 rehearsal: one candidate passed and one was rejected. The expanded answer includes its supporting quote and page citation; these are actual outputs, not staged data.*

### 4. Treat handwriting as evidence that needs review

Full-page Gemma transcription was incomplete; a Qwen-VL experiment stalled. Dedicated GLM-OCR produced more useful drafts, but misread dimensions, subscripts, an array name and infinity symbols.

Scanned PDFs therefore stay outside retrieval until every scanned page has been reviewed against its original image. The learner can edit the transcription. Partial output is labelled, and blank reviewed pages are excluded.

The verifier reads approved text. It cannot repair an OCR mistake hidden in that text. Human review is part of the ingestion process.

### 5. Test the complete path, including refusals

On an **8 GB Apple M1**, I ran ten questions against an original three-page mechanics PDF. The preserved reports show:

| Check | Earlier run | Revised run |
|---|---|---|
| Supported answers correct | 4 / 7 | 7 / 7 |
| False refusals on supported questions | 3 / 7 | 0 / 7 |
| Unrelated questions refused | 3 / 3 | 3 / 3 |

The revised answers had the expected document/page anchors in all seven cases. Returned tutor latency was **44.5 seconds median**, with a 34.3–57.6-second range.

The mixed quiz accepted one short-answer question using the source's **9 J** kinetic-energy example on page 2. It rejected one MCQ because the blind solver disagreed with its key. That records disagreement, not proof of which model was wrong.

![Recorded earlier and revised CiteTutor evaluation counts, plus the timing breakdown of a separate 45.73-second live Sentry trace.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/assets/citetutor-results.png)

*Same small fixture, two recorded runs. Prompts and runtime changed, so this is not a controlled ablation. The latency plot reconstructs a separate live trace; it is not a dashboard screenshot.*

This is a developer-authored smoke evaluation, not general accuracy across college PDFs. Correctness used gold patterns and source comparison; citation accuracy checked document/page anchors. Earlier failures remain in the [evaluation report](https://github.com/arywk40-hue/hacktober/blob/main/eval/RESULTS.md) and [scan observations](https://github.com/arywk40-hue/hacktober/blob/main/eval/SCAN_RESULTS.md).

Separately, 56 automated contract tests passed for implementation behavior, including chunking, citation/refusal handling and telemetry privacy. Those tests do not measure model accuracy.

## Why Does Open Innovation Matter?

**The model roles do the central work.** Nomic retrieves, Gemma drafts, Qwen verifies, and GLM-OCR transcribes. Open-weight models let those operations run through local Ollama without a hosted-model fallback or per-request AI API charges. Physical network-disconnection testing remains pending.

**The study material stays local.** My friend's documents, questions and answers remain on their laptop. Optional Sentry tracing exports only allowlisted operational metadata; leaving its DSN blank disables it.

**The models are replaceable.** Switching the scan role to GLM-OCR was useful when the earlier vision experiments failed. I could change that role while retaining Gemma tutoring and the same acceptance policy.

**The policy is inspectable.** Retrieval, citation mapping, quote validation and rejection rules are application code that can be reviewed and changed. Model-specific licences still apply, and hardware and electricity have costs.

My friend's speed criticism remains fair. Serial inference and unloading weights help limit laptop memory use, but introduce a latency trade-off. The next improvement should preserve the checks while making the wait easier to live with.

## My Agent Session

I used Codex to assist with implementation, debugging, testing and documentation, while directing the scope and product decisions.

[BUILD_LOG.md](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md) records failed experiments, design changes and actual rejection outcomes. It is a development record; no exported DevRelay session is claimed.

## Prize Categories

The intended categories are conditional on resolving the adaptation's eligibility.

### Best Use of Gemma

Gemma generates both core outputs: tutor explanations and practice questions. Its structured responses feed the citation and verification gates. Its actual role is visible in the health endpoint, evaluation records and live generation spans.

### Best Use of Sentry Agent Tracing

Sentry helped make the waiting time explainable. I instrumented tutor, quiz and OCR operations with spans for retrieval, generation, blind solving, support checks and rejection.

| Inspected live trace | Observation |
|---|---|
| Supported answer | 45.73 s total: Gemma 24.84 s, blind Qwen solve 9.68 s, support check 10.80 s |
| Refused request | 1.66 min and three rejected drafts; first rejection was `unsupported_quantity`, before Qwen ran |
| Public glassboard OCR | GLM-OCR call 59.07 s; 4,072 input / 87 output tokens |

The supported trace connects directly to the friend feedback: two verification calls added 20.48 seconds. The refusal trace shows how retries increase the wait and distinguishes source-guard rejection from model-verifier rejection.

An event/span field allowlist and a second filter at the SDK transport boundary exclude documents, images, filenames, questions, answers and free-form model text. The inspected AI span showed **“No input for this span.”**

Sentry observes timing, tokens and outcomes. Source checks remain local.

![Actual Sentry Agent Activity screenshot showing the local Gemma drafting span, both Qwen verification calls, token counts and No input for this span.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/sentry-gemma-privacy.png)

*Actual dashboard capture of the recorded 45.73-second tutor request. Gemma drafts for 24.84 seconds; Qwen performs the following checks. The input panel contains no model content.*

![Actual Sentry refusal waterfall showing three Gemma drafts and three Draft rejected spans over a 1.66-minute request.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/sentry-refusal-waterfall.png)

*Three drafts were rejected by source guards before Qwen ran. This is the preserved request from October 4, captured in the dashboard on October 5.*

![Actual Sentry OCR span showing local glm-ocr:q8_0, 59.07 seconds, token counts and No input for this span.](https://raw.githubusercontent.com/arywk40-hue/hacktober/main/docs/demo/sentry-ocr-privacy.png)

*The public glassboard transcription ran locally. Sentry shows timing and tokens, with no image or transcription input captured.*

[Verified tutor traces](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/current-tutor-live.json), [OCR trace](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/ocr-live.json), and [Sentry setup/privacy details](https://github.com/arywk40-hue/hacktober/blob/main/docs/SENTRY.md) are in the repository.

Public demo photo: [Learning Physics](https://commons.wikimedia.org/wiki/File:Learning_Physics.jpg), Preply.com Images / preply.com, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).
