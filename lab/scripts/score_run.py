"""Score finished runs against a reference annotation and compare them.

Reads `extraction.json` from each run directory, compares it to the annotation,
writes `score.json` next to it and prints one table for all of them.

The comparison is automatic and gold-based, so it is a LOWER BOUND on
precision: an extraction the annotation never listed counts as wrong even when
a human would accept it. Its purpose is to make runs comparable to each other.
R4's criterion is a manual count and this does not replace it.

Usage:
  uv run python lab/scripts/score_run.py build/runs/* \
      --annotation lab/gold/1INF33-2026-2.annotation.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import gold, rules, scoring  # noqa: E402
from iekg.contracts import Extraction  # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", type=Path, help="run directories")
    parser.add_argument("--annotation", type=Path, required=True)
    args = parser.parse_args()

    spec = rules.load()
    annotation = gold.load_annotation(args.annotation, gold.read_backbone(spec))
    if annotation.annotator != gold.CANONICAL_ANNOTATOR:
        print(f"CONTRAST ANNOTATION by '{annotation.annotator}': these numbers are "
              f"experimental, not R4's precision.\n")

    print(f"reference: {len(annotation.topics)} topics, "
          f"{annotation.concept_count} concepts, "
          f"{sum(1 for t in annotation.topics if t.links_to_ku)} linked\n")

    header = (f"{'run':<34} {'topics P/R':>18} {'concepts P/R':>18} "
              f"{'link':>12} {'noise':>6}")
    print(header)
    print("-" * len(header))

    for run_dir in sorted(args.runs):
        path = run_dir / "extraction.json"
        if not path.exists():
            print(f"{run_dir.name:<34}  no extraction.json")
            continue

        extraction = Extraction.model_validate_json(path.read_text(encoding="utf-8"))
        report = scoring.score(extraction, annotation)
        (run_dir / "score.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        topics, concepts, links = report["topics"], report["concepts"], report["linking"]
        print(
            f"{run_dir.name:<34} "
            f"{topics['precision_exact']:.2f}/{topics['recall_exact']:.2f}"
            f" ~{topics['precision_relaxed']:.2f}/{topics['recall_relaxed']:.2f}  "
            f"{concepts['precision_exact']:.2f}/{concepts['recall_exact']:.2f}"
            f" ~{concepts['precision_relaxed']:.2f}/{concepts['recall_relaxed']:.2f}  "
            f"{links['correct']}/{links['judged']}={links['accuracy']:.2f}  "
            f"{report['noise']['count']:>4}"
        )

    print("\nP/R exact, then ~relaxed (half the content words shared).")
    print("A wide gap between the two means the right things were found and named badly.")
    print("link = correct / judged, judged only on topics that matched the reference.")
    print("noise = extracted topics matching something the reference put out of scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
