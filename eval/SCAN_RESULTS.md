# Local scan test observations

Tested October 4, 2026 on an 8 GB Apple M1 with Ollama 0.35.1. All inference used installed local weights. The college PDF and complete model outputs are private, under ignored `data/handwriting-check/`; no source pages are published here.

## Five-page handwritten lecture PDF

The supplied PDF has five image-only pages and zero selectable characters. Its topic is matrix-chain multiplication. Original page images were visually inspected. These observations are not a character/word accuracy benchmark.

| Model experiment | Observed result |
|---|---|
| Gemma 3 4B | Page 1 returned only three labels in 116.92 s. Page 2 hit the output limit after 562.66 s and was rejected. |
| Qwen2.5-VL 3B | Full-page attempt stalled on this laptop; cancelled without a completed transcription. |
| GLM-OCR q8 | Native `Text Recognition:` generation produced useful drafts, but repeated output. End-of-text stops alone did not fix it. A Markdown-fence stop helped, with omissions requiring review. |

| Page | GLM-OCR draft observation | Seconds |
|---|---|---:|
| 1 | Three matrix dimensions match. A highlighted dimension annotation loses a trailing zero. | 24.52 |
| 2 | Partial/repeated pseudocode; subscript and array-name errors. Explicit incomplete warning. | 99.99 |
| 3 | Recurrence recognized, but one highlighted subproblem omitted. | 29.11 |
| 4 | Cell-purpose comment recognized; array name and infinity symbols misread. | 28.23 |
| 5 | Mostly blank/cropped page returned no text. | 26.30 |

The bounded OCR adapter retains truncated GLM text as a clearly marked partial draft, cuts exact repeated blocks, and never automatically indexes it. A Markdown-fence stop can omit code. Review is required for completeness as well as correctness. Leave unreadable material blank to exclude it; do not infer cropped content. The verifier sees approved text, not the image.

## Study checks after transcription correction

For an isolated temporary library, Codex visually corrected readable portions of pages 1–4 and excluded page 5. This was a test preparation step, not user approval of the production library.

The first test returned a wrong accepted answer about the array: initialization instead of the requested cell meaning. Its passing verifier verdict is retained privately. This led to the tutor's independent blind-reading step before draft agreement/support checking.

| Revised tutor request | Actual result | Seconds |
|---|---|---:|
| What does the array cell store? | Minimum operations for the matrix subsequence, cited page 4. | 34.66 |
| What are the three matrix dimensions? | All three visible dimensions, cited page 1. | 43.26 |
| Unrelated capital-of-France question | `Not enough evidence in this document` | 16.97 |

Two mixed quiz candidates passed literal source checks, independent blind solving and support verification: **2 accepted, 0 rejected**. Their keys and page-4 quotes were visually compared with the corrected source. Earlier failures are retained. This is a three-question smoke check, not the ten-question benchmark or a broad reliability claim.

The production library was separately marked ready with only page 1 included while testing was underway; this test did not perform that approval. **Review again** lets the user revisit the other pages while keeping the original PDF. Reopening temporarily removes the derived index until reapproval.

## Public glassboard photo

Also tested [Learning Physics](https://commons.wikimedia.org/wiki/File:Learning_Physics.jpg), by **Preply.com Images / preply.com**, licensed [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/). This was an image-to-text test, not a second PDF-ingestion test. GLM-OCR returned the following four visually matching items in **48.15 s** (4,072 input / 87 output tokens):

```text
E=mc²
PHYSICS
F=ma
PE=m×g×h
```

The draft was not indexed. Pendulum, field-line and graph interpretation were not tested; neither correctness on four items nor absence of a partial-output warning establishes general whiteboard recognition accuracy.

## Reproduce locally

```sh
ollama pull glm-ocr:q8_0
uv run --offline python -m scripts.check_scans /path/to/notes.pdf
./run.sh
```

The script saves private drafts in ignored `data/scan-check.json` and performs no approval or indexing. In the UI, use **Review scans** (or **Review again**), read/correct each page against its image, check every page, then approve the document. Run contract checks with `uv run --offline python -m pytest -q`.
