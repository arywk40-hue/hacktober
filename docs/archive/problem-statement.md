# Multimodal-personalized-
Multimodal AI Hackathon 2026

Track D: Personalized Tutoring & Adaptive Learning
Challenge: Build an AI study companion that unifies lecture videos,
textbooks, and slides into a source-cited knowledge base, and uses it to
run adaptive assessments and personalized tutoring.
Context:
Students often study from lecture videos, textbooks, and slides scattered across places, and
general AI chatbots can give answers that are not tied to the course material or to what the
student already understands. A source-grounded companion that models the learner could
make study time more trustworthy and effective.

Requirements:
1. Multimodal Knowledge Base:
a. Ingest lecture videos, textbooks, and slide decks without manual preprocessing.
b. Organize content into topics, concepts, and prerequisites, with every unit linked
to its origin (page, slide number, video timestamp).
c. Identify major topics, subtopics, and key concepts, and tag every content unit to
them.
d. Extract and use information from images, diagrams, and figures in slides and
textbooks.
2. Source Grounding:
a. Explain concepts and answer questions using cited excerpts that open the exact
page, slide, or timestamp
b. Decline or clearly flag queries the material does not cover, separating outside
knowledge from source-backed content.

3. Adaptive Assessment:
a. Generate quizzes and mock exams (MCQ, short answer, numerical problems) on
student-chosen scope, with each question tagged to a topic, source location, and
difficulty.
b. Verify question correctness (using answer verification or cross-model validation)
and avoid repeated questions across assessments.
c. Give cited feedback on each answer and a post-assessment report identifying
weak topics and likely misconceptions.

4. Learner Model:
a. Maintain per-topic mastery estimates that update after every quiz and
conversation (for example, using Bayesian knowledge tracing, IRT-style
estimation, or spaced repetition).
b. Handle new students with no history (diagnostic quiz, intake conversation).
5. System Evaluation:
a. Evaluate the retrieval and generation pipeline using a standard evaluation
framework (using RAGAS, DeepEval, TruLens, or similar)
b. Report metrics for faithfulness, answer relevancy, and context precision and
recall on a team-built test set (questions with known source locations, off-material
queries)
c. Evaluate personalization using simulated student profiles run across multiple
sessions, reporting mastery gains and question repetition rate

6. Optional Enhancements:
a. Generate a visual course flow map of topics and prerequisites
b. Produce revision material targeted at weak topics (flashcards, slides, audio
briefs)
c. Generate a study schedule based on weak topics, forgetting curves, and time
before an exam
d. Support mixed-language content or Indian-language interaction (English lectures
with Hindi explanations)
e. Audio based for tutoring sessions.

Expected Deliverables:
● Working Software Prototype: A web/app based prototype featuring the multimodal
ingestion workflow, source-grounded tutor chat, adaptive assessment generator, and
dashboard.
● Project Documentation: Documentation of architecture, grounding method, and
learner-model approach.
● Evaluation & Benchmarking: Evaluation results of framework-based metrics and
simulated student results on team-chosen course material.
● Demonstration Video: A 3-10 minute youtube video demonstrating the working system,
source uploading workflow, grounded chat interactions, assessment pipeline, and
technical architecture implementation.

Technical Considerations:
● Generated content must remain grounded in uploaded material, with unsupported claims
declined or flagged
● Question tags and answer keys should be accurate enough to support a reliable learner
model.
● Personalization should improve measurably as more student data becomes available
● Teams may use any suitable course material (MIT OpenCourseWare, NPTEL, public
textbooks, self-created content); no fixed dataset is required.
Evaluation Criteria:
● Knowledge Base & Grounding (20%): Accuracy of multimodal extraction, source-link
preservation, citation accuracy, correct refusal of unsupported queries
● Assessment Quality (15%): Question correctness and novelty, topic and source
tagging, usefulness of feedback and analysis reports.
● Personalization Effectiveness (20%): Learner-model approach, measurable gains in
simulated student runs, responsiveness of tutor and recommendations to student state
● User Experience & Demo Video (15%): Dashboard clarity, UI/UX workflow, usability,
optional features.
● System Evaluation (15%): Choice of evaluation framework and metrics, quality of test
set, rigor and honesty of reported results.
● Technical Implementation (15%): Code quality, system architecture.
