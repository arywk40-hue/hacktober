# Measured local results

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
