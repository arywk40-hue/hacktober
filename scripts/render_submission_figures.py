"""Render submission diagrams from source-reviewed architecture and recorded results.

Presentation-only dependency: matplotlib. Does not run models or send telemetry.
"""
import json
import os
import tempfile
from pathlib import Path
from statistics import median

os.environ.setdefault("MPLCONFIGDIR", tempfile.mkdtemp(prefix="citetutor-figures-"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
INK = "#172D45"
MUTED = "#52667C"
LINE = "#C9D5DF"
BLUE = "#2467BB"
PURPLE = "#7555B4"
TEAL = "#167E77"
AMBER = "#9B651B"
RED = "#AB4444"
PAPER = "#FAFBFD"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 12,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": INK,
    "svg.fonttype": "none", "svg.hashsalt": "citetutor-submission",
})


def text(ax, x, y, value, size=12, color=INK, weight="normal", ha="left", va="center"):
    return ax.text(x, y, value, fontsize=size, color=color, fontweight=weight,
                   ha=ha, va=va, linespacing=1.5, zorder=5)


def box(ax, x, y, width, height, title, detail, color=TEAL, fill="#F0F8F7"):
    ax.add_patch(FancyBboxPatch(
        (x, y), width, height, boxstyle="round,pad=0.02,rounding_size=0.12",
        facecolor=fill, edgecolor=LINE, linewidth=1, zorder=3))
    text(ax, x + 0.20, y + height - 0.30, title, 13, color, "bold")
    text(ax, x + 0.20, y + height - 0.64, detail, 10.7, va="top")


def arrow(ax, points, color=MUTED, dashed=False):
    for start, end in zip(points[:-2], points[1:-1], strict=True):
        ax.plot([start[0], end[0]], [start[1], end[1]], color=color, linewidth=1.35,
                linestyle="--" if dashed else "-", zorder=2)
    ax.add_patch(FancyArrowPatch(
        points[-2], points[-1], arrowstyle="-|>", mutation_scale=14,
        linewidth=1.35, color=color, linestyle="--" if dashed else "-", zorder=2))


def save(fig, stem, title, description):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=160, facecolor=fig.get_facecolor())
    fig.savefig(OUT / f"{stem}.svg", facecolor=fig.get_facecolor(),
                metadata={"Date": None, "Title": title, "Description": description})
    plt.close(fig)


def architecture():
    fig, ax = plt.subplots(figsize=(18, 17), facecolor=PAPER)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.set(xlim=(0, 18), ylim=(0, 17))
    ax.axis("off")
    text(ax, 0.7, 16.35, "CiteTutor", 31, weight="bold")
    text(ax, 0.7, 15.80, "Local study help. Inspectable sources. Verification before display.", 15, MUTED)
    ax.add_patch(FancyBboxPatch(
        (0.5, 3.15), 17, 12.10, boxstyle="round,pad=0.02,rounding_size=0.16",
        facecolor="#FFFFFF", edgecolor=LINE, linewidth=1.5, zorder=0))
    text(ax, 0.9, 14.90, "ON THE LEARNER'S LAPTOP", 12, TEAL, "bold")
    text(ax, 16.95, 14.90, "FastAPI + local UI  ·  Ollama  ·  SQLite", 11, MUTED, ha="right")
    text(ax, 0.95, 14.30, "01  INGEST AND INDEX", 11, MUTED, "bold")
    box(ax, 1, 12.30, 4.5, 1.65, "PDF material", "Text chapters or scanned notes\nPhysical page numbers preserved")
    box(ax, 6.7, 12.30, 4.5, 1.65, "Extract / review", "PyMuPDF extracts selectable text\nScans: GLM-OCR + human review\nUnapproved scans stay out of retrieval")
    box(ax, 12.4, 12.30, 4.5, 1.65, "Local source index", "SQLite + nomic-embed-text vectors\n1,600-character chunks / 200 overlap\nDocument, chunk and page identity")
    arrow(ax, [(5.5, 13.12), (6.65, 13.12)])
    arrow(ax, [(11.2, 13.12), (12.35, 13.12)])
    arrow(ax, [(14.65, 12.28), (14.65, 11.60), (2.8, 11.60), (2.8, 10.85)])
    text(ax, 0.95, 11.08, "02  TUTOR", 11, MUTED, "bold")
    box(ax, 1, 9.08, 3.6, 1.75, "Hybrid retrieval", "Question + selected material\nBM25-style + cosine → RRF\nDefault: four source chunks")
    box(ax, 5.4, 9.08, 3.15, 1.75, "Gemma draft", "gemma3:4b\nStructured answer segments\nSupplied chunk IDs only", BLUE, "#EEF4FC")
    box(ax, 9.35, 9.08, 2.95, 1.75, "Code guards", "Pydantic / JSON Schema\nKnown, present citations\nWorked-quantity guard*", AMBER, "#FBF5EA")
    box(ax, 13.1, 9.08, 3.8, 1.75, "Qwen verification", "qwen2.5:3b — different family\nBlind solve: no Gemma draft\nThen support + agreement", PURPLE, "#F4F0FB")
    for x1, x2 in [(4.6, 5.35), (8.55, 9.30), (12.30, 13.05)]:
        arrow(ax, [(x1, 9.95), (x2, 9.95)])
    box(ax, 5.4, 7.03, 6.9, 1.35, "Fail → retry, at most three drafts", "Failed drafts stay hidden. None pass →\n“Not enough evidence in this document”", RED, "#FDF1F1")
    box(ax, 13.1, 7.03, 3.8, 1.35, "Pass → show answer", "Code builds [p. N] citations\nClick to inspect source text")
    arrow(ax, [(10.82, 9.06), (10.82, 8.40)], RED, True)
    text(ax, 11.02, 8.75, "fail", 10, RED)
    arrow(ax, [(13.08, 9.65), (12.68, 9.65), (12.68, 7.72), (12.33, 7.72)], RED, True)
    arrow(ax, [(15, 9.06), (15, 8.40)], TEAL)
    text(ax, 15.20, 8.75, "pass", 10, TEAL)
    arrow(ax, [(5.38, 7.72), (4.97, 7.72), (4.97, 9.70), (5.37, 9.70)], RED, True)
    text(ax, 0.98, 8.03, "No unverified streaming.\nStyle changes wording,\nnever factual evidence.", 11, MUTED)
    text(ax, 0.98, 6.60, "*Explicit value-and-unit requests require a worked quantity in the cited text.", 10.5, MUTED)
    text(ax, 0.95, 6.09, "03  QUIZ — A SEPARATE ACCEPTANCE GATE", 11, MUTED, "bold")
    box(ax, 1, 4.30, 3.5, 1.45, "Page range → Gemma", "One PDF, selected pages\nMCQ or short-answer candidate\nKey, rationale and source quote", BLUE, "#EEF4FC")
    box(ax, 5.15, 4.30, 3.5, 1.45, "Validate / retrieve", "Schema, source IDs, exact quotes\nRetrieve with stem + options\nKey and rationale excluded", AMBER, "#FBF5EA")
    box(ax, 9.30, 4.30, 3.5, 1.45, "Qwen blind solve", "No proposed key or rationale\nThen key agreement + support\nReject unsupported / ambiguous", PURPLE, "#F4F0FB")
    box(ax, 13.45, 4.30, 3.45, 1.45, "Accept or drop", "Only verified questions shown\nSupporting page + quote\nRejected count stays visible")
    for x1, x2 in [(4.5, 5.1), (8.65, 9.25), (12.8, 13.4)]:
        arrow(ax, [(x1, 5.02), (x2, 5.02)])
    text(ax, 0.98, 3.62, "Model judgments can be wrong; verification checks approved text, not the original image.", 11, MUTED)
    text(ax, 0.95, 2.68, "OPTIONAL TELEMETRY — EXTERNAL SERVICE", 11, MUTED, "bold")
    box(ax, 1, 0.60, 5.5, 1.55, "Metadata-only export", "Event/span field allowlist\nSecond filter at the SDK transport boundary\nBlank DSN disables Sentry", TEAL)
    box(ax, 8, 0.60, 8.9, 1.55, "Sentry Agent Tracing", "Latency, token counts, attempts and fixed outcome codes\nNo documents, images, filenames, prompts or answers\nObserves the pipeline; source checks stay local", BLUE, "#EEF4FC")
    arrow(ax, [(9.1, 3.12), (9.1, 2.38), (3.75, 2.38), (3.75, 2.17)], TEAL, True)
    arrow(ax, [(6.52, 1.37), (7.96, 1.37)], TEAL)
    save(fig, "citetutor-architecture", "CiteTutor local architecture",
         "PDF ingestion and reviewed OCR feed local hybrid retrieval. Gemma drafts, code validates "
         "citations, Qwen blindly solves and checks support before display. Quiz candidates have a "
         "separate gate. Optional Sentry receives allowlisted operational metadata only.")


def load(path):
    return json.loads((ROOT / path).read_text())


def counts(report):
    rows = report["questions"]
    return [sum(q["in_scope"] and q["correct_by_gold_patterns"] for q in rows),
            sum(q["in_scope"] and q["result"]["declined"] for q in rows),
            sum(not q["in_scope"] and q["result"]["declined"] for q in rows)]


def results():
    old = load("eval/reports/local.json")
    new = load("eval/reports/blind-reading.json")
    trace = load("eval/traces/current-tutor-live.json")["supported"]
    if (old["pdf_sha256"], old["questions_sha256"]) != (new["pdf_sha256"], new["questions_sha256"]):
        raise ValueError("Historical comparison requires identical PDF and question fixtures")
    fig = plt.figure(figsize=(16, 12), facecolor=PAPER)
    fig.text(0.06, 0.95, "CiteTutor: measured behavior", fontsize=26, fontweight="bold")
    fig.text(0.06, 0.908, "Authored 3-page mechanics PDF · 10 questions · 8 GB Apple M1", fontsize=13, color=MUTED)
    fig.text(0.06, 0.86, "TWO RECORDED RUNS ON THE SAME FIXTURE", fontsize=11, color=MUTED, fontweight="bold")
    ax = fig.add_axes((0.30, 0.53, 0.62, 0.28), facecolor=PAPER)
    labels = ["Supported answers correct\n7 supported cases — higher is better",
              "False refusals\n7 supported cases — lower is better",
              "Out-of-scope refusals\n3 unrelated cases — higher is better"]
    before, after = counts(old), counts(new)
    for index, (first, second) in enumerate(zip(before, after, strict=True)):
        y = 2 - index
        ax.barh(y + 0.16, first, height=0.26, color="#9CA9B6", label="Earlier · Oct 4, 13:48 IST" if index == 0 else None)
        ax.barh(y - 0.16, second, height=0.26, color=TEAL, label="Revised · Oct 4, 17:23 IST" if index == 0 else None)
        denominator = 3 if index == 2 else 7
        ax.text(first + 0.10, y + 0.16, f"{first}/{denominator}", va="center", fontsize=13, fontweight="bold")
        ax.text(second + 0.10, y - 0.16, f"{second}/{denominator}", va="center", fontsize=13, fontweight="bold")
    ax.set(yticks=[2, 1, 0], yticklabels=labels, xlim=(0, 7.9), xticks=range(8), xlabel="Questions (count)")
    ax.tick_params(axis="y", length=0, pad=18, labelsize=11)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=LINE, alpha=0.65, linewidth=0.8)
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.07), frameon=False, ncol=2, fontsize=11)
    fig.text(0.06, 0.46, "Prompts and Ollama/runtime changed between runs. This is not a controlled ablation.",
             fontsize=12, color=AMBER, fontweight="bold")
    current_latency = median(q["seconds"] for q in new["questions"]
                             if q["in_scope"] and not q["result"]["declined"])
    fig.text(0.06, 0.417, f"Revised run: expected citations 7/7 · quiz 1 accepted, 1 rejected · median answer {current_latency:.1f} s",
             fontsize=12, color=MUTED)
    fig.text(0.06, 0.35, "ONE LIVE SENTRY TRACE: WHY A VERIFIED ANSWER TAKES TIME", fontsize=11, color=MUTED, fontweight="bold")
    durations = [trace["generator"]["model_seconds"], trace["blind_reading"]["model_seconds"],
                 trace["support_check"]["model_seconds_displayed"]]
    total = trace["root_seconds_displayed"]
    remainder = total - sum(durations)
    timeline = fig.add_axes((0.06, 0.215, 0.86, 0.10), facecolor=PAPER)
    offset = 0
    for seconds, color, label in zip(durations, [BLUE, PURPLE, "#AA95CF"],
                                     ["Gemma draft", "Qwen blind solve", "Qwen support"], strict=True):
        timeline.barh(0, seconds, left=offset, height=0.62, color=color)
        timeline.text(offset + seconds / 2, 0, f"{label}\n{seconds:.2f} s", fontsize=11,
                      color="white" if color != "#AA95CF" else INK, ha="center", va="center")
        offset += seconds
    timeline.barh(0, remainder, left=offset, height=0.62, color="#CED7DF")
    timeline.set(xlim=(0, 46), ylim=(-0.7, 0.7), yticks=[], xticks=range(0, 46, 5), xlabel="Elapsed time (seconds)")
    for spine in timeline.spines.values():
        spine.set_visible(False)
    fig.text(0.06, 0.145, f"45.73 s end to end · verification calls {sum(durations[1:]):.2f} s · remaining time ≈ {remainder:.2f} s",
             fontsize=12, fontweight="bold")
    fig.text(0.06, 0.105, "Small developer-authored fixture; no general accuracy or competitor superiority claim.", fontsize=11, color=MUTED)
    fig.text(0.06, 0.065, "Sources: eval/reports/local.json + blind-reading.json; eval/traces/current-tutor-live.json", fontsize=10, color=MUTED)
    fig.text(0.06, 0.035, "Replotted recorded measurements. This figure is not a Sentry dashboard screenshot.", fontsize=10, color=MUTED)
    save(fig, "citetutor-results", "CiteTutor recorded results and latency",
         "Earlier and revised runs on identical fixtures: correct supported answers 4/7 to 7/7, "
         "false refusals 3/7 to 0/7, out-of-scope refusals 3/3 in both. Prompts and runtime changed. "
         "A separate live supported Sentry trace took 45.73 seconds. Small authored fixture only.")


if __name__ == "__main__":
    architecture()
    results()
    print(f"Saved architecture and results as PNG/SVG in {OUT}")
