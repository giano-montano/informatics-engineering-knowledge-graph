"""Development aid: ingest syllabi one by one over the reference layer alone.

For the adjustment of the prompt (thesis, "Casos de prueba de la ingesta
automatizada"): each syllabus runs through the real orchestrator, extractor and
validator, on the snapshot of a base that holds only the reference layer, and
nothing is written to Neo4j. Runs and facts go to their own stores under
``var/tuning/``, so the evaluator measures them with::

    uv run python scripts/evaluate_ingestion.py cases --isolated --hide-held-out \
        --operational-db var/tuning/operational.sqlite --facts-dir var/tuning/facts

With ``--chain DIR --before CODE`` the snapshot is, instead, the graph a chain
left before it ingested CODE: the base as it is now, less what the runs of DIR
wrote from CODE on. It shows how a syllabus links to existing nodes without
running the chain again. Still nothing is written.

The two held-out syllabi are refused. Calls to a paid provider are counted in
``var/tuning/paid-calls.json`` before they are made, against a fixed cap, and
go without retries of any kind.

    uv run python scripts/tune_prompt.py 1INF25 1INF33
    uv run python scripts/tune_prompt.py --all
"""

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from neo4j import GraphDatabase

from iekg.core.auditor import AuditReport
from pydantic_ai import Agent, PromptedOutput
from pydantic_ai.messages import ModelRequest, RetryPromptPart, UserPromptPart

from iekg.core.batch import Batch, EdgeFact, Snapshot
from iekg.core.repository import GraphRepository, WriteResult
from iekg.fact_store import FactStore
from iekg.graph_schema import REFERENCE
from iekg.ingestion import extractor as extractor_module
from iekg.ingestion import worker
from iekg.ingestion.declared import SYLLABUS
from iekg.ingestion.extractor import INSTRUCTIONS, SyllabusOutput, prompt_version, read_document
from iekg.ingestion.orchestrator import Orchestrator
from iekg.ingestion.submission import submit_document
from iekg.operational_store import LOAD, OperationalStore
from iekg.settings import ProviderSettings, Settings

SYLLABI = Path("casos-de-prueba/silabos-en-orden")
TUNING = Path("var/tuning")
HELD_OUT = ("1INF27", "1INF37")
# In the order of the measurement.
COURSES = {
    "1INF25": "Programación 2",
    "1INF27": "Algoritmia",
    "1INF33": "Bases de Datos",
    "1INF49": "Ingeniería de Requisitos",
    "1INF29": "Sistemas Operativos",
    "1INF30": "Programación 3",
    "1INF31": "Arquitectura de Software",
    "1INF32": "Algoritmos Avanzados",
    "1INF24": "Inteligencia Artificial",
    "1INF50": "Diseño de Software",
    "1INF37": "Ingeniería de Software",
    "1INF54": "Proyecto de Diseño y Desarrollo de Software",
    "1INF47": "Proyecto de Implementación de Software",
}
# Paid providers: where they are, the variable with their key and the cap of
# calls for the whole adjustment session.
PAID = {
    "openai": (None, "OPEN_AI_API_KEY", 2),
    "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY", 4),
}


def syllabus_path(code: str) -> Path:
    found = [path for path in SYLLABI.glob("*.PDF") if f"-{code}-" in path.name]
    if len(found) != 1:
        raise SystemExit(f"error: {len(found)} syllabi for {code} in {SYLLABI}")
    return found[0]


def cached_reader(path: Path) -> str:
    """Docling's Markdown, read once per document: the conversion takes far longer than it changes."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    cache = TUNING / "markdown" / f"{digest}.md"
    if cache.exists():
        return cache.read_text(encoding="utf-8")
    text = read_document(path)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(text, encoding="utf-8")
    return text


@dataclass
class ReferenceGraph:
    """The reference layer as the base has it, and a writer that writes nothing."""

    snapshot: Snapshot

    def read_snapshot(self) -> Snapshot:
        return self.snapshot

    def write_batch(self, batch: Batch, snapshot: Snapshot, *, layer: str, provenance: str) -> WriteResult:
        return WriteResult(len(batch.nodes), len(batch.edges), 0, 0)

    def audit(self) -> AuditReport:
        return AuditReport(())


def read_snapshot(settings: Settings) -> Snapshot:
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        return GraphRepository(driver, settings.neo4j_database).read_snapshot()


def read_reference_snapshot(settings: Settings) -> Snapshot:
    snapshot = read_snapshot(settings)
    foreign = [key for key, node in snapshot.nodes.items() if node.layer != REFERENCE]
    if foreign or not snapshot.nodes:
        raise SystemExit(f"error: the base must hold the reference layer alone ({len(snapshot.nodes)} nodes, "
                         f"{len(foreign)} of another layer); run `iekg-build load` first")
    return snapshot


def snapshot_before(snapshot: Snapshot, chain: Path, code: str) -> Snapshot:
    """``snapshot`` less the nodes and edges the runs of ``chain`` wrote from the syllabus ``code`` on."""
    facts = FactStore(chain / "facts")
    with OperationalStore(chain / "operational.sqlite") as store:
        course_of = {run.id: run.course_code for run in store.list_runs()}
    order = list(COURSES)
    earlier_nodes: set[str] = set()
    earlier_edges: set[EdgeFact] = set()
    later_nodes: set[str] = set()
    later_edges: set[EdgeFact] = set()
    for run_id in sorted(facts.run_ids()):
        batch = facts.load(run_id).batch
        before = order.index(course_of[run_id]) < order.index(code)
        (earlier_nodes if before else later_nodes).update(batch.nodes_by_key)
        (earlier_edges if before else later_edges).update(batch.edges)
    dropped = later_nodes - earlier_nodes
    nodes = {key: node for key, node in snapshot.nodes.items() if key not in dropped}
    edges = tuple(edge for edge in snapshot.edges
                  if edge.source in nodes and edge.target in nodes and edge not in later_edges - earlier_edges)
    print(f"Snapshot before {code}: {len(nodes)} of {len(snapshot.nodes)} nodes, "
          f"{len(edges)} of {len(snapshot.edges)} edges")
    return Snapshot(nodes=nodes, edges=edges)


def record_retries(extractor) -> list[str]:
    """Keep what each content retry told the model: the stores do not record it."""
    told: list[str] = []
    inner = extractor._extraction

    def extraction(history, retries, output=None):
        told[:] = [str(part.content)[:2000] for message in history if isinstance(message, ModelRequest)
                   for part in message.parts if isinstance(part, (RetryPromptPart, UserPromptPart))][1:]
        return inner(history, retries, output)

    extractor._extraction = extraction
    return told


def spend_paid_call(provider: str, note: str) -> None:
    """Count the call before making it; refuse past the cap."""
    cap = PAID[provider][2]
    ledger = TUNING / "paid-calls.json"
    calls = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else []
    made = sum(1 for call in calls if call["provider"] == provider)
    if made >= cap:
        raise SystemExit(f"error: {provider} already has {made} of {cap} calls; none is left")
    calls.append({"provider": provider, "at": datetime.now().astimezone().isoformat(timespec="seconds"), "note": note})
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(calls, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Paid call {made + 1} of {cap} to {provider}: {note}")


def provider_settings(args: argparse.Namespace) -> ProviderSettings:
    if args.provider == "dev":
        base = ProviderSettings.from_environment()
        return ProviderSettings(args.model or base.model, base.api_key, base.base_url,
                                args.effort or base.reasoning_effort, base.temperature, base.max_retries,
                                base.timeout_seconds)
    base_url, key_variable, _ = PAID[args.provider]
    if not args.model or not args.effort:
        raise SystemExit("error: a paid call names its --model and its --effort ('default' sends none)")
    # No retries of any kind: one run is one request.
    effort = None if args.effort == "default" else args.effort
    return ProviderSettings(args.model, os.environ[key_variable], base_url, effort, None, 0, 1800.0)


def ask_by_prompt(extractor) -> None:
    """For a provider without schema-bound output (DeepSeek, ADR-015): the schema goes in
    the prompt and the answer comes as a JSON object. A probe of the prompt, not the system."""
    agent = extractor._agent
    extractor._agent = Agent(agent.model, output_type=PromptedOutput(SyllabusOutput), instructions=INSTRUCTIONS,
                             model_settings=agent.model_settings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("courses", nargs="*", help="course codes; none of the held-out ones")
    parser.add_argument("--all", action="store_true", help="the 11 syllabi of the adjustment, in order")
    parser.add_argument("--provider", choices=("dev", *PAID), default="dev")
    parser.add_argument("--model", help="default: IEKG_LLM_MODEL (dev provider)")
    parser.add_argument("--effort", help="default: IEKG_LLM_REASONING_EFFORT (dev provider)")
    parser.add_argument("--content-retries", type=int,
                        help="override the content retries of the extractor (a paid call goes with 0)")
    parser.add_argument("--note", default="", help="why these runs, for the log")
    parser.add_argument("--chain", type=Path, help="the stores of a chain whose graph is in the base")
    parser.add_argument("--before", help="with --chain: the syllabus the snapshot stops before")
    args = parser.parse_args()

    courses = [code for code in COURSES if code not in HELD_OUT] if args.all else [c.upper() for c in args.courses]
    if not courses:
        parser.error("name the courses, or --all")
    for code in courses:
        if code in HELD_OUT:
            raise SystemExit(f"error: {code} is held out: it is not ingested before the measurement")
        if code not in COURSES:
            raise SystemExit(f"error: {code} is not a test case")
    paid = args.provider != "dev"
    if paid and len(courses) != 1:
        raise SystemExit("error: a paid call takes one syllabus at a time")

    settings = Settings.from_environment()
    provider = provider_settings(args)
    if paid:
        extractor_module.CONTENT_RETRIES = 0
    if args.content_retries is not None:
        extractor_module.CONTENT_RETRIES = args.content_retries
    if args.chain:
        if courses != [args.before]:
            raise SystemExit("error: with --chain, the one course is the one named by --before")
        graph = ReferenceGraph(snapshot_before(read_snapshot(settings), args.chain, args.before))
    else:
        graph = ReferenceGraph(read_reference_snapshot(settings))
    extractor = worker.build_extractor(provider, reader=cached_reader)
    if args.provider == "deepseek":
        ask_by_prompt(extractor)
    told = record_retries(extractor)
    log = TUNING / "runs.jsonl"

    with OperationalStore(TUNING / "operational.sqlite") as store:
        if store.latest_audit_report() is None:
            # The audit gate asks for a clean report; the reference layer was audited by the load.
            store.complete_audit_report(store.open_audit_report(origin=LOAD), AuditReport(()))
        orchestrator = Orchestrator(store=store, graph=graph, extractor=extractor, facts=FactStore(TUNING / "facts"),
                                    documents=TUNING / "documents", public_base_url=settings.public_base_url)
        for code in courses:
            path = syllabus_path(code)
            cached_reader(path)  # before the call is counted: a reading failure spends nothing
            if paid:
                spend_paid_call(args.provider, f"{code} {provider.model} {provider.reasoning_effort} {args.note}")
            with path.open("rb") as content:
                run_id = submit_document(store, TUNING / "documents", content, file_name=path.name,
                                         resource_type=SYLLABUS, course_code=code, course_name=COURSES[code])
            started = time.monotonic()
            told.clear()
            orchestrator.process(store.take_pending_run())
            run = store.get_run(run_id)
            record = {
                "run_id": run_id, "course": code, "status": run.status, "provider": args.provider,
                "model": run.model, "requested_model": provider.model, "effort": provider.reasoning_effort,
                "prompt_version": prompt_version(), "content_retries": run.content_retries,
                "input_tokens": run.input_tokens, "output_tokens": run.output_tokens,
                "seconds": round(time.monotonic() - started, 1), "error": run.error, "note": args.note,
                "chain": str(args.chain) if args.chain else None, "retries_told": list(told),
                "discards": [[d.rule, d.fact, d.message] for d in store.discards_of(run_id)],
                "at": datetime.now().astimezone().isoformat(timespec="seconds"),
            }
            with log.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"  {json.dumps(record, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
