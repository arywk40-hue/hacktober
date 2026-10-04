# Submission figures

These are diagrams and replotted measurements, not product screenshots or Sentry dashboard captures. Both PNGs are embedded in `submission.md`; they can also be uploaded through DEV's image uploader. Keep the captions and descriptive alt text. Use the full-resolution images so readers can zoom into labels.

| Figure | Upload-ready PNG | Editable SVG | Placement |
|---|---|---|---|
| Implemented architecture | [Architecture PNG](assets/citetutor-architecture.png) | [Architecture SVG](assets/citetutor-architecture.svg) | How I Built It, after model roles |
| Recorded results and latency | [Results PNG](assets/citetutor-results.png) | [Results SVG](assets/citetutor-results.svg) | How I Built It, after the evaluation table |

## Architecture caption

Architecture of the implemented application. Drafts pass citation and source-support checks before display; optional telemetry crosses a separate metadata-only boundary.

The diagram separates tutor and quiz acceptance gates. Scan transcription requires human review before indexing. Gemma generates; a different Qwen family performs blind solving and source-support checks. Sentry receives operational metadata, not source material. Model judgments can still be wrong.

## Results caption

Two recorded runs on the same small fixture, plus a separate live Sentry timing breakdown. Prompts and runtime changed, so this is not a controlled ablation or a comparison against other projects. The trace is replotted from recorded measurements; actual dashboard screenshots belong in the Sentry section.

The renderer reads [the earlier report](../eval/reports/local.json), [the revised report](../eval/reports/blind-reading.json) and [the inspected live trace](../eval/traces/current-tutor-live.json). It checks identical PDF and question hashes before comparing runs. Counts come from the question records; answer latency comes from returned supported questions. The trace's remaining time is approximate because the root and support duration were recorded from rounded dashboard values.

## What makes the work distinctive

For the post or narration:

> CiteTutor's central design choice is verification before display. Citation provenance is resolved by code, while a different model family first answers from the evidence without seeing the draft or proposed quiz key. Failed drafts are withheld, rejected quiz candidates are counted, and scans stay outside retrieval until reviewed. The evaluation and trace figures show both the recorded outcomes and the time these checks take.

This demonstrates the implemented behavior and development progress. We have not run a matched benchmark against other entrants, a plain-RAG ablation, or a general college-material evaluation. Do not label the figures “better than other submissions,” “zero hallucinations,” or “100% accurate.”

## Re-render

The app does not depend on Matplotlib. Figure generation is a separate presentation task:

```sh
uv run --no-project --with matplotlib==3.10.7 python scripts/render_submission_figures.py
```

This may need a one-time package download. If Matplotlib is already installed, `python3 scripts/render_submission_figures.py` also works. Generation reads existing local reports; it does not call Ollama, send Sentry events or create a new benchmark.

Actual app and Sentry dashboard captures are now saved in the [screenshot gallery](demo/README.md) and embedded in the draft. The finished video and earlier-code eligibility clarification remain pending.
