# Local evaluation

Run after installing the default Ollama weights and Python development dependencies:

The completed run and its limitations are summarised in [RESULTS.md](RESULTS.md).

```sh
uv run --offline python -m scripts.evaluate
```

The script authors `sample.pdf` if absent, creates an isolated temporary SQLite workspace, indexes that PDF with real local embeddings, and runs the production HTTP handlers against real Ollama models. No test double, cloud judge, RAGAS download or running web app is required. User study data is not modified.

`questions.json` contains ten gold cases: seven supported questions with expected pages/answer patterns, and three questions outside the PDF. The script then generates two mixed quiz candidates and applies the real blind-solve/support pipeline.

## Metrics

| Metric | Definition |
|---|---|
| In-scope answer correctness | Gold-pattern matches / answered in-scope cases. Null if all were refused. |
| In-scope success | Gold-pattern matches / all seven in-scope cases. Refusals count as failures. |
| Citation accuracy | Anchors pointing to the correct fixture document and an expected gold page / all returned anchors. The page endpoint must exist. |
| Citation coverage | Answered in-scope cases with citations / answered in-scope cases. |
| Out-of-scope refusal rate | Refused out-of-scope cases / all three out-of-scope cases. |
| In-scope refusal rate | Refused in-scope cases / all seven in-scope cases. |
| Quiz acceptance/rejection | Actual schema, quotes, independent retrieval, blind solve and support outcomes. |

Pattern scoring can miss valid paraphrases or accept incorrect extra wording. Inspect every response against the PDF; these are smoke metrics on an authored fixture. Citation-page accuracy does not establish that every sentence is semantically supported.

The full report contains responses, citations, quiz keys/quotes, rejection reasons, model identities, local token/latency measurements, Git revision and dirty-worktree status at the start of the run. New reports also include SHA-256 hashes of the PDF and gold file. Its page URLs reference the temporary test database, which is deleted after the run; inspect the committed PDF for subsequent review. During new runs, a `.partial.json` checkpoint preserves completed cases if execution is interrupted; it is removed on successful completion.

Reports:

- `reports/baseline.json`: failed 4B/3B run with the preliminary evidence classifier; retained honestly.
- `reports/lighter-first.partial.json`: interrupted early lighter-model run, retained for debugging. This is not a ten-question result.
- `reports/concise-first.json`: complete 1B/3B run; five of seven supported answers correct, two incomplete numerical answers, and both quiz candidates rejected for schema failures.
- `reports/larger-format.partial.json`: stopped 4B/3B run after five cases; exposed an exponent bypassing the number check and a wrong-page numerical citation. Not a full evaluation.
- `reports/local.json`: latest completed full evaluation; review its model tags and timestamp.

For another PDF, supply a matching ten-case gold file:

```sh
uv run --offline python -m scripts.evaluate --pdf path/to/chapter.pdf --questions path/to/gold.json --output eval/reports/custom.json
```

Model downloads and dependency setup need internet; application inference uses loopback only. The historical adaptive-learning simulation is archived under `docs/archive/previous-adaptive-simulation.json` and is not a CiteTutor result.
