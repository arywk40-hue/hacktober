---
title: "CiteTutor: a local study tutor that verifies before it answers"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

> Unpublished draft. CiteTutor adapts pre-existing Course Companion code. The challenge FAQ excludes old projects; resolve eligibility with the organisers before presenting this adaptation as an eligible entry. Resetting history does not change when code was written. The video and exported screenshots remain pending.

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

I asked one college friend to try CiteTutor on a chapter from their own course material. They found it useful, but a little slow.

That is fair feedback. CiteTutor makes them wait while it checks an answer before showing it. Gemma drafts an explanation, code validates its citations, and Qwen independently reads the source and checks the draft. Failed drafts are withheld. After at most three attempts, the tutor either shows a cited answer or says **“Not enough evidence in this document.”** These checks reduce some errors; they do not guarantee correctness.

My friend can organise PDF notes and textbook chapters by subject, ask for an explanation or hint, and practise MCQs or short-answer questions from selected pages. Clicking a citation opens the page text; reviewed scans also show the original image. The practical aim is to make checking a study answer easy.

This is reported friend feedback, not a controlled study or measured learning improvement. Their name, chapter and notes stay private. Speed remains a usability problem to improve.

## Demo

**Video demo: [ADD YOUR PUBLIC VIDEO LINK HERE]**

**Recording and exported screenshots pending.** Replace this notice with an accessible video URL and actual captures before publishing. The [three-minute recording guide](https://github.com/arywk40-hue/hacktober/blob/main/docs/DEMO.md) is a shot list, not a finished demo.

Record one session: upload the original public mechanics fixture, ask the force question, open its citation, show an unrelated question refusing, and generate a verified practice set with its actual accepted/rejected counts. Then compare a public scan with its editable transcription and show real Sentry generation, verification and rejection spans. Label shortened waits with the recorded duration.

After setup, run `./run.sh` and open http://127.0.0.1:8000. [README setup](https://github.com/arywk40-hue/hacktober#setup) includes the model pulls.

## Code

[CiteTutor repository](https://github.com/arywk40-hue/hacktober)

The earlier Course Companion implementation predates the weekend window. The previous history is backed up; earlier revisions and subsequent adaptation remain documented in [BUILD_LOG.md](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md).

## How I Built It

FastAPI serves a small HTML/JavaScript interface. PyMuPDF extracts text per physical page. Local nomic embeddings and keyword ranking retrieve chunks stored in SQLite. There is no database server, queue or cloud inference fallback.

**Retrieve → Gemma structured draft → citation/source checks → Qwen blind reading → support and agreement check → cited answer or refusal.**

Gemma supplies source aliases, which code resolves to stored chunks and authoritative page numbers. Unknown or missing citations fail. Qwen's blind reading sees the question and evidence, without Gemma's draft or learner style. Another step checks the draft against that reading and the source. Nothing is streamed before verification. Small laptop models currently receive a concise, one-paragraph/one-chunk task.

Quiz candidates have their own checks: schema, source IDs and literal supporting quotes, independently retrieved evidence, then a blind Qwen solve without the proposed key or rationale. Unsupported or disagreeing candidates are dropped; the UI shows rejected counts. Disagreement does not establish which model was wrong.

### What the real models did

The revised evaluation on an 8 GB M1 used an original three-page mechanics PDF:

| Check | Result from this run |
|---|---|
| Supported questions answered correctly | 7 / 7 |
| Expected document/page citations | 7 / 7 |
| Unrelated questions refused | 3 / 3 |
| Quiz candidates | 1 accepted, 1 rejected |
| Returned tutor latency | Median 44.5 seconds |

The rejected MCQ disagreed with the blind solver; the accepted short answer and quote matched the fixture. This is a **small smoke check**, not general accuracy across college PDFs. Earlier runs falsely refused supported questions. A handwriting test accepted an irrelevant answer before blind tutor reading was added. These failures remain in [evaluation results](https://github.com/arywk40-hue/hacktober/blob/main/eval/RESULTS.md) and [scan observations](https://github.com/arywk40-hue/hacktober/blob/main/eval/SCAN_RESULTS.md).

### Handwriting needs review

Full-page Gemma transcription was incomplete on handwritten lecture notes; Qwen-VL stalled. Dedicated local GLM-OCR produced more useful drafts, but misread dimensions, subscripts, an array name and infinity symbols. Repeated or truncated output is labelled partial.

Scans stay outside retrieval until every scanned page is reviewed against its image. Blank reviewed pages are excluded. The verifier checks approved text, so it cannot fix an OCR error hidden in that text. This is assisted transcription with human review.

## Why Does Open Innovation Matter?

The open components do the central work: nomic retrieves, Gemma drafts, Qwen checks, and GLM-OCR reads scans. After dependencies and weights are installed, the core uses the laptop and local Ollama, with no hosted-model fallback or per-request AI API charges.

My friend's notes, questions and answers stay local. Optional Sentry tracing sends sanitized timing, token and outcome metadata; leave its DSN blank for fully local operation. Physical network-disconnection testing remains pending.

Model roles are configurable and source checks are inspectable. We can change models for different hardware without handing the study policy to a provider. Model-specific licences apply; hardware and electricity still cost money. The current trade-off is visible: private local generation and verification take time.

## My Agent Session

I used Codex as a coding assistant for the CiteTutor adaptation, implementation, testing and documentation. I directed the scope and product choices, including running models locally, checking answers before display and keeping scan transcription subject to review.

The [build log](https://github.com/arywk40-hue/hacktober/blob/main/BUILD_LOG.md) records decisions, failed experiments, actual evaluation results and verifier rejections. It is a development record, not an exported agent transcript. I have not published a DevRelay session; no session embed is claimed.

## Prize Categories

These are technology targets, conditional on resolving the adaptation's eligibility.

### Best Use of Gemma

Local `gemma3:4b` supplies both core generation tasks: structured tutor explanations and MCQ/short-answer candidates. Qwen independently verifies, nomic embeds, and GLM-OCR reads images. Gemma's role is visible in `/api/health`, the evaluation's real model calls and the live tutor trace.

### Best Use of Sentry Agent Tracing

Live traces were inspected in Sentry's Traces and Agents views:

| Actual trace | What it showed |
|---|---|
| Supported tutor request | Passed on attempt one in 45.73 s: Gemma draft 24.84 s, Qwen blind reading 9.68 s, support check 10.80 s. |
| Refused request | 1.66 min, three rejected drafts. The first rejection was `unsupported_quantity`, before Qwen was called. |
| Public glassboard image | Local GLM-OCR model call 59.07 s, 4,072 input / 87 output tokens; no image or transcription in Sentry. |

The useful finding is where time accumulates: generation dominates the accepted request, and retries make a refusal slower. Source-guard failures and verifier failures are separate stages. This explains the wait; tracing itself did not improve accuracy or speed.

The outgoing allowlist excludes documents, images, questions, answers, filenames and model input text. The inspected AI span showed **No input for this span**. Sentry observes the pipeline; it does not recognise images or verify facts. Its estimated API costs do not measure local hardware costs.

Include actual saved screenshots with this post. Verified metadata and trace IDs are in [current tutor traces](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/current-tutor-live.json) and [OCR trace](https://github.com/arywk40-hue/hacktober/blob/main/eval/traces/ocr-live.json); [Sentry setup](https://github.com/arywk40-hue/hacktober/blob/main/docs/SENTRY.md) explains reproduction and privacy. Historical slower runs remain archived.

Public photo credit: [Learning Physics](https://commons.wikimedia.org/wiki/File:Learning_Physics.jpg), Preply.com Images / preply.com, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). Private lecture notes are not published.
