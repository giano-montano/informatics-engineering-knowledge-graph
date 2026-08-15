"""Run one or more ingestion pipelines over a document and leave the evidence.

Nothing here writes to Neo4j. A run produces `build/runs/<pipeline>-<model>-
<document>/` with the text, the prompts, the extraction, the linking decisions,
the schema violations and the Cypher that WOULD be written. Loading it is a
separate step, taken after reading what it says.

The blind gate: a run refuses to start unless the document has a sealed
reference annotation. Showing an extraction before the annotation exists
contaminates the gold standard, and a rule that lives only in a handoff
document gets forgotten exactly once.

Usage:
  uv run python lab/scripts/run_pipeline.py --list
  uv run python lab/scripts/run_pipeline.py P1 --document <pdf>
  uv run python lab/scripts/run_pipeline.py all --document <pdf> --model reasoner_fallback
  uv run python lab/scripts/run_pipeline.py P0 --document <txt> --ungated  # smoke test
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from iekg import gold, llm, pipeline, rules  # noqa: E402
from iekg.abox import SourceDocument  # noqa: E402

FILENAME = re.compile(r"^(?P<code>[0-9A-Z]+)-(?P<term>\d{4}-\d)", re.IGNORECASE)


def describe(specs: dict[str, pipeline.PipelineSpec]) -> None:
    for name, spec in specs.items():
        print(f"{name}  {spec.title}")
        print(f"    adds:     {spec.adds}")
        print(f"    isolates: {spec.isolates}")
        print(f"    stages:   {' -> '.join(spec.stages)}")
        print(f"    model:    {spec.model}")


def as_document(path: Path) -> SourceDocument:
    match = FILENAME.match(path.name)
    code = match.group("code").upper() if match else path.stem.upper()[:16]
    term = match.group("term") if match else "0000-0"
    return SourceDocument(code=code, term=term, path=path, title=path.stem)


def parse_options(pairs: list[str]) -> dict:
    """`--option threshold=0.7` overrides lab/pipelines.yaml for one run.

    Only for sweeping a parameter. Anything that survives the sweep belongs in
    the YAML, or the run that produced a result stops being reproducible from
    the repository.
    """
    out: dict = {}
    for pair in pairs:
        key, _, value = pair.partition("=")
        if not _:
            raise SystemExit(f"--option expects key=value, got {pair!r}")
        try:
            out[key] = float(value) if "." in value else int(value)
        except ValueError:
            out[key] = {"true": True, "false": False}.get(value.lower(), value)
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pipelines", nargs="*", help="P0 P1 ... or 'all'")
    parser.add_argument("--document", type=Path)
    parser.add_argument("--model", help="override the catalog name in pipelines.yaml")
    parser.add_argument("--option", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--list", action="store_true", help="show the compositions")
    parser.add_argument("--ungated", action="store_true",
                        help="run without a sealed reference annotation")
    parser.add_argument("--annotation", type=Path,
                        help="use this annotation file instead of the canonical one")
    parser.add_argument("--tag", default="",
                        help="suffix for the run directory, to keep a sweep apart")
    args = parser.parse_args()

    specs = pipeline.load_pipelines()
    if args.list or not args.pipelines:
        describe(specs)
        return 0

    if args.document is None:
        raise SystemExit("--document is required")
    if not args.document.exists():
        raise SystemExit(f"no such document: {args.document}")

    names = list(specs) if args.pipelines == ["all"] else args.pipelines
    unknown = [n for n in names if n not in specs]
    if unknown:
        raise SystemExit(f"unknown pipeline(s): {unknown}; known: {', '.join(specs)}")

    document = as_document(args.document)
    annotation_path = args.annotation or gold.GOLD_DIR / f"{document.key}.annotation.yaml"
    annotation = gold.read_seal(annotation_path)
    sealed = annotation is not None

    if sealed and annotation.annotator != gold.CANONICAL_ANNOTATOR:
        # It opens the gate -- there is a blind reference and the run cannot
        # contaminate it -- but it is not the gold standard, and a number
        # measured against it is not R4's precision figure. Said out loud here
        # and written into every manifest, because a file that behaves exactly
        # like the real one is the easiest kind to mistake for it.
        print(f"CONTRAST ANNOTATION: {annotation_path.name}")
        print(f"         annotator '{annotation.annotator}', not "
              f"'{gold.CANONICAL_ANNOTATOR}'. Gate opens, gold standard does not.")
        print("         Anything measured against this is experimental, not R4.")

    if not sealed and not args.ungated:
        print(f"BLOCKED  {document.key} has no sealed reference annotation.")
        print(f"         expected: {annotation_path.relative_to(ROOT)}")
        print("         Fill it in and seal it (set `date`), then check it with")
        print("         lab/scripts/emit_annotation_template.py --check.")
        print("         Running now would show extractions of a document whose")
        print("         gold standard is not yet blind, which cannot be undone.")
        print("         --ungated overrides this and is recorded in the manifest.")
        return 1
    if not sealed:
        print(f"WARNING  running UNGATED on {document.key}: no sealed annotation.")

    spec = rules.load()
    catalog = llm.load()
    overrides = parse_options(args.option)

    failures = 0
    for name in names:
        config = specs[name]
        if args.model:
            config = replace(config, model=args.model)
        if overrides:
            config = replace(config, options={**config.options, **overrides})

        print(f"\n=== {name}  {config.title}  ({config.model})")
        try:
            out_dir = pipeline.run_dir(config, document)
            if args.tag:
                out_dir = out_dir.with_name(f"{out_dir.name}-{args.tag}")
            ctx = pipeline.run(config, document, spec, catalog,
                               out_dir=out_dir,
                               gate_bypassed=not sealed,
                               annotation=annotation,
                               annotation_path=annotation_path)
        except Exception as exc:
            print(f"    FAILED  {type(exc).__name__}: {exc}"[:300])
            failures += 1
            continue

        for record in ctx.records:
            print(f"    {record.stage:<18} {record.seconds:6.2f}s "
                  f"{record.requests:>3} req {record.tokens:>7} tok  {record.note}")

        declared = catalog.entry(config.model).model_id
        answered = sorted(ctx.answered_by)
        if answered and answered != [declared]:
            # Never accepted in silence: a run served by the fallback is not a
            # measurement of the model it was asked for.
            print(f"    FALLBACK FIRED: asked {declared}, answered {', '.join(answered)}")
        print(f"    -> {ctx.out_dir.relative_to(ROOT)}")

    print(f"\n{failures} pipeline(s) failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
