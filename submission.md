---
title: "CiteTutor: local college study help with answers you can check"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

> Draft for review. This project adapts a pre-existing repository; the official FAQ excludes old projects. Do not present this as a new, eligible entry without resolving that requirement with the organisers. Do not invent a friend testimonial or claim an unrecorded demo.

## What I Built

I built CiteTutor to help a friend in college study from their own material. They can create a subject, add several PDF notes or textbook chapters, ask for an explanation or hint, and practise questions from selected pages.

The question I wanted the app to answer was: can a study helper make its explanations easy to check? Each answer segment links to a document and physical page. Unsupported drafts are rejected. The tutor refuses when it cannot verify a complete answer from the material.

## Demo

Run `./run.sh` and open http://127.0.0.1:8000. A local model server does not require publishing a friend's documents.

Demo walkthrough to record:

1. Create a Physics subject and upload `eval/sample.pdf`.
2. Ask for the force on a 2 kg body accelerating at 4 m/s²; show the result and click its citation.
3. Ask an out-of-scope question and show the explicit refusal.
4. Generate a two-question practice set over pages 1–3; show verification counts, a source answer and its supporting quote.

**Before publishing:** attach a real screenshot or recording of the final working flow. Add feedback only after the friend has actually tried it.

## Code

https://github.com/arywk40-hue/hacktober

This repo starts with a current snapshot of the CiteTutor adaptation. Its earlier Course Companion code predates the weekend window. The previous commit history is backed up separately; the actual development steps, earlier commit IDs and failures remain recorded in `BUILD_LOG.md`.

## How I Built It

FastAPI serves a minimal HTML/JavaScript interface. PyMuPDF extracts page text. SQLite stores documents, chunks, embeddings and local verifier audits. Keyword ranking and dense cosine search are fused to retrieve source evidence.

Gemma creates a structured draft. Short source aliases map exactly to stored chunk IDs. Unknown citations fail before verification. Qwen checks the concise answer against its cited evidence and requested question. The small generator is constrained to one paragraph and one supporting chunk to avoid adding unrequested facts. The app tries at most three drafts and displays only a complete pass.

Quiz generation is a separate pipeline: validate the question schema and literal quotes, independently retrieve relevant text, then ask Qwen to solve the question without its proposed answer or rationale. A separate step checks the key against the blind answer and source evidence. Rejected candidates never appear in the practice set; their counts and reasons do.

The first live test was poor: a preliminary evidence classifier refused every supported question. We retained that baseline, removed the false-negative gate, and made post-draft verification the acceptance step. A smaller verifier also confused claims in a batch check. Gemma 1B later omitted numerical values and struggled with quiz schemas. The final defaults are Gemma 4B and Qwen 3B, run serially with immediate unloading on the 8 GB laptop. Type-specific question schemas help generation; blind verification still decides acceptance.

The final local evaluation answered four of seven supported questions correctly, with correct-page citations for all four returned answers. All three out-of-scope questions were refused. Three supported questions were also falsely refused, so this is a conservative prototype with a real usefulness limitation. The MCQ and short-answer quiz candidates both passed independent verification and manual source review, with zero rejected in that final set. Earlier schema failures and rejected candidates remain recorded in the build log and reports.

On the 8 GB M1 laptop, returned tutor answers had a median latency of about 52 seconds. The complete ten-question run and quiz took about 14 minutes. See `eval/RESULTS.md` and the full report. The fixture is small; its results do not establish accuracy across college material. Verification can miss mistakes, so source inspection remains part of the study flow.

## Why Does Open Innovation Matter?

The open components perform the central work: local embeddings find relevant material, Gemma produces explanations, and another model checks them. After setup, documents and questions stay on the laptop and inference needs no internet or paid API tokens. The UI has no external assets. Optional Sentry tracing is off by default; when enabled, sanitized timing/token/count metadata leaves the laptop while document and model content stays local.

The models can be swapped and the verification policy can be inspected and changed. That makes the tool easier to adapt to a friend's hardware and study needs. Hardware and electricity still have costs; each model's licence applies.

## Prize Categories

**Best Use of Gemma** is the technology category target, conditional on the entry meeting the challenge's eligibility requirements. The [weekend category rules](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) explicitly include local Gemma inference.

CiteTutor runs `gemma3:4b` through local Ollama for both central generation tasks: structured explanations grounded in retrieved PDF chunks, and MCQ/short-answer quiz candidates with source IDs and supporting quotes. Gemma supplies the answer and question drafts; Qwen, from a different model family, independently decides whether they pass. That separation lets us inspect and reject unreliable output while keeping document processing on the laptop.

Evidence of the integration is in `study/tutor.py`, `study/assessment.py`, the model roles returned by `/api/health`, and the actual Gemma calls recorded in `eval/reports/local.json`. The demo should show the installed model tag, one cited answer, and a quiz's verified count and source quote. The measured false refusals and latency remain disclosed in the evaluation section above.

**Sentry Agent Tracing — implemented; live demonstration pending.** Manual AI spans expose the tutor and quiz pipelines, local model latency/token usage, retry/refusal outcomes, and fixed rejection codes. The SDK's automatic integrations are disabled; transactions and envelopes pass an allowlist that excludes all note/model content and attachments. Tests cover three rejected tutor drafts, quiz key disagreement, privacy and failed network transport. The sample trace command uses real local models and can also capture SDK envelopes locally without sending telemetry. See `docs/SENTRY.md` for setup.

Before claiming the Sentry partner category, configure a real project and add a verified trace screenshot/link and actual observations here. No live ingestion is claimed yet. Entire and ElevenLabs are not integrated. Prize selection depends on a valid entry and judging; these integrations do not guarantee an award.

The real-model local trace preview (`eval/traces/local-preview.json`) caught three `unsupported_quantity` drafts before refusal: a requested result was absent from the cited source. The guard rejected them before Qwen was called. The span metadata shows the cost of retrying on this laptop: that refusal took 465 seconds, compared with 141 seconds for the supported answer on its first attempt. The two-question quiz took 299 seconds, accepted both candidates, and shows separate blind-solve and support-verdict calls. This is local SDK instrumentation evidence, not a live Sentry dashboard capture or a benchmark of tracing overhead.
