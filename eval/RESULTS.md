# Measured local results

## Revised pipeline: October 4, 17:23 IST

Completed on an 8 GB Apple M1 with Ollama 0.35.1 and installed Gemma 3 4B, Qwen 2.5 3B and nomic-embed-text. The clean starting revision was `e9b43e4`. Sentry was disabled for this isolated temporary-library run. Full responses, hashes, model identities and call statistics are in [reports/blind-reading.json](reports/blind-reading.json).

| Check | Result |
|---|---|
| Supported questions answered correctly | **7 / 7** |
| Correctness among returned supported answers | 7 / 7 |
| Citation anchors on the expected document/page | 7 / 7 |
| Returned answers with citations | 7 / 7 |
| Out-of-scope questions refused | **3 / 3** |
| False refusals on supported questions | 0 / 7 |
| Mixed quiz candidates | **1 accepted, 1 rejected** |

All seven answers were compared with the extracted fixture pages as well as the gold patterns. They state the first and third laws, 8 N force, 9 J kinetic energy, 6 kg m/s momentum, 30 J work and 5 W power with the expected page anchors. One otherwise correct answer retains a raw `C1` alias in its prose; the authoritative page citation is also present. The three unrelated questions returned the exact refusal.

The accepted short-answer quiz asks for the kinetic energy of a 2 kg body moving at 3 m/s; key **9 J**, cited page 2. Its quote matches the page, and its rationale/key agree with the document's formula and worked example. The MCQ candidate was dropped because **“Blind solver disagreed with the answer key.”** This records the actual gate outcome; disagreement alone does not establish which model was wrong. The rejected item was not displayed.

Total time was **478.99 seconds** including indexing and quiz verification. Returned tutor answers took 34.3–57.6 seconds, median **44.5 seconds**. Ollama reported **22,677 input / 2,009 output tokens** across 29 chat calls, excluding embeddings. These are local measurements, not API bills.

This is a ten-case smoke check on a three-page authored fixture, not measured reliability on college PDFs or handwriting. Gold patterns can miss errors; citation accuracy checks document/page anchors. The runtime and prompts changed since the historical run, and generation is probabilistic: the improvement cannot be attributed to blind reading alone. Earlier wrong answers and refusals are retained below and in [scan observations](SCAN_RESULTS.md).

Reproduce without sending telemetry:

```sh
CITETUTOR_SENTRY_DSN= uv run --offline python -m scripts.evaluate --output eval/reports/new-run.json
```

## Historical pipeline: October 4, 13:48 IST

This run predates tutor blind reading and scan support. It remains a historical result, not a measurement of the revised pipeline.

Completed October 4, 2026 at 13:48 IST, on an 8 GB Apple M1. Production handlers used installed Gemma 3 4B, Qwen 2.5 3B and nomic-embed-text. The code revision was `90bb37e`; the worktree was clean when the run started. Full responses, model metadata, fixture hashes, timings and counts are in [reports/local.json](reports/local.json).

The published branch was later reset to a current snapshot at the author's request. Evaluation revision IDs refer to the separately backed-up development history; the reports retain their original measurements and metadata.

| Check | Result |
|---|---|
| Supported questions answered correctly | **4 / 7 (57.1%)** |
| Correctness among returned supported answers | 4 / 4 |
| Citation anchors on the expected document/page | 4 / 4 |
| Returned answers with citations | 4 / 4 |
| Out-of-scope questions refused | 3 / 3 |
| False refusals on supported questions | **3 / 7 (42.9%)** |
| Mixed quiz candidates | 2 accepted, 0 rejected |

The tutor correctly answered Newton's first law, the 8 N force example, the 6 kg m/s momentum example and the 30 J work example. It falsely refused Newton's third law, the 9 J kinetic-energy example and the 5 W power example. Those facts are present in the PDF. The third-law question exhausted three drafts; the kinetic-energy and power requests were declined by the generator on the first attempt.

The accepted MCQ asks about third-law interaction forces, with key C: equal magnitude and opposite direction, supported on page 1. The accepted short-answer question asks for the kinetic energy of a 2 kg body at 3 m/s, with key 9 J and supporting text on page 2. Both passed literal quote validation, independent retrieval, blind Qwen solving and a separate support check. Manual review against the fixture confirmed both keys and source quotes. This does not establish reliability on other material.

The run took **857.9 seconds** including indexing, ten tutor requests and the quiz. Returned tutor answers took 48.2–91.6 seconds, with a median of 52.0 seconds. The longest refused request took 180.1 seconds. Ollama reported 23,100 input tokens and 1,673 output tokens across 27 generation/verification calls; embedding token counts are not included.

Gold-pattern correctness is a heuristic. The four returned answers and two quiz items were also manually compared with the authored PDF. Citation accuracy measures expected page anchors; it is not a general proof of factual support. This tiny fixture is a smoke evaluation, not an across-subject benchmark. False refusals and slow laptop inference remain material limitations.

Earlier failures are retained in the other reports rather than replaced by this result. The initial classifier refused every supported question; later runs exposed incomplete numerical answers and a wrong-page citation. The current numerical-source guard improves conservative acceptance, at the cost of refusing calculations whose worked result is absent from the cited source.

Reproduce after setup:

```sh
uv run --offline python -m scripts.evaluate
```

Local generation is probabilistic; future results may differ. Runtime calls are restricted to installed local weights and loopback HTTP. Physical network disconnection has not been tested.
