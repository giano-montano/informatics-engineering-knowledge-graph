"""Development aid: measure the five navigation patterns of AC-05.

Not an entry point of the system. It runs the same query functions the
navigation routes run, from every starting node of each pattern, and writes
the report the thesis asks for (Table 15; design of the navigation routes,
section 8): a JSON file under var/measurements/ and a Markdown table on the
console.

    uv run python scripts/measure_navigation.py
"""

import argparse
import json
import math
import platform
import statistics
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import neo4j
from neo4j import GraphDatabase, NotificationDisabledCategory

from iekg.api.navigation import (
    GRAINS,
    MAX_DEPTH,
    Query,
    concept_specializations,
    course_prerequisites,
    element_location,
    element_resources,
    fetch_in,
    learning_path,
)
from iekg.core.repository import Tx
from iekg.graph_schema import CONCEPT, COURSE, KEY, KNOWLEDGE_ELEMENT
from iekg.settings import Settings

ROUNDS = 10
THRESHOLD_MS = 1000
RESOLUTION_MS = 1

# Runs a unit of work in a read transaction, like Session.execute_read: the
# script passes that one, the tests their rolled-back transaction.
Execute = Callable[..., Any]


@dataclass(frozen=True)
class Pattern:
    code: str
    name: str
    starts: str  # Cypher returning the keys of the starting nodes, as ``key``
    # The queries from one starting node; one per grain in the lifted prerequisite.
    queries: Callable[[str], Sequence[tuple[str | None, Query]]]
    # The location has fixed depth: the partonomy has three levels.
    reports_depth: bool


def _of(*labels: str) -> str:
    where = " OR ".join(f"n:{label}" for label in labels)
    return f"MATCH (n) WHERE {where} RETURN n.{KEY} AS key ORDER BY key"


PATTERNS = (
    Pattern("PC2", "prerequisite between courses", _of(COURSE),
            lambda key: [(None, course_prerequisites(key))], reports_depth=False),
    Pattern("PC3", "area of a concept", _of(CONCEPT),
            lambda key: [(None, element_location(key))], reports_depth=False),
    Pattern("PC5", "resources rolled up over the parts", _of(KNOWLEDGE_ELEMENT, COURSE),
            lambda key: [(None, element_resources(key))], reports_depth=False),
    Pattern("PC6", "prerequisite lifted to a grain", _of(KNOWLEDGE_ELEMENT, COURSE),
            lambda key: [(grain, learning_path(key, grain)) for grain in GRAINS], reports_depth=True),
    Pattern("PC7", "specialization closure", _of(CONCEPT),
            lambda key: [(None, concept_specializations(key))], reports_depth=True),
)

# Operators that read every node, of the base or of a label, or every edge.
_FULL_SCANS = ("AllNodesScan", "LabelScan", "LabelsScan", "AllRelationshipsScan", "RelationshipTypeScan")


# --- Statistics --------------------------------------------------------------


def nearest_rank(ordered: Sequence[int], fraction: float) -> int:
    """The value at position ceil(fraction * n) of the ordered times: always one
    that was observed."""
    return ordered[max(math.ceil(fraction * len(ordered)), 1) - 1]


def summarize(times: Sequence[int]) -> dict[str, Any]:
    if not times:
        return {"executions": 0, "median_ms": None, "p95_ms": None, "max_ms": None, "passes": None}
    ordered = sorted(times)
    median, p95 = statistics.median(ordered), nearest_rank(ordered, 0.95)
    return {
        "executions": len(ordered),
        "median_ms": median,
        "p95_ms": p95,
        "max_ms": ordered[-1],
        "passes": median < THRESHOLD_MS and p95 < THRESHOLD_MS,
    }


# --- Execution ---------------------------------------------------------------


def _keys_in(tx: Tx, text: str) -> list[str]:
    return [record["key"] for record in tx.run(text)]


def _timed_in(tx: Tx, query: Query) -> tuple[int, int | None]:
    """Time in the engine, without serialization or transport, and the greatest
    depth in the response."""
    fetched = fetch_in(tx, query)
    if fetched.subgraph is None:
        raise LookupError(f"no starting node for {query.parameters}")
    depths = [node.depth for node in fetched.subgraph.nodes if node.depth is not None]
    summary = fetched.summary
    return summary.result_available_after + summary.result_consumed_after, max(depths, default=None)


def measure_pattern(execute: Execute, pattern: Pattern, keys: Sequence[str], rounds: int = ROUNDS) -> dict[str, Any]:
    """A warm-up round and ``rounds`` measured ones; each round runs the pattern
    once from every starting node, so two runs from the same node have all the
    others between them. The first run of the warm-up is the cold one."""
    units = [(key, grain, query) for key in keys for grain, query in pattern.queries(key)]
    warmup = [execute(_timed_in, query) for _, _, query in units]
    measured = [[execute(_timed_in, query)[0] for _, _, query in units] for _ in range(rounds)]
    depths = [depth for _, depth in warmup if depth is not None]
    return {
        "pattern": pattern.code,
        "name": pattern.name,
        "starting_nodes": len(keys),
        "cold_ms": warmup[0][0] if warmup else None,
        **summarize([ms for round_ in measured for ms in round_]),
        "max_depth": max(depths, default=None) if pattern.reports_depth else None,
        "runs": [
            {"key": key, "grain": grain, "warmup_ms": warmup[i][0], "ms": [round_[i] for round_ in measured]}
            for i, (key, grain, _) in enumerate(units)
        ],
    }


def plan_in(tx: Tx, query: Query) -> dict[str, Any]:
    """The operators of the query's plan, and those that break section 3 of the design."""
    summary = tx.run("EXPLAIN " + query.text, query.parameters).consume()
    operators = sorted(set(_operators(summary.plan)))
    return {
        "operators": operators,
        "unpruned_expansions": [op for op in operators if op.startswith("VarLengthExpand") and "Pruning" not in op],
        "full_scans": [op for op in operators if any(scan in op.split("@")[0] for scan in _FULL_SCANS)],
    }


def _operators(plan: dict) -> list[str]:
    return [plan["operatorType"], *(op for child in plan.get("children", []) for op in _operators(child))]


# --- Graph and environment ---------------------------------------------------


def graph_in(tx: Tx) -> dict[str, Any]:
    by_label = {r["label"]: r["n"] for r in tx.run(
        "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS n ORDER BY label")}
    by_type = {r["type"]: r["n"] for r in tx.run(
        "MATCH ()-[r]->() RETURN type(r) AS type, count(*) AS n ORDER BY type")}
    return {
        "nodes": tx.run("MATCH (n) RETURN count(n) AS n").single()["n"],
        "edges": sum(by_type.values()),
        "nodes_by_label": by_label,
        "edges_by_type": by_type,
    }


_SETTINGS = (
    "server.memory.heap.initial_size",
    "server.memory.heap.max_size",
    "server.memory.pagecache.size",
    "db.memory.pagecache.warmup.enable",
)


def engine_in(tx: Tx) -> dict[str, Any]:
    """What the engine says of itself: version, edition, and the machine it sees."""
    component = tx.run("CALL dbms.components() YIELD name, versions, edition "
                       "WHERE name = 'Neo4j Kernel' RETURN versions[0] AS version, edition").single()
    system = tx.run("CALL dbms.queryJmx('java.lang:type=OperatingSystem') YIELD attributes "
                    "RETURN attributes").single()["attributes"]
    settings = {r["name"]: r["value"] for r in tx.run(
        "SHOW SETTINGS YIELD name, value WHERE name IN $names RETURN name, value", names=list(_SETTINGS))}
    return {
        "version": component["version"],
        "edition": component["edition"],
        "processors": _attribute(system, "AvailableProcessors"),
        # Java 14 renamed TotalPhysicalMemorySize; a container reports its own limit.
        "memory_bytes": _attribute(system, "TotalMemorySize") or _attribute(system, "TotalPhysicalMemorySize"),
        "os": " ".join(str(_attribute(system, name)) for name in ("Name", "Version", "Arch")),
        "settings": settings,
    }


def _attribute(attributes: dict, name: str) -> Any:
    return (attributes.get(name) or {}).get("value")


def host() -> dict[str, Any]:
    """The machine the script runs on: the engine does not report the processor model."""
    return {
        "processor": _cpu_model() or platform.processor() or None,
        "platform": platform.platform(),
        "python": platform.python_version(),
        "driver": neo4j.__version__,
    }


def _cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as cpuinfo:
            for line in cpuinfo:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


# --- The measurement ---------------------------------------------------------


def _clear_query_caches_in(tx: Tx) -> None:
    tx.run("CALL db.clearQueryCaches()").consume()


def measure(execute: Execute, starts: dict[str, Sequence[str]] | None = None, rounds: int = ROUNDS) -> dict[str, Any]:
    """Every pattern from every starting node, with the plan cache emptied first
    so the first run of each pattern is cold. ``starts`` overrides the starting
    nodes, by pattern code."""
    execute(_clear_query_caches_in)
    patterns = []
    for pattern in PATTERNS:
        keys = starts[pattern.code] if starts is not None else execute(_keys_in, pattern.starts)
        patterns.append(measure_pattern(execute, pattern, keys, rounds))
    # After the runs: EXPLAIN caches the plan it shows.
    for pattern, measured in zip(PATTERNS, patterns):
        sample = measured["runs"][0]["key"] if measured["runs"] else "none"
        measured["plans"] = [{"grain": grain, **execute(plan_in, query)} for grain, query in pattern.queries(sample)]
    return {
        "measured_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "rounds": rounds,
        "threshold_ms": THRESHOLD_MS,
        "resolution_ms": RESOLUTION_MS,
        "max_depth_bound": MAX_DEPTH,
        "graph": execute(graph_in),
        "engine": execute(engine_in),
        "host": host(),
        "patterns": patterns,
    }


def markdown(report: dict[str, Any]) -> str:
    def cell(value: Any) -> str:
        if value is None:
            return "—"
        if isinstance(value, bool):
            return "yes" if value else "no"
        return f"{value:g}" if isinstance(value, float) else str(value)

    lines = [
        "| Pattern | Starting nodes | Executions | Cold (ms) | Median (ms) | p95 (ms) | Max (ms) | Max depth | Under 1 s |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for p in report["patterns"]:
        lines.append("| " + " | ".join(cell(v) for v in (
            f"{p['pattern']} {p['name']}", p["starting_nodes"], p["executions"], p["cold_ms"],
            p["median_ms"], p["p95_ms"], p["max_ms"], p["max_depth"], p["passes"])) + " |")
    graph, engine = report["graph"], report["engine"]
    memory = f"{engine['memory_bytes'] / 2**30:.1f} GiB" if engine["memory_bytes"] else "memory unknown"
    lines += [
        "",
        f"Graph: {graph['nodes']} nodes, {graph['edges']} edges. Depth bound: {report['max_depth_bound']}.",
        f"Engine: Neo4j {engine['version']} {engine['edition']}, {engine['processors']} processors, {memory}, "
        f"{engine['os']}.",
        f"Host processor: {report['host']['processor']}.",
    ]
    for p in report["patterns"]:
        for plan in p.get("plans", []):
            flagged = plan["unpruned_expansions"] + plan["full_scans"]
            if flagged:
                grain = f" ({plan['grain']})" if plan["grain"] else ""
                lines.append(f"Warning: the plan of {p['pattern']}{grain} has {', '.join(flagged)}.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, help="report file (default: var/measurements/ac05-<date-time>.json)")
    args = parser.parse_args()
    settings = Settings.from_environment()
    output = args.output or Path("var/measurements") / f"ac05-{datetime.now():%Y%m%d-%H%M%S}.json"
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        # A base without institutional data does not know some labels and properties.
        with driver.session(database=settings.neo4j_database,
                            notifications_disabled_categories=[NotificationDisabledCategory.UNRECOGNIZED]) as session:
            report = measure(session.execute_read)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(markdown(report))
    print(f"\nReport written to {output}")
    return 0 if all(p["passes"] for p in report["patterns"]) else 1


if __name__ == "__main__":
    sys.exit(main())
