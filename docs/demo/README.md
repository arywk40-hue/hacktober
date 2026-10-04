# Actual submission screenshots

These PNGs were captured from the real Safari app and Sentry interfaces on October 5, 2026. They are unedited screenshots, not generated mockups or reconstructed traces. The app screenshots show fresh local requests against the public authored mechanics fixture in an isolated demo library, with Sentry disabled. The underlying Sentry requests completed on October 4 using that fixture or the credited public glassboard image. Private course notes were not used or changed.

| Image | Evidence | Suggested placement |
|---|---|---|
| [App library](app-library.png) | Uploaded three-page public sample, ready with three source chunks | Optional opening image |
| [Verified answer](app-verified-answer.png) | Actual 8 N answer and page 1 citation | Demo, primary app screenshot |
| [Source page](app-source-page.png) | Opened citation showing original page 1 worked example | Page provenance |
| [Verified quiz](app-verified-quiz.png) | One accepted, one rejected for blind-key disagreement; 9 J answer, quote and page 2 | Quiz acceptance gate |
| [Gemma/privacy](sentry-gemma-privacy.png) | Local Gemma model, token count, 24.84 s draft, two following Qwen calls, absent input content | Sentry category, primary screenshot |
| [Tutor waterfall](sentry-tutor-waterfall.png) | Actual 45.73 s request with retrieval, embeddings and three chat calls | Optional expanded tracing evidence |
| [Refusal waterfall](sentry-refusal-waterfall.png) | 1.66 min request, three drafts and three rejection spans | Sentry category, rejection evidence |
| [OCR/privacy](sentry-ocr-privacy.png) | Local GLM-OCR, 59.07 s, token counts and absent input content | Sentry category, optional OCR evidence |

Trace IDs and inspected values are in [current tutor records](../../eval/traces/current-tutor-live.json) and [OCR records](../../eval/traces/ocr-live.json). The account-gated Sentry pages are not required to view these PNGs.

The fresh app results are preserved in [capture-run.json](capture-run.json), exported from the isolated demo library. This is a one-answer/two-candidate rehearsal, not another ten-question evaluation. UTC completion timestamps fall on October 4; the local capture date is October 5 in Asia/Kolkata.

The first rejection was `unsupported_quantity`; its source-guard failures precede Qwen. The waterfall does not show that attribute itself. Do not call this a Qwen-verifier rejection.

The plot in docs/assets is a separate explanatory figure. These files are the actual dashboard screenshots. The finished video remains pending.
