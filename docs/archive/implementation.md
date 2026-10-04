# Implementation — one complete product in 15 days

The deliverable is the full multimodal study companion described in `problem-statement.md`. There is no separate PDF-only product, reduced-scope submission or second delivery. Work is integrated continuously into the same app. Hardware capacity comes from the available team machines; the laptop running the editor is not the deployment limit.

## Scope protected through release

- Video, PDF and PPTX upload and ingestion, including diagrams and figures.
- Topics, concepts, evidence-backed prerequisites and exact source locations.
- Grounded tutoring, clear refusals, page/bbox and timestamp citations.
- Scoped MCQ, short-answer and numerical questions; mock exams; verification and repetition control.
- Cited feedback, weak-topic/misconception reports, diagnostics and mastery tracking after quizzes and graded conversation.
- Library, tutor, source viewer, assessment runner and dashboard in one web application.
- RAGAS evaluation on a human-checked test set, multi-session simulated students, setup documentation and demo video.

Cross-modal image matching, audio tutoring, revision-material generation and a study planner remain optional enhancements from the original challenge. Required diagram understanding and assessment reports are never treated as optional.

## 15-day delivery schedule

Days are working days from project kickoff; calendar dates depend on the actual submission deadline. Workstreams can be assigned across the team, but all integrate into this one release.

| Day | Work | Acceptance evidence |
|---|---|---|
| 1 | Agree course corpus, model tags/endpoints and machine allocation; bring up API, web app, Postgres, Redis and worker | All four model roles respond; schema validation and application tests pass |
| 2 | PDF extraction, scans and page vision; source storage and queue recovery | Born-digital and scanned fixtures preserve readable content and correct bboxes |
| 3 | PPTX rendering/notes and video ASR/frames; benchmark GPU/CPU placement | Slide numbers and sampled video seeks match source content |
| 4 | Topic/concept resolution, prerequisite evidence and cycle checks; normalized DB migrations/vector indexes | Every unit tagged or flagged; reviewers inspect concepts and edges |
| 5 | Hybrid retrieval, reranking and source viewer across all three modalities | Citation links open correct page/slide/time; figure queries retrieve relevant evidence |
| 6 | Sufficiency gate, claim verification, refusal cases and conversational context | Dev-set refusal and support metrics recorded; unverified claims never emitted |
| 7 | Question generation for all three types; blind solving, numeric calculation and novelty | Bank contains approved questions per required type; keys stay server-side |
| 8 | Adaptive selection, fixed mock papers, cold-start diagnostic and reports | Complete assessment updates state once; repeat submissions do not duplicate evidence |
| 9 | BKT/decay calibration, misconception resolution, teach-back grading; authentication/access boundaries | Graded chat updates state; ordinary questions do not; isolation tests pass |
| 10 | Frontend integration, session recovery, source/error/loading states and accessibility | Full upload → tutor → assessment → report → dashboard journey verified in browser |
| 11 | Human-check gold QA/off-material set and question audit; local RAGAS pipeline | Framework metrics reproduce from saved configuration and source IDs |
| 12 | Multi-session simulator, ablations, confidence intervals and profiling | Report both positive and negative results; same budgets and pools across policies |
| 13 | Deployment hardening, queue restart/timeout recovery, clean-machine installation | Fresh deployment and demo course run without manual DB repairs |
| 14 | Feature freeze; final regression, docs and recorded demo | All required workflows shown; limitations agree with measured results |
| 15 | Fix release blockers; submission package and final verification | Public repo/setup, 3–10 minute video, Devpost description and team details ready |

## Code now in the repository

```text
study/
  config.py       model/server, storage and queue configuration
  schemas.py      validated locators, evidence and assessment contracts
  db.py           Postgres/SQLite persistence and transactional records
  models.py       schema-constrained Ollama clients, role-specific endpoints
  ingest.py       PDF/PPTX/video ingestion and resumable extraction checkpoint
  graph.py        verified prerequisite links and cycle prevention
  retrieval.py    lexical/dense ranking and reciprocal-rank fusion
  tutor.py        grounded replies and graded teach-back evidence
  assessment.py   question verification, selection, grading and reports
  learner.py      BKT, forgetting and shared selection score
  jobs.py         durable question-bank generation jobs
  main.py         HTTP API and web application
  static/         library, tutor/viewer, practice/report and dashboard
scripts/          synthetic evaluation and local RAGAS runner
tests/           contract and integration tests using explicit model doubles
```

`README.md` records what is implemented versus what has actually been validated. A function existing in the repo does not count as a passed live-model acceptance gate.

## Current engineering decisions

- Run all inference on team-owned hardware. Role-specific endpoints allow distributing generation, verification, vision and embeddings across machines.
- Use Postgres and RQ/Redis in deployment. SQLite exists for isolated tests, not as the deployment capacity decision.
- Keep deterministic learner and selection logic independent of orchestration. A graph framework is not required to implement bounded generate/verify loops.
- Serve the current web client from FastAPI to integrate all required workflows now. A framework migration is justified only by a concrete UI requirement; it does not replace required functionality work.
- Numeric verification currently compares independent model answers. Before release, add deterministic supported expression/template checks; never execute arbitrary generated Python in the API process.
- The current JSON record store needs migration-backed normalized tables and indexed vector/full-text retrieval before large-corpus deployment. Preserve existing IDs during migration.
- Evaluation quality is a deliverable. The initial synthetic adaptive policy loses on average mastery gain to both baselines; improve and re-evaluate without hiding that result.

## Release gate

- [ ] Live PDF, PPTX, video and diagram fixtures pass locator/content audits.
- [ ] Tutor's off-material and unsupported-claim cases pass measured checks.
- [ ] All three question types and fixed mock exams pass human correctness review.
- [ ] Adaptive sessions use the latest committed state and avoid served/repeated questions.
- [ ] Learner updates are idempotent and reflect only graded evidence.
- [ ] Cold start, teach-back, misconceptions and cited reports work end to end.
- [ ] RAGAS metrics and simulator comparisons reproduce with run provenance.
- [ ] Browser, keyboard, restart/retry and clean-deployment tests pass.
- [ ] Documentation accurately describes limitations and setup.
- [ ] Demo video and submission components are ready.
