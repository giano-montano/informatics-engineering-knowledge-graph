"""Compile the rules to Cypher and run the integrity queries.

Compilation and execution are deliberately separate steps: the .cypher files
are written to build/ so they can be read, versioned and cited, and only
afterwards executed.

Usage: uv run python lab/scripts/check_integrity.py [--emit-only]
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import integrity, rules  # noqa: E402
from iekg.db import session  # noqa: E402

TARGET = ROOT / "build"


def main() -> int:
    spec = rules.load()
    written = integrity.write_artifacts(spec, TARGET)

    print(f"=== artifacts emitted in {TARGET.relative_to(ROOT)} ===")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")

    if "--emit-only" in sys.argv:
        return 0

    queries = integrity.compile_queries(spec)
    print(f"\n=== running {len(queries)} integrity queries ===")

    total = 0
    with session() as s:
        for rule_id, cypher in queries:
            # Cypher accepts // comments, so the header stays as is; only the
            # trailing semicolon gets in the way.
            rows = list(s.run(cypher.rstrip().rstrip(";")))
            if rows:
                total += len(rows)
                print(f"  VIOLATED  {rule_id}: {len(rows)} cases")
                for row in rows[:5]:
                    print(f"              {row['entity']} -- {row['detail']}")
            else:
                print(f"  OK        {rule_id}")

    print(f"\n{'Integrity satisfied.' if total == 0 else f'{total} violations.'}")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
