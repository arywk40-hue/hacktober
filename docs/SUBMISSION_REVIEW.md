# CiteTutor submission review — October 4, 2026

## Coverage and method

Screened **199 unique tagged posts** returned by two public DEV API pages during this review; page 3 returned no entries. Read selected introductions, reported testing and handover passages across those posts, and compared **26 relevant write-ups closely**, including eight older posts linked from the tag page's related list. This is a feed snapshot, not a guarantee that every published submission is indexed or that future entries are included. Some tagged posts are duplicates, work in progress, or use another challenge template.

All 199 article bodies were accessible: 180 through the article API, 19 through public HTML after API failures. Downloading a body is not the same as reading it in depth. [SUBMISSION_COVERAGE.csv](SUBMISSION_COVERAGE.csv) records the distinction. The eight additional detailed comparisons appear in the table below.

This assesses the authors' public write-ups and CiteTutor's existing code/results. Competitor repositories, videos, user testimonials and dashboards were not independently tested or authenticated. No competitor code or article bodies were copied into this repository. Reactions are not used to score engineering or predict a winner.

The [official rubric](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01) puts writing first, followed by theme relevance, creativity, technical execution and optional partner use.

## Candid rating

These are subjective editorial scores, not official weights, ranks or prize forecasts.

| Area | Current assessment | Reason |
|---|---|---|
| Open AI at the core | 9 / 10 | All four model roles run locally; source retrieval and verification depend on them. |
| Technical execution | 8 / 10 | Separate blind verification, citation/quote checks, retry limits, real evaluation and content-free tracing. |
| Distinctiveness | 6.5 / 10 | Local PDF chat, citations and quizzes are common; independent model-family verification is the more specific angle. |
| Friend/theme story | 7 / 10 | Real course-chapter feedback is now reported; the particular study obstacle and changed study behaviour remain unspecified. |
| Demo/presentation | 5 / 10 | A recording guide and live trace records exist, but there is no finished public video or saved screenshot set. |
| Overall submission readiness | About 7 / 10 | Evidence needs to be visible in the post; the reused-code eligibility issue is a separate unresolved gate. |

The ten-question mechanics result is useful evidence of one run, not a general reliability estimate. CiteTutor's 44.5-second median also matters to a student. Source checks can miss mistakes; a correct page anchor does not by itself establish support.

## Closest comparisons and useful lessons

Summaries describe published claims, not independently verified outcomes.

| Entry | What its write-up does well | Implication for CiteTutor |
|---|---|---|
| [hjkl](https://dev.to/sizzlebop/i-built-my-husband-a-vim-trainer-with-a-gemma-coach-that-runs-in-the-browser-5fmh) | Specific learning habits, a live browser demo and generated drills validated in a real Vim engine. | Explain what validation actually runs and show the learner using it. |
| [Suniye](https://dev.to/himanshu_748/suniye-let-my-parents-hear-the-message-themselves-41bh) | Separates tested paths from pending family checks; Sentry distinguishes model loading from generation. | Show a trace finding and its limits, alongside the user flow. |
| [Nightjar](https://dev.to/zkasuran/i-built-my-brother-a-bedtime-storyteller-that-runs-on-his-laptop-1lpf) | Explorable demo, labelled synthetic data and model failures that escaped checks. | Retain failures and distinguish fixture results from actual learner outcomes. |
| [Groundtruth](https://dev.to/jarviswick/groundtruth-a-revision-partner-for-my-cousin-that-only-answers-from-his-notes-1nfk) | Source quotes, conservative verdict checks and reported latency measurements. | Grounding alone is not unique; demonstrate blind verification and rejected questions. |
| [Darvin](https://dev.to/rishavj90/darvin-a-rag-study-buddy-i-built-for-my-friend-drowning-in-pdfs-2l2j) | Same PDF-study problem, page citations and a linked video; generation uses hosted Groq. | CiteTutor's fully local generator and verifier are a meaningful architectural difference. |
| [StudyBuddy quiz generator](https://dev.to/shadow16ua/studybuddy-ai-taming-gemma-2b-to-build-a-local-quiz-generator-for-a-friend-4mpo) | Narrow local Gemma use and a concrete JSON-generation problem. | Explain why schema validity is only the first check; demonstrate source/key verification. |
| [NEVERTWICE](https://dev.to/offxhashir/i-built-my-best-friend-a-mistake-engine-for-the-nust-entry-test-434d) | Specific exam, video/live demo and changes attributed to a friend's test. | Report actual feedback and any resulting improvement. Do not add adaptive learning for this weekend. |
| [TenMin](https://dev.to/shreyach52/tenmin-study-cards-for-a-friend-who-cant-sit-through-100-slides-4b57) | Specific study behaviour, real feedback, source slides and acknowledged processing delays. | Keep progress visible while preserving the policy against showing unverified output. |
| [StudyLens NCERT](https://dev.to/prachi_b_5b1b053e2cae28e1/studylens-ncert-buddy-2k1f) | Exam-specific workflow and concrete latency debugging. | Prefer one understandable study session over a tour of every feature. |
| [StudyLens for a sister](https://dev.to/shashwatsinha03/studylens-for-my-tensed-sister-juggling-with-her-academics-5fd0) | Local PDF Q&A, quizzes and a described friend test. | A longer feature list would not distinguish CiteTutor. |
| [PROOF](https://dev.to/farhan_bangash_d8021d8280/i-built-proof-for-a-friend-who-was-studying-but-not-actually-understanding-280g) | An Operating Systems misconception makes its learning goal concrete. | Describe one real question and how checking its source helped. |
| [Nkuzi](https://dev.to/bukeeastrey/nkuzi-an-offline-study-partner-that-remembers-the-slides-so-my-friends-dont-have-to-3007) | Real study context, source-checked corrections, a friend's trial and hardware limits. | Treat quote checks and verification as engineering choices, not proof of infallibility. |
| [Thai meter-sheet reader](https://dev.to/ninefyi/i-taught-a-local-gemma-to-read-a-rental-meter-sheet-1led) | Separates a fabricated demo from real handwriting results and discloses an unflagged error. | Show scan review and a genuine recognition mistake; avoid broad handwriting accuracy claims. |
| [Thaththa's Memory Box](https://dev.to/jayanagunaweera01/thaththas-memory-box-a-personal-ai-agent-that-isnt-allowed-to-make-things-up-82d) | One keepsake and family-provided corrections explain provenance. Some placeholders remain. | Show which text is reviewed evidence and which output is only a model draft. |
| [Gym Log Buddy](https://dev.to/shubham_nayak_/i-built-a-local-ai-gym-log-for-a-friend-who-always-forgot-his-weights-5b14) | Reports held-out model checks and discovers test leakage and a UI crash. | Test another chapter after freezing prompts; keep unit tests separate from model accuracy. |
| [Local Computer](https://dev.to/mascarock/a-private-budget-chat-for-paola-checked-by-local-gemma-iec) | A short video, actual screenshots and a checked model sentence. | A local-only project can still have an accessible video demo. |
| [Cek Dulu](https://dev.to/derbyps/cek-dulu-i-built-a-scam-checker-for-my-parents-and-they-told-me-they-dont-need-me-anymore-17cc) | Specific recipients, reported onboarding trouble and false-alarm analysis. | Include the friend's criticism; usefulness is more persuasive than praise alone. |
| [EchoNote AI](https://dev.to/codebysumit/echonote-ai-i-built-an-offline-lecture-notes-app-for-my-friend-8hn) | A named student's lecture workflow and local model roles. | Connect the open stack to the friend's actual study routine. |
| [StudyBuddy / Llama](https://dev.to/papa_moussasanogo_1c3d01/i-built-studybuddy-ai-an-open-source-study-assistant-for-students-using-ollama-and-llama-3-42l6) | Explains basic local study tools; PDF upload is listed as future work. | CiteTutor already has deeper PDF evidence handling; show it clearly. |
| [Tripwire](https://dev.to/sansk_ya/tripwire-a-guardrails-layer-for-llm-apps-built-for-a-friend-4i86) | Separates tuned, held-out and external checks and discloses judge failures. | Keep acceptance checks and measured correctness distinct. |
| [OSS Buddy](https://dev.to/ibrahimiqbal/oss-buddy-a-local-gemma-that-picks-weekend-sized-issues-so-my-cousin-can-finally-land-his-first-pr-277f) | One recipient's recurring obstacle and a small intelligible pipeline. | Lead with the problem and outcome before listing frameworks. |
| [Soft With Meaning](https://dev.to/xiao_ilands/soft-with-meaning-an-offline-companion-for-vivaldis-four-seasons-built-for-one-friend-5k0) | Narrow personal purpose and an openly removed wrong-answer model. | Keep the scope small and show why an unreliable component changed. |
| [PrepPal](https://dev.to/scar3max/preppal-how-i-built-an-adaptive-open-source-ai-mock-interviewer-for-my-anxious-batchmate-30n7) | A specific interview problem and reported feedback; it combines local and cloud inference. | State precisely that CiteTutor's generation and verification both remain local. |
| [BiteSize](https://dev.to/yash_raghubanshi_6896e89b/bitesize-the-open-source-anti-overwhelm-agent-i-built-for-my-best-friend-mayank-14dc) | A recipient's concrete obstacle drives the single-step interaction. | Describe a practical study obstacle without inventing details or copying the story. |
| [ChurnScope](https://dev.to/talha2007/churnscope-saving-my-friends-startup-from-silent-user-drop-off-with-open-ai-dom-intelligence-4o2c) | Detailed product and outcome claims, which this review did not independently validate. | Prefer a small number of directly inspectable CiteTutor results. |
| [BugReplay](https://dev.to/jhashivam0022/bugreplay-helping-developers-learn-from-bugs-their-team-has-already-solved-27mn) | Clear knowledge-reuse idea; its demo is still described as forthcoming. | A planned demo remains a readiness gap, including for CiteTutor. |

## Changes made in this review

- Rewrote [submission.md](../submission.md) around verification before display.
- Added the author's newly reported friend trial: their own course chapter worked well, but the app felt slow. No direct quote, course name, measured learning gain or exact question was invented.
- Condensed repeated historical Sentry runs into a current three-row trace table and linked the archived evidence.
- Clarified Gemma/Qwen/nomic/GLM-OCR responsibilities and the difference between source guards, verification and tracing.
- Kept the small-fixture limitation, mandatory scan review, pending media and earlier-code provenance visible.

No runtime behaviour, models, study data or competitor code was changed. Documentation needs whitespace/link/claim checks; another model benchmark is not required just to edit the write-up.

## Priorities before publication

1. **Resolve eligibility.** The existing code predates the window. A new remote or rewritten history does not make that code new. Ask the organisers how the old-project prohibition applies alongside their allowance for significant credited reuse. No organiser message was sent.
2. **Finish the three-minute video.** Show upload → answer → citation → refusal → verified quiz, with actual results. Export real screenshots: the Gemma/Qwen waterfall, three rejected attempts, and OCR metadata with no input captured. Account-gated trace links alone do not let every judge inspect the evidence.
3. **Check one different chapter with frozen prompts.** Record supported-answer failures, incorrect answers, citation support and refusals. Current 7/7 and 3/3 belong to the authored fixture; the friend's general feedback is not a scored benchmark.
4. **Make the source selection obvious in the demo.** Earlier UI inspection showed a different PDF selected for a matrix question. The saved handwritten lecture had only 117 characters on page 1 and blank pages 2–5. Use Review again and check all readable pages before relying on it. Do not auto-approve OCR for the recording.
5. **Explain the wait honestly.** Show progress and actual elapsed times. The current accepted trace spends 24.84 seconds drafting and about 20.48 seconds in two verifier calls. On this 8 GB laptop, keeping several models resident needs testing; don't sacrifice independent checks or claim a speed improvement without measurements.

Avoid new voice, dashboards, adaptive learning, extra hosting or additional partner integrations for this submission. Gemma and Sentry already have meaningful roles.

Suggested organiser question, for the author to send:
> My CiteTutor repository adapts earlier Course Companion code, with local model, verification, scan-review and tracing work added during this weekend. I will disclose the earlier code and new changes. Does this fall under permitted significant credited reuse, or does the old-project rule make the adaptation ineligible?

The official deadline is **October 5 at 12:29 PM IST**. Do not publish an eligible-entry claim unless that issue is resolved.
