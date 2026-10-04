---
title: "CiteTutor: local Gemma, blind verification, and citations you can inspect"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

<!-- Publication checklist: add an accessible demo video and exported Sentry screenshots. Resolve eligibility with the organisers: this adapts pre-existing Course Companion code, and the challenge FAQ excludes old projects. A history reset does not make earlier code new. -->

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

One college friend tried CiteTutor on a chapter from their own course material. Their feedback was that it worked well, but was a little slow.

That feedback captures the project's main trade-off. **CiteTutor shows an answer only after its citations and factual support pass separate checks.** Gemma drafts; a different model family independently reads the evidence; code controls what reaches the learner.

CiteTutor is a local, source-grounded study tutor. My friend can organise PDF notes and chapters by subject, request explanations or hints, and generate MCQs and short-answer practice from selected pages. Every displayed tutor answer has clickable page citations. If no draft passes within three attempts, it returns **“Not enough evidence in this document.”**

The aim is to make answers easy to inspect against the course material. Learner preferences can change the explanation style, but never count as factual evidence. My friend's feedback is one real trial, not a measured learning outcome; their notes remain private.

## Demo

**Video: [ADD YOUR PUBLIC VIDEO LINK HERE]**

<!-- Recording and screenshot exports remain pending. Use docs/DEMO.md for the shot list; it is not a finished demo. Label edited waits with their actual duration. -->

The demo should follow one complete study session: upload the original mechanics sample, ask a supported question, inspect its citation, show an unrelated question refusing, and generate practice with visible accepted/rejected counts. It should also show scan review and the real Sentry traces behind generation, verification and rejection.

After setup, run:

```sh
./run.sh
```

Open http://127.0.0.1:8000. [Setup and model pulls](https://github.com/arywk40-hue/hacktober#setup) and the [recording guide](https://github.com/arywk40-hue/hacktober/blob/main/docs/DEMO.md) are in the repository.

## Code

[CiteTutor on GitHub](https://github.com/arywk40-hue/hacktober)

**Provenance:** CiteTutor adapts my earlier Course Companion implementation, which predates the challenge window. Earlier development and subsequent changes are documented in [BUILD_LOG.md](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md). Eligibility for this adaptation still needs organiser clarification.

## How I Built It

The core is a **local retrieval-augmented generation (RAG) pipeline**, built with Python, uv, FastAPI, PyMuPDF, SQLite and a minimal HTML/JavaScript frontend. Ollama runs all model inference locally. Calls execute in process; there is no queue or database server.

| Local model | Responsibility |
|---|---|
| `gemma3:4b` | Structured tutor drafts and quiz candidates |
| `qwen2.5:3b` | Blind solving, source-support and answer-agreement checks |
| `nomic-embed-text` | Document and query embeddings |
| `glm-ocr:q8_0` | Optional transcription of scanned pages |

### Page-preserving retrieval

PyMuPDF extracts text per physical PDF page. I split it into overlapping chunks, with a maximum of **1,600 characters and 200-character overlap**, without crossing page boundaries. Each chunk retains its document identity and page number.

Retrieval combines **BM25-style keyword ranking** with **dense cosine similarity**, then merges both rankings using **Reciprocal Rank Fusion**. Keyword matching helps preserve exact terms; embeddings help retrieve differently worded questions. Nomic receives separate `search_document:` and `search_query:` prefixes.

SQLite stores the chunks and vectors. Similarity is calculated in process over the small local corpus; this is deliberately a simple vector store. The default retrieval budget is four chunks, scoped to the selected subject and documents.

### Schema-constrained answers with source provenance

Gemma returns JSON conforming to a **Pydantic-derived JSON Schema**, passed through Ollama's structured-output interface. The application validates the result again before using it.

The display path is:

```text
Retrieve → Gemma draft → schema/citation guards
         → Qwen blind solve → support/agreement check
         → cited answer, or retry/refusal
```

Each answer segment must reference supplied chunk IDs. Code rejects unknown or missing IDs and resolves valid IDs to authoritative stored page numbers. The model does not get to invent citation targets.

Next, Qwen answers the question from the cited evidence **without seeing Gemma's draft or the learner's explanation style**. A separate Qwen call then judges whether the draft answers the same question, agrees with that blind reading, and has source support for every claim. Using a different family and withholding the draft during the first pass is intended to reduce anchoring; it is not a proof of correctness.

For explicit “value and unit” requests, a source guard also requires the worked quantity to appear in the cited text. That is conservative: it can refuse a new calculation even when a formula is available.

The pipeline permits at most three drafts and **never streams unverified text**. The current laptop prompt asks for one concise paragraph using the single best supporting chunk. These constraints keep the task manageable for small models.

### Practice questions have a separate acceptance gate

A plausible question and a real quotation can still have an incorrect answer key. Quiz verification therefore checks more than quotation presence:

1. Validate the question schema, source IDs and literal supporting quotes after whitespace normalization.
2. Retrieve evidence again using the stem and options, excluding the proposed key and rationale.
3. Ask Qwen to solve using only that evidence, with no proposed key, rationale or generator-supplied quote.
4. Require an unambiguous supported answer, MCQ key agreement or short-answer semantic agreement, and a separate source-support judgment.

Failed candidates are dropped before display. The UI reports accepted and rejected counts with rejection reasons.

### OCR is a reviewed input boundary

Handwriting exposed a different problem: verification cannot repair evidence that was transcribed incorrectly.

Gemma's full-page transcription was incomplete, and a Qwen-VL experiment stalled. Dedicated GLM-OCR produced more useful drafts, but still misread dimensions, subscripts, an array name and infinity symbols. Repeated or truncated output is marked partial.

Scanned PDFs remain outside retrieval until every scanned page is reviewed against its original image. The learner can correct the transcription; blank reviewed pages are excluded. This is **human-reviewed local OCR**, with the approved text serving as the verifier's evidence.

### What I actually tested

The revised pipeline ran ten questions against an original three-page mechanics PDF on an **8 GB Apple M1**, using the installed local models:

| Check | Observed result |
|---|---|
| Supported answers correct | 7 / 7 |
| Citations on expected document/pages | 7 / 7 |
| Out-of-scope questions refused | 3 / 3 |
| False refusals on supported questions | 0 / 7 |
| Quiz candidates | 1 accepted, 1 rejected |
| Returned tutor latency | Median 44.5 s; range 34.3–57.6 s |

The accepted short-answer question used the source's **9 J** kinetic-energy example on page 2. The MCQ was rejected because its key disagreed with the blind solver. That disagreement records a gate outcome; it does not establish which model was wrong.

This is a small developer-authored smoke evaluation, not an across-course accuracy benchmark. Correctness used gold patterns and source comparison; citation accuracy checked document/page anchors. Earlier false refusals and an irrelevant answer that passed an earlier verifier remain documented in [evaluation results](https://github.com/arywk40-hue/hacktober/blob/main/eval/RESULTS.md) and [scan observations](https://github.com/arywk40-hue/hacktober/blob/main/eval/SCAN_RESULTS.md).

Separately, **56 automated contract tests** passed for implementation behavior, including chunking, citation/refusal handling and telemetry privacy. Those tests do not measure model accuracy.

## Why Does Open Innovation Matter?

Open-weight models perform the central tasks: retrieval, drafting, verification and scan transcription. After dependencies and weights are installed, the core uses local Ollama with **no hosted inference fallback or per-request model API charges**. Physical network-disconnection testing remains pending.

Local execution keeps my friend's documents, questions and answers on their laptop. Sentry is optional: with its DSN blank, tracing stays disabled; when enabled, only allowlisted operational metadata is exported.

Separate, configurable model roles also let me change the generator, verifier or OCR model for different hardware. The failed transcription experiments made that flexibility useful: I could replace the image-reading role while retaining Gemma for tutoring and the same source checks.

The code exposes the retrieval, validation and acceptance policy for inspection. Model-specific licences still apply, and hardware and electricity still cost money. The current cost is also time: serial inference and unloading models between calls limit memory use but introduce a latency trade-off.

## My Agent Session

I used Codex to assist with implementation, debugging, testing and documentation, while directing the scope and product decisions.

The [build log](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md) records failed experiments, design changes and actual verifier rejections. It is a development record; no exported DevRelay session is claimed.

## Prize Categories

The intended categories are conditional on resolving the adaptation's eligibility.

### Best Use of Gemma

Gemma is the core generator for both tutor explanations and practice questions. Its structured drafts enter the application's citation and verification gates before reaching the learner. Its role is visible in the health endpoint, real-model evaluation and live Sentry generation spans.

### Best Use of Sentry Agent Tracing

I instrumented tutor, quiz and OCR operations with parent transactions and child spans for retrieval, generation, blind solving, support checks and rejection. Sentry receives model/role labels, latency, Ollama-reported token counts, attempt counts and fixed outcome codes.

These live traces were inspected in Sentry's Traces and Agents views:

| Trace | What it revealed |
|---|---|
| Supported answer | 45.73 s overall: Gemma draft 24.84 s, blind Qwen solve 9.68 s, support check 10.80 s |
| Refused request | 1.66 min and three rejected drafts; the first rejection was `unsupported_quantity`, before Qwen ran |
| Public glassboard OCR | GLM-OCR call 59.07 s, 4,072 input / 87 output tokens; no image or transcription exported |

The accepted trace gives a concrete explanation for my friend's speed feedback: drafting took 24.84 seconds and the two verification calls added 20.48 seconds. The refused trace shows how retries increase the wait. It also separates deterministic source-guard rejection from model-verifier rejection.

Privacy is enforced through an **event/span metadata allowlist and a second filter at the SDK transport boundary**. Documents, images, filenames, questions, answers and free-form model text are excluded. The inspected AI span showed **“No input for this span.”** Sentry observes the pipeline; accuracy checks remain in the local application.

[Current tutor trace evidence](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/current-tutor-live.json), [OCR trace evidence](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/ocr-live.json) and [Sentry setup/privacy details](https://github.com/arywk40-hue/hacktober/blob/main/docs/SENTRY.md) are available in the repository.

<!-- Add actual exported Sentry screenshots here before publishing. Existing trace records do not replace the requested visual evidence. -->

Public demo photo: [Learning Physics](https://commons.wikimedia.org/wiki/File:Learning_Physics.jpg), Preply.com Images / preply.com, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).
