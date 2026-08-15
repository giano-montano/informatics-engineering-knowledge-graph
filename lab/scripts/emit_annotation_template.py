"""Emit the blind reference annotation form and its backbone pick list.

The blind annotation is the sequencing blocker of the O2 comparison: it has to
exist before any pipeline output is shown for the annotated syllabus. This
script produces the empty form; filling it is manual, on purpose.

It refuses to overwrite a form that already has content, so a rerun can never
destroy work in progress.

Usage:
  uv run python lab/scripts/emit_annotation_template.py \
      lab/docs/syllabus/1INF33-2026-2-SILABO-BASES-DE-DATOS.PDF
  uv run python lab/scripts/emit_annotation_template.py <pdf> --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import gold, rules  # noqa: E402

# PUCP syllabus filenames carry the course code and term: 1INF33-2026-2-...
FILENAME = re.compile(r"^(?P<code>[0-9A-Z]+)-(?P<term>\d{4}-\d)", re.IGNORECASE)


def parse_name(path: Path) -> tuple[str, str]:
    match = FILENAME.match(path.name)
    if not match:
        raise SystemExit(
            f"cannot read course code and term from {path.name!r}; "
            f"expected something like 1INF33-2026-2-SILABO.PDF"
        )
    return match.group("code").upper(), match.group("term")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("syllabus", type=Path, help="the PDF to be annotated")
    parser.add_argument("--annotator", default="giano")
    parser.add_argument("--slots", type=int, default=8,
                        help="empty topic blocks to pre-render (default 8)")
    parser.add_argument("--check", action="store_true",
                        help="validate the filled form instead of writing one")
    args = parser.parse_args()

    code, term = parse_name(args.syllabus)
    spec = rules.load()
    catalog = gold.read_backbone(spec)
    gold.GOLD_DIR.mkdir(parents=True, exist_ok=True)

    catalog_path = gold.GOLD_DIR / "backbone-catalog.md"
    form_path = gold.GOLD_DIR / f"{code}-{term}.annotation.yaml"

    if args.check:
        if not form_path.exists():
            print(f"MISSING  {form_path.relative_to(ROOT)}")
            return 1
        try:
            annotation = gold.load_annotation(form_path, catalog)
        except gold.AnnotationError as exc:
            print(f"INVALID  {form_path.relative_to(ROOT)}\n         {exc}")
            return 1
        print(f"{form_path.relative_to(ROOT)}")
        print(f"  {len(annotation.topics)} topics, {annotation.concept_count} concepts, "
              f"{len(annotation.out_of_scope)} out of scope")
        linked = sum(1 for t in annotation.topics if t.links_to_ku)
        print(f"  {linked}/{len(annotation.topics)} topics linked to a knowledge unit")
        low = [t.label_en for t in annotation.topics if t.confidence == "low"]
        if low:
            print(f"  low confidence: {', '.join(low)}")
        if not annotation.date:
            print("  NOT SEALED: `date` is empty, so the form is still open")
            return 1
        if not annotation.blind:
            print("  WARNING: blind is false; this reference cannot ground precision")
        print("Annotation valid.")
        return 0

    catalog_path.write_text(gold.catalog_markdown(catalog), encoding="utf-8")
    areas = len({e.area_key for e in catalog})
    print(f"Wrote {catalog_path.relative_to(ROOT)}  ({areas} areas, {len(catalog)} units)")

    if form_path.exists():
        # Only the untouched template gets overwritten; anything typed stays.
        existing = form_path.read_text(encoding="utf-8")
        if '""' not in existing or existing.count('label_es: ""') != existing.count("label_es:"):
            print(f"KEPT   {form_path.relative_to(ROOT)} already has content, not touching it")
            return 0

    form_path.write_text(
        gold.template(code, term, args.syllabus, annotator=args.annotator,
                      topic_slots=args.slots),
        encoding="utf-8",
    )
    print(f"Wrote {form_path.relative_to(ROOT)}  ({args.slots} empty topic slots)")
    print("\nFill it in by hand BEFORE running any pipeline on that syllabus.")
    print("Then: uv run python lab/scripts/emit_annotation_template.py "
          f"{args.syllabus.as_posix()} --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
