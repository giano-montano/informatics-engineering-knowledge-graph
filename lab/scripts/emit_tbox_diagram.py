"""Emit the T-box diagram from the ontology and the schema rules.

Reads no database and writes none: the T-box is not materialised in Neo4j.
Same contract as check_integrity.py --emit-only.

Usage: uv run python lab/scripts/emit_tbox_diagram.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import rules, tbox  # noqa: E402

TARGET = ROOT / "build" / "tbox.md"


def main() -> int:
    spec = rules.load()
    box = tbox.read_tbox(None, spec)

    print(f"Read T-box: {len(box.classes)} classes, "
          f"{len(box.object_properties)} object properties, "
          f"{len(box.data_properties)} data/annotation properties")

    unmapped = sorted(c for c in box.classes if not tbox.is_projected(c, spec))
    if unmapped:
        print(f"WARNING  classes with no LPG mapping: {unmapped}")

    unknown = sorted(set(spec.classes) - set(box.classes))
    if unknown:
        print(f"WARNING  mapped classes absent from the ontology: {unknown}")

    path = tbox.write_artifact(spec, TARGET)
    print(f"Written {path.relative_to(ROOT)}")
    return 1 if unmapped or unknown else 0


if __name__ == "__main__":
    sys.exit(main())
