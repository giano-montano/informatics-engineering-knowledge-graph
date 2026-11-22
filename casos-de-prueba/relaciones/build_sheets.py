"""Builds the sheets for the manual judgment of CP-15 and CP-16 from the final graph.

CP-15: every PART_OF edge from a topic to a CS2023 knowledge unit, ordered by
(topic key, unit key).
CP-16: per type, the edges are ordered by key, numbered from 0, and
``random.Random(seed).sample(range(N), 30)`` picks the indices; all of them if N <= 30.
Prerequisite and specialization are ordered by (source key, target key); the required
concept, by (course code, concept key). The sample depends only on the graph and the seed.

    uv run python casos-de-prueba/relaciones/build_sheets.py --seed 20261116
"""

import argparse
import random
from pathlib import Path

from neo4j import GraphDatabase
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

from iekg.settings import Settings

SAMPLE = 30
HERE = Path(__file__).parent

CP15 = """
MATCH (t:Topic)-[r:PART_OF]->(u:KnowledgeUnit)-[:PART_OF]->(a:KnowledgeArea)
OPTIONAL MATCH (lr:LearningResource {key: r.provenance})
RETURN t.key AS source, u.key AS target, t.prefLabelEs AS topic,
       [(t)-[:WAS_DERIVED_FROM]->(:LearningResource)-[:IS_ABOUT]->(c:Course) | c.courseCode] AS courses,
       [(c:Concept)-[:PART_OF]->(t) | c.prefLabelEs] AS concepts,
       split(u.key, '#')[1] AS unit_code, u.prefLabelEs AS unit, u.prefLabelEn AS unit_en,
       a.prefLabelEn AS area, lr.prefLabelEs AS syllabus
ORDER BY source, target
"""

BETWEEN_CONCEPTS = """
MATCH (s:Concept)-[r:%s]->(d:Concept)
OPTIONAL MATCH (lr:LearningResource {key: r.provenance})
RETURN s.key AS source, d.key AS target, s.prefLabelEs AS source_name, d.prefLabelEs AS target_name,
       [(s)-[:PART_OF]->(t:Topic) | t.prefLabelEs] AS s_topics,
       [(c:Course)-[:TEACHES_CONCEPT]->(s) | c.courseCode] AS s_courses,
       [(d)-[:PART_OF]->(t:Topic) | t.prefLabelEs] AS d_topics,
       [(c:Course)-[:TEACHES_CONCEPT]->(d) | c.courseCode] AS d_courses,
       lr.prefLabelEs AS syllabus
ORDER BY source, target
"""

REQUIRED = """
MATCH (c:Course)-[:REQUIRES_CONCEPT]->(x:Concept)
RETURN c.key AS source, x.key AS target, c.courseCode AS course, c.prefLabelEs AS course_name,
       x.prefLabelEs AS concept,
       [(x)-[:PART_OF]->(t:Topic) | t.prefLabelEs] AS topics,
       [(o:Course)-[:TEACHES_CONCEPT]->(x) | o.courseCode] AS taught_by,
       EXISTS { (c)-[:TEACHES_CONCEPT]->(x) } AS also_taught
ORDER BY course, target
"""

CONCEPT_TYPES = (
    ("CP-16 prerrequisito", "HAS_PREREQUISITE", "comprender el origen exige conocer el destino"),
    ("CP-16 especialización", "SPECIALIZES", "el origen es un tipo del destino"),
)


def joined(values) -> str:
    return "; ".join(sorted({str(v) for v in values if v}))


def pick(records: list, seed: int) -> list[tuple[int, object]]:
    """The sampled edges with their index in the ordered list."""
    if len(records) <= SAMPLE:
        return list(enumerate(records))
    return [(i, records[i]) for i in sorted(random.Random(seed).sample(range(len(records)), SAMPLE))]


def sheet(book: Workbook, title: str, note: str, header: list[str], rows: list[list]) -> None:
    page = book.create_sheet(title)
    page.append([note])
    page.append(header)
    for cell in page[2]:
        cell.font = Font(bold=True)
    for row in rows:
        page.append(row)
    for column in page.columns:
        page.column_dimensions[column[0].column_letter].width = 30
    for row in page.iter_rows(min_row=3):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")
    page.freeze_panes = "A3"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, required=True, help="the seed written in the relations guide")
    seed = parser.parse_args().seed
    target = HERE / f"juicio-de-relaciones-semilla-{seed}.xlsx"
    if target.exists():
        raise SystemExit(f"{target} already exists; it is written once so that judgments are not lost")
    settings = Settings.from_environment()
    book = Workbook()
    book.remove(book.active)
    summary = []
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)) as driver:
        def ask(query: str) -> list:
            return driver.execute_query(query, database_=settings.neo4j_database)[0]

        records = ask(CP15)
        rows = [[i, joined(r["courses"]), r["topic"], joined(r["concepts"]), r["unit_code"], r["unit"], r["unit_en"],
                 r["area"], r["syllabus"], "", "", "", "", r["source"], r["target"]] for i, r in enumerate(records)]
        sheet(book, "CP-15", f"Todas las aristas PART_OF de un tema a una unidad de CS2023: {len(rows)}. Juicio: "
              "correcta, aceptable o incorrecta. Los tópicos de la unidad se consultan en el documento CS2023.",
              ["i", "curso", "tema", "conceptos del tema", "unidad", "unidad (es)", "unidad (en)", "área", "sílabo",
               "juicio", "unidad_mejor", "topico_cs2023", "motivo", "clave del tema", "clave de la unidad"], rows)
        summary.append(("CP-15", len(rows), len(rows), "todas"))

        for title, edge_type, criterion in CONCEPT_TYPES:
            records = ask(BETWEEN_CONCEPTS % edge_type)
            chosen = pick(records, seed)
            rows = [[i, r["source_name"], joined(r["s_topics"]), joined(r["s_courses"]), r["target_name"],
                     joined(r["d_topics"]), joined(r["d_courses"]), r["syllabus"], "", "", r["source"], r["target"]]
                    for i, r in chosen]
            sheet(book, title, f"{edge_type}: {len(chosen)} de {len(records)} aristas, semilla {seed}. Correcta si "
                  f"{criterion}. Juicio: correcta o incorrecta; motivo obligatorio si es incorrecta.",
                  ["i", "origen", "temas del origen", "cursos que enseñan el origen", "destino", "temas del destino",
                   "cursos que enseñan el destino", "sílabo", "juicio", "motivo", "clave del origen",
                   "clave del destino"], rows)
            summary.append((title, len(chosen), len(records), [i for i, _ in chosen]))

        records = ask(REQUIRED)
        chosen = pick(records, seed)
        rows = [[i, r["course"], r["course_name"], r["concept"], joined(r["topics"]), joined(r["taught_by"]),
                 "sí" if r["also_taught"] else "no", "", "", r["source"], r["target"]] for i, r in chosen]
        sheet(book, "CP-16 concepto requerido", f"REQUIRES_CONCEPT: {len(chosen)} de {len(records)} aristas, semilla "
              f"{seed}. Correcta si el curso necesita el concepto como entrada y no lo enseña. Juicio: correcta o "
              "incorrecta; motivo obligatorio si es incorrecta.",
              ["i", "curso", "nombre del curso", "concepto", "temas del concepto", "lo enseñan",
               "el curso también lo enseña", "juicio", "motivo", "clave del curso", "clave del concepto"], rows)
        summary.append(("CP-16 concepto requerido", len(chosen), len(records), [i for i, _ in chosen]))

    page = book.create_sheet("Muestra", 0)
    page.append(["hoja", "juzgadas", "N en el grafo", "semilla", "índices (desde 0, en el orden de la consulta)"])
    for title, chosen, total, indices in summary:
        page.append([title, chosen, total, seed, str(indices)])
    book.save(target)
    for title, chosen, total, indices in summary:
        print(f"{title}: {chosen} of {total}; indices {indices}")
    print(f"Written {target}")


if __name__ == "__main__":
    main()
