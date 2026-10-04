"""Capture real local OCR drafts for visual comparison; never auto-approve or index them."""

import argparse
import json
import time
from pathlib import Path

from study.config import Settings
from study.ingest import extract_pdf, page_image
from study.models import ModelError, Models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--model", help="Installed local vision tag; defaults to CITETUTOR_OCR_MODEL")
    parser.add_argument("--force-scan", action="store_true", help="Read existing text layers as images")
    parser.add_argument("--out", type=Path, default=Path("data/scan-check.json"))
    args = parser.parse_args()
    settings = Settings(**({"ocr_model": args.model} if args.model else {}))
    pages = extract_pdf(args.pdf, allow_scans=True, force_scan=args.force_scan)
    report = {"filename": args.pdf.name, "model": settings.ocr_model, "pages": [],
              "status": "unapproved_drafts_for_visual_review", "indexed": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    models = Models(settings)
    try:
        for page in pages:
            if page["reviewed"]:
                report["pages"].append({"page": page["page"], "status": "selectable_text_skipped"})
                continue
            print(f'Reading page {page["page"]} locally…', flush=True)
            start = time.monotonic()
            try:
                draft = models.transcribe(page_image(args.pdf, page["page"]))
                item = {"page": page["page"], "text": draft.text,
                        "incomplete": draft.incomplete,
                        "unclear_markers": draft.text.casefold().count("[unclear]"),
                        "status": "needs_review", "usage": models.calls[-1]}
            except ModelError as exc:
                item = {"page": page["page"], "status": "failed", "error": str(exc)}
            item["seconds"] = round(time.monotonic() - start, 2)
            report["pages"].append(item)
            args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
            print({k: v for k, v in item.items() if k not in {"text", "usage"}}, flush=True)
        args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"Private draft report: {args.out}. Compare every page; this is not an accuracy score.")
    finally:
        models.close()


if __name__ == "__main__":
    main()
