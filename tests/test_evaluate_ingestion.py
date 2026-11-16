"""The evaluator of the extraction test cases: one negative test per matching
rule of the thesis (5.2.5.4), the fusion measures (5.2.5.5), and the property
that a batch built from the annotation scores 100 %. None needs Neo4j."""

import pytest
from conftest import BACKBONE, ROOT

from evaluate_ingestion import (
    COMPOUND_HEADINGS,
    GOLD,
    REVIEW_DIR,
    Attempt,
    Entry,
    Gold,
    Item,
    ReviewRow,
    UnknownEndpoint,
    agreement,
    closest,
    compare_review,
    compare_reviewers,
    comparison_path,
    comparison_rows,
    evaluate,
    export_review,
    extraction_path,
    fusion,
    items_of,
    load_compound_headings,
    load_gold,
    match,
    measure,
    outside_of,
    most_hits,
    pipeline_against_review,
    pipeline_comparison_path,
    pipeline_comparison_rows,
    read_adjudication,
    read_reference,
    read_review,
    review,
    total,
    write_comparison,
    write_pipeline_comparison,
)

from iekg.core.batch import Batch, EdgeFact, NodeFact
from iekg.graph_schema import (
    CONCEPT,
    COURSE,
    HAS_PREREQUISITE,
    KNOWLEDGE_UNIT,
    PART_OF,
    PREF_LABEL_ES,
    REQUIRES_CONCEPT,
    TOPIC,
)
from iekg.operational_store import COMPLETED, REJECTED


def entry(id, global_id, label, kind="concepto", level="obligatoria", aliases=(), syllabus="S1"):
    return Entry(syllabus, global_id, f"{syllabus}-{id:03d}", kind, level, label, tuple(aliases), "")


def topic(name, key=None):
    return Item(key or f"t:{name}", TOPIC, name)


def concept(name, key=None):
    return Item(key or f"c:{name}", CONCEPT, name)


def consumed(matches):
    return [m.entry.id if m.entry else None for m in matches]


def node(item):
    return NodeFact(item.key, item.label, {PREF_LABEL_ES: item.name})


def batch(*items, edges=()):
    return Batch(tuple(node(item) for item in items), tuple(edges))


def accepted(run_id, syllabus, *items, edges=()):
    return Attempt(run_id, syllabus, True, batch(*items, edges=edges), COMPLETED)


def rejected(run_id, syllabus, *items, readable=True):
    return Attempt(run_id, syllabus, False, batch(*items) if readable else None, REJECTED)


# --- Hit ------------------------------------------------------------------------


def test_an_item_is_a_hit_by_the_label_or_an_alias_after_normalizing():
    gold = Gold((entry(1, "G1", "Árboles B", aliases=["B-trees"]),))
    assert consumed(match([concept("arbol b")], gold, "S1")) == ["S1-001"]
    assert consumed(match([concept("B-Trees")], gold, "S1")) == ["S1-001"]


def test_an_item_with_a_name_the_annotation_does_not_have_is_a_false_positive():
    gold = Gold((entry(1, "G1", "Árboles B"),))
    matches = match([concept("Árboles balanceados")], gold, "S1")
    assert consumed(matches) == [None]
    assert measure(matches, gold, "S1")["precision"] == 0


def test_the_names_of_a_notion_come_from_its_entries_in_every_syllabus():
    gold = Gold((
        entry(1, "G1", "Recursión"),
        entry(1, "G1", "Recursividad", aliases=["algoritmos recursivos"], syllabus="S2"),
    ))
    assert consumed(match([concept("Algoritmo recursivo")], gold, "S1")) == ["S1-001"]


def test_a_notion_without_an_entry_in_the_syllabus_of_the_case_is_not_a_hit():
    gold = Gold((entry(1, "G1", "Recursión"), entry(1, "G2", "Grafos", syllabus="S2")))
    assert consumed(match([concept("Grafos")], gold, "S1")) == [None]


# --- One to one -----------------------------------------------------------------


def test_a_second_item_of_a_notion_with_one_entry_is_a_false_positive():
    gold = Gold((entry(1, "G1", "Recursión", aliases=["recursividad"]),))
    matches = match([concept("Recursión"), concept("Recursividad")], gold, "S1")
    assert consumed(matches) == ["S1-001", None]
    measured = measure(matches, gold, "S1")
    assert (measured["hits"], measured["false_positives"], measured["precision"]) == (1, 1, 0.5)


def test_two_items_of_a_notion_with_two_entries_are_two_hits():
    gold = Gold((entry(1, "G1", "Herencia", kind="tema"), entry(2, "G1", "Herencia")))
    assert consumed(match([concept("Herencia"), topic("Herencia")], gold, "S1")) == ["S1-002", "S1-001"]


# --- Tie-break ------------------------------------------------------------------


def test_the_entry_with_the_label_of_the_item_wins_over_type_and_identifier():
    gold = Gold((
        entry(1, "G1", "Procesos e hilos", kind="tema", aliases=["hilos"]),
        entry(2, "G2", "Hilos"),
    ))
    # By type or by identifier the topic would have taken the first entry.
    assert consumed(match([topic("Hilos")], gold, "S1")) == ["S1-002"]


def test_without_a_label_the_entry_of_the_same_type_wins_over_the_identifier():
    gold = Gold((
        entry(1, "G1", "Procesos e hilos", kind="tema", aliases=["threads"]),
        entry(2, "G2", "Hilos", aliases=["threads"]),
    ))
    # By identifier the concept would have taken the first entry.
    assert consumed(match([concept("Threads")], gold, "S1")) == ["S1-002"]


def test_with_everything_else_equal_the_lowest_identifier_wins():
    # Written in reverse, so the order of the file would choose the other.
    gold = Gold((entry(2, "G2", "Hilos", aliases=["threads"]), entry(1, "G1", "Hebras", aliases=["threads"])))
    assert consumed(match([concept("Threads")], gold, "S1")) == ["S1-001"]


def test_the_order_of_the_batch_decides_and_the_best_order_is_reported():
    gold = Gold((entry(1, "G1", "Hebras", aliases=["threads"]), entry(2, "G2", "Hilos", aliases=["threads"])))
    items = [concept("Threads"), concept("Hebras")]
    matches = match(items, gold, "S1")
    assert consumed(matches) == ["S1-001", None]
    assert most_hits(items, gold, "S1") == 2
    assert measure(matches, gold, "S1")["most_hits"] == 2


# --- Acceptable entries and recall ----------------------------------------------


def test_an_acceptable_entry_extracted_is_a_hit():
    gold = Gold((entry(1, "G1", "Pseudocódigo", level="aceptable"),))
    matches = match([concept("Pseudocódigos")], gold, "S1")
    assert measure(matches, gold, "S1")["precision"] == 1


def test_a_missing_acceptable_entry_does_not_lower_the_recall_and_a_mandatory_one_does():
    gold = Gold((
        entry(1, "G1", "Recursión"),
        entry(2, "G2", "Pseudocódigo", level="aceptable"),
        entry(3, "G3", "Grafos"),
    ))
    without_acceptable = measure(match([concept("Recursión"), concept("Grafos")], gold, "S1"), gold, "S1")
    assert (without_acceptable["mandatory_notions"], without_acceptable["recall"]) == (2, 1)
    without_mandatory = measure(match([concept("Recursión"), concept("Pseudocódigo")], gold, "S1"), gold, "S1")
    assert (without_mandatory["recovered"], without_mandatory["recall"]) == (1, 0.5)
    assert [missed["global_id"] for missed in without_mandatory["missed_notions"]] == ["G3"]


def test_a_notion_is_recovered_through_any_of_its_entries_and_counts_once():
    gold = Gold((entry(1, "G1", "Herencia", kind="tema"), entry(2, "G1", "Herencia", level="aceptable")))
    measured = measure(match([concept("Herencia")], gold, "S1"), gold, "S1")
    assert (measured["mandatory_notions"], measured["recovered"]) == (1, 1)
    both = measure(match([concept("Herencia"), topic("Herencia")], gold, "S1"), gold, "S1")
    assert (both["hits"], both["mandatory_notions"], both["recovered"]) == (2, 1, 1)


def test_f1_combines_precision_and_recall_and_empty_denominators_stay_empty():
    gold = Gold((entry(1, "G1", "Recursión"), entry(2, "G2", "Grafos")))
    measured = measure(match([concept("Recursión"), concept("Pilas")], gold, "S1"), gold, "S1")
    assert (measured["precision"], measured["recall"], measured["f1"]) == (0.5, 0.5, 0.5)
    nothing = measure([], gold, "S1")
    assert (nothing["precision"], nothing["recall"], nothing["f1"], nothing["type_agreement"]) == (None, 0, None, None)


# --- Type -----------------------------------------------------------------------


def test_the_type_does_not_take_part_in_the_match_and_is_reported_apart():
    gold = Gold((entry(1, "G1", "Recursión"), entry(2, "G2", "Grafos")))
    measured = measure(match([topic("Recursión"), concept("Grafos")], gold, "S1"), gold, "S1")
    assert (measured["hits"], measured["precision"]) == (2, 1)
    assert (measured["type_matches"], measured["type_agreement"]) == (1, 0.5)


# --- The items of a batch -------------------------------------------------------


def test_an_existing_node_the_batch_links_is_an_item_with_the_label_of_its_batch():
    known = {"old": (CONCEPT, "Recursión"), "ku": (KNOWLEDGE_UNIT, "Algoritmos")}
    new, course = concept("Grafos", key="new"), Item("course", COURSE, "Algoritmia")
    linking = Batch((node(new), node(course)), (
        EdgeFact(HAS_PREREQUISITE, "new", "old"),
        EdgeFact(REQUIRES_CONCEPT, "course", "old"),
        EdgeFact(PART_OF, "new", "ku"),
    ))
    # Once, though two edges reach it; the course and the knowledge unit are not items.
    assert items_of(linking, known) == [new, Item("old", CONCEPT, "Recursión")]


def test_an_endpoint_in_no_earlier_batch_stops_the_evaluation():
    linking = Batch((node(concept("Grafos", key="new")),), (EdgeFact(HAS_PREREQUISITE, "new", "lost"),))
    with pytest.raises(UnknownEndpoint, match="lost"):
        items_of(linking, {})


# --- The runs -------------------------------------------------------------------

GOLD_OF_TWO = Gold((
    entry(1, "G1", "Recursión"),
    entry(2, "G2", "Grafos"),
    entry(1, "G1", "Recursividad", syllabus="S2"),
    entry(2, "G3", "Pilas", syllabus="S2"),
))


def test_a_chain_measures_the_first_accepted_batch_and_counts_the_rejected_attempts():
    report = evaluate(GOLD_OF_TWO, [
        rejected(1, "S1", concept("Recursión"), concept("Colas")),
        rejected(2, "S1", readable=False),
        accepted(3, "S1", concept("Recursión", key="r"), concept("Grafos")),
        accepted(4, "S1", concept("Recursión", key="again")),
        accepted(5, "S2", concept("Pilas", key="p"), edges=[EdgeFact(HAS_PREREQUISITE, "p", "r")]),
    ], {})
    first, second = report["cases"]
    assert (first["case"], first["run_id"], first["attempts"], first["precision"]) == ("CP-01", 3, 3, 1)
    # The linked node counts in the second case, by the label its own batch gave it.
    assert (second["case"], second["attempts"], second["items"], second["hits"]) == ("CP-02", 1, 2, 2)
    assert [(r["run_id"], r["readable"], r.get("precision")) for r in report["rejected_attempts"]] == [
        (1, True, 0.5), (2, False, None)]
    assert report["totals"]["all"]["items"] == 4
    assert any("run 4" in warning for warning in report["warnings"])
    assert report["passes"] is True


def test_a_syllabus_rejected_every_time_adds_its_mandatory_notions_to_the_total_recall():
    report = evaluate(GOLD_OF_TWO, [
        accepted(1, "S1", concept("Recursión"), concept("Grafos")),
        rejected(2, "S2", concept("Pilas")),
    ], {})
    out = report["cases"][1]
    assert (out["accepted"], out["attempts"], out["items"], out["mandatory_notions"]) == (False, 1, 0, 2)
    assert (report["totals"]["all"]["precision"], report["totals"]["all"]["recall"]) == (1, 0.5)


def test_there_is_no_verdict_while_a_test_case_has_no_run():
    report = evaluate(GOLD_OF_TWO, [accepted(1, "S1", concept("Recursión"))], {})
    assert report["passes"] is None
    assert report["not_run"] == ["S2"]
    assert report["totals"]["all"]["mandatory_notions"] == 2


def test_the_verdict_fails_under_the_threshold():
    report = evaluate(GOLD_OF_TWO, [
        accepted(1, "S1", concept("Recursión"), concept("Colas")),
        accepted(2, "S2", concept("Pilas"), concept("Montículos")),
    ], {})
    assert (report["totals"]["all"]["precision"], report["passes"]) == (0.5, False)


def test_the_totals_are_sums_and_the_held_out_cases_are_reported_apart():
    report = evaluate(GOLD_OF_TWO, [
        accepted(1, "S1", concept("Recursión"), concept("Grafos"), concept("Colas"), concept("Listas")),
        accepted(2, "S2", concept("Pilas")),
    ], {}, held_out=("S2",))
    totals = report["totals"]
    # 3 hits of 5 items: not the mean of 50 % and 100 %.
    assert totals["all"]["precision"] == 0.6
    assert (totals["tuning"]["cases"], totals["tuning"]["precision"]) == (1, 0.5)
    assert (totals["held_out"]["cases"], totals["held_out"]["precision"]) == (1, 1)
    assert total([])["precision"] is None


def test_hiding_the_held_out_cases_leaves_no_figure_of_theirs():
    report = evaluate(GOLD_OF_TWO, [
        accepted(1, "S1", concept("Recursión", key="r")),
        rejected(2, "S2", concept("Pilas")),
        accepted(3, "S2", concept("Pilas"), concept("Montículos")),
    ], {}, held_out=("S2",), hide_held_out=True)
    assert [case["syllabus"] for case in report["cases"]] == ["S1"]
    assert report["rejected_attempts"] == []
    assert report["totals"]["all"] == report["totals"]["tuning"]
    assert report["totals"]["held_out"]["cases"] == 0
    assert (report["hidden"], report["passes"], report["fusion"]) == (["S2"], None, None)


def test_an_isolated_run_sees_the_reference_layer_alone():
    reference = {"ku": (KNOWLEDGE_UNIT, "Algoritmos")}
    alone = accepted(2, "S2", concept("Pilas", key="p"), edges=[EdgeFact(PART_OF, "p", "ku")])
    report = evaluate(GOLD_OF_TWO, [
        accepted(1, "S1", concept("Recursión", key="r")),
        accepted(3, "S1", concept("Recursión", key="r2"), concept("Grafos")),
        alone,
    ], reference, isolated=True)
    # Every accepted run is measured; the total takes the last of each syllabus.
    assert [(c["run_id"], c["attempts"], c["hits"]) for c in report["cases"]] == [(1, None, 1), (2, None, 1), (3, None, 2)]
    assert report["totals"]["all"]["hits"] == 3
    assert (report["mode"], report["passes"], report["fusion"]) == ("isolated", None, None)

    chained = accepted(4, "S2", concept("Pilas", key="p"), edges=[EdgeFact(HAS_PREREQUISITE, "p", "r")])
    with pytest.raises(UnknownEndpoint):
        evaluate(GOLD_OF_TWO, [accepted(1, "S1", concept("Recursión", key="r")), chained], reference, isolated=True)


# --- Fusion ---------------------------------------------------------------------


def hit(item, global_id, id=1):
    return match([item], Gold((entry(id, global_id, item.name),)), "S1")


def test_two_nodes_of_the_same_type_with_one_notion_are_a_duplicate():
    measured = fusion([hit(concept("Recursión", key="a"), "G1"), hit(concept("Recursión", key="b"), "G1"),
                       hit(concept("Recursión", key="c"), "G1")])
    assert (measured["duplicated_notions"], measured["surplus_nodes"], measured["split_notions"]) == (1, 2, 0)


def test_two_nodes_of_different_type_with_one_notion_are_a_split_notion_not_a_duplicate():
    measured = fusion([hit(topic("Recursión", key="a"), "G1"), hit(concept("Recursión", key="b"), "G1")])
    assert (measured["duplicated_notions"], measured["split_notions"], measured["wrong_fusions"]) == (0, 1, 0)


def test_a_node_with_two_notions_is_a_wrong_fusion():
    measured = fusion([hit(concept("Relaciones", key="a"), "G1"), hit(concept("Relaciones", key="a"), "G2")])
    assert (measured["wrong_fusions"], measured["excepted_fusions"]) == (1, 0)
    assert measured["wrong"][0]["global_ids"] == ["G1", "G2"]


def test_a_node_seen_twice_with_the_same_notion_is_none_of_the_three():
    measured = fusion([hit(concept("Recursión", key="a"), "G1"), hit(concept("Recursión", key="a"), "G1")])
    assert (measured["nodes_with_hits"], measured["duplicated_notions"], measured["wrong_fusions"]) == (1, 0, 0)


def test_a_compound_heading_and_one_of_its_parts_on_a_node_are_excepted():
    matched = [hit(concept("Pruebas", key="a"), "G1"), hit(concept("Pruebas", key="a"), "G-heading")]
    measured = fusion(matched, frozenset({"G-heading"}))
    assert (measured["wrong_fusions"], measured["excepted_fusions"]) == (0, 1)


def test_the_exception_needs_exactly_one_notion_left():
    two_left = [hit(concept("Pruebas", key="a"), g) for g in ("G1", "G2", "G-heading")]
    assert fusion(two_left, frozenset({"G-heading"}))["wrong_fusions"] == 1
    none_left = [hit(concept("Pruebas", key="a"), g) for g in ("G-heading", "G-other-heading")]
    assert fusion(none_left, frozenset({"G-heading", "G-other-heading"}))["wrong_fusions"] == 1


def test_the_chain_reports_the_fusion_with_the_compound_headings_of_the_annotation():
    gold = Gold((
        entry(1, "G1", "Verificación y validación", kind="tema", aliases=["validación"]),
        entry(1, "G2", "Validación", syllabus="S2"),
    ))
    report = evaluate(gold, [
        accepted(1, "S1", concept("Validación", key="v")),
        accepted(2, "S2", concept("Pilas", key="p"), edges=[EdgeFact(HAS_PREREQUISITE, "p", "v")]),
    ], {}, compound_headings=frozenset({"S1-001"}))
    assert (report["fusion"]["wrong_fusions"], report["fusion"]["excepted_fusions"]) == (0, 1)


# --- The reviewer's extraction --------------------------------------------------

GOLD_REVIEWED = Gold((
    entry(1, "G1", "Recursión", aliases=["recursividad"]),
    entry(2, "G2", "Grafos", level="aceptable"),
    entry(3, "G3", "Pilas", kind="tema"),
    entry(4, "G3", "Pilas"),
    entry(5, "G4", "Montículos", level="aceptable"),
))
REVIEWED = [ReviewRow("Recursividad", "tema"), ReviewRow("recursividad", "concepto"), ReviewRow("Grafos", "Concepto"),
            ReviewRow("Colas", "tema", "colas y pilas", "dudoso"), ReviewRow("Stacks", "tema")]


def adjudicated(side, name, category, global_id="", notion="", missing_alias=""):
    return {"lado": side, "nombre": name, "id_global": global_id, "categoria": category, "nocion": notion,
            "alias_faltante": missing_alias}


def test_the_reviewer_and_the_annotation_are_compared_both_ways_by_name():
    compared = compare_review(GOLD_REVIEWED, "S1", REVIEWED)
    # Rows that normalize alike count once.
    assert (compared["reviewer_rows"], compared["repeated_rows"]) == (5, 1)
    assert compared["reviewer_registered"] == {"count": 2, "of": 4, "proportion": 0.5}
    # By notion and without level: the two entries of G3 are one notion.
    assert compared["notions_extracted"] == {"count": 2, "of": 4, "proportion": 0.5}
    assert [d["name"] for d in compared["reviewer_only"]] == ["Colas", "Stacks"]
    assert compared["reviewer_only"][0] == {"name": "Colas", "text": "colas y pilas", "comment": "dudoso"}
    assert [(d["global_id"], d["level"]) for d in compared["annotation_only"]] == [
        ("G3", "obligatoria"), ("G4", "aceptable")]
    assert compared["adjudicated"] is None


def test_the_notions_the_reviewer_extracted_are_split_by_level():
    compared = compare_review(GOLD_REVIEWED, "S1", REVIEWED)
    assert (compared["mandatory_extracted"]["count"], compared["mandatory_extracted"]["of"]) == (1, 2)
    assert (compared["acceptable_extracted"]["count"], compared["acceptable_extracted"]["of"]) == (1, 2)


def test_the_type_the_reviewer_wrote_is_compared_on_the_matched_pairs_only():
    # "Recursividad" as a topic against a concept entry; "Grafos" agrees; the unmatched rows do not count.
    assert compare_review(GOLD_REVIEWED, "S1", REVIEWED)["type_agreement"] == {"count": 1, "of": 2, "proportion": 0.5}
    untyped = compare_review(GOLD_REVIEWED, "S1", [ReviewRow("Grafos")])
    assert untyped["type_agreement"]["of"] == 0


def test_the_adjudication_adds_the_pairs_the_author_made_and_counts_each_category():
    compared = compare_review(GOLD_REVIEWED, "S1", REVIEWED, [
        adjudicated("revisor", "Stacks", "misma_nocion", notion="G3", missing_alias="sí"),
        adjudicated("revisor", "Colas", "omision"),
        adjudicated("anotacion", "Montículos", "no_extraida", global_id="G4"),
    ])
    after = compared["adjudicated"]
    assert after["reviewer_registered"] == {"count": 3, "of": 4, "proportion": 0.75}
    assert after["notions_extracted"] == {"count": 3, "of": 4, "proportion": 0.75}
    assert after["categories"]["revisor"] == {"misma_nocion": 1, "omision": 1, "criterio": 0, "no_sustentada": 0}
    # G3 was paired through the reviewer's row: it needs no line of its own.
    assert after["categories"]["anotacion"] == {
        "misma_nocion": 1, "no_extraida": 1, "inclusion_indebida": 0, "criterio": 0}
    assert (after["missing_aliases"], after["pending"]) == (1, 0)
    # The automatic figures stay as they were.
    assert compared["reviewer_registered"]["count"] == 2


def test_a_discrepancy_without_a_category_is_pending():
    compared = compare_review(GOLD_REVIEWED, "S1", REVIEWED, [adjudicated("revisor", "Colas", "criterio")])
    assert compared["adjudicated"]["pending"] == 3


@pytest.mark.parametrize("line, message", [
    (adjudicated("revisor", "Colas", "no_extraida"), "category"),
    (adjudicated("anotacion", "Montículos", "omision", global_id="G4"), "category"),
    (adjudicated("revisor", "Stacks", "misma_nocion", notion="G9"), "not a notion"),
    (adjudicated("pipeline", "Stacks", "criterio"), "side"),
])
def test_an_adjudication_outside_the_protocol_is_refused(line, message):
    with pytest.raises(ValueError, match=message):
        compare_review(GOLD_REVIEWED, "S1", REVIEWED, [line])


def test_the_pipeline_is_compared_with_the_reviewer_without_type_nor_one_to_one():
    rows = [ReviewRow("Pilas"), ReviewRow("Recursión")]
    items = [topic("Pilas"), concept("Pilas"), concept("Recursividad", key="r"), concept("Colas", key="q")]
    compared = pipeline_against_review(items, rows)
    # No aliases on the reviewer's side: "Recursividad" does not reach "Recursión".
    assert compared["pipeline_registered"] == {"count": 2, "of": 4, "proportion": 0.5}
    assert [item["name"] for item in compared["pipeline_only"]] == ["Recursividad", "Colas"]

    paired = pipeline_against_review(items, rows, [
        {"clave": "r", "fila_del_revisor": "Recursión"}, {"clave": "q", "fila_del_revisor": ""}])
    assert paired["adjudicated"]["pipeline_registered"] == {"count": 3, "of": 4, "proportion": 0.75}
    with pytest.raises(ValueError, match="not a row of the reviewer"):
        pipeline_against_review(items, rows, [{"clave": "q", "fila_del_revisor": "Filas"}])


def test_the_workbook_is_exported_once_and_the_files_to_adjudicate_come_back_as_written(tmp_path):
    from openpyxl import Workbook

    workbook = Workbook()
    workbook.active.title = "Consigna"
    sheet = workbook.create_sheet("S1")
    sheet.append(["Tiempo (min):", None, "S1"])
    sheet.append([])
    sheet.append(["N°", "Tema o concepto", "Tipo", "Texto del sílabo", "Página", "Comentario"])
    sheet.append([1, "Recursión ", "concepto", "recursión\ny grafos", 2, None])
    sheet.append([2, None, None, None, None, None])
    sheet.append([3, "Colas", "tema", None, 3, "no estoy\tseguro"])
    workbook.save(tmp_path / "filled.xlsx")

    (path,) = export_review(tmp_path / "filled.xlsx", tmp_path, GOLD_REVIEWED.syllabi)
    assert path == extraction_path(tmp_path, "S1")
    assert path.read_text(encoding="utf-8").split("\n")[:2] == [
        "N°\tTema o concepto\tTipo\tTexto del sílabo\tPágina\tComentario", "1\tRecursión\tconcepto\trecursión y grafos\t2\t"]
    rows_of = read_review(tmp_path, GOLD_REVIEWED.syllabi)
    assert rows_of == {"S1": [ReviewRow("Recursión", "concepto", "recursión y grafos"),
                              ReviewRow("Colas", "tema", "", "no estoy seguro")]}
    # The reviewer's rows are never written over.
    with pytest.raises(FileExistsError):
        export_review(tmp_path / "filled.xlsx", tmp_path, GOLD_REVIEWED.syllabi)

    report = review(GOLD_REVIEWED, rows_of, [accepted(1, "S1", concept("Recursión"), concept("Grafos", key="g"))], {})
    (compared,) = report["syllabi"]
    write_comparison(comparison_path(tmp_path, "S1"), GOLD_REVIEWED, compared)
    lines = read_adjudication(comparison_path(tmp_path, "S1"))
    assert [(line["lado"], line["nombre"], line["id_global"]) for line in lines] == [
        ("revisor", "Colas", ""), ("anotacion", "Grafos", "G2"), ("anotacion", "Pilas", "G3"),
        ("anotacion", "Montículos", "G4")]
    assert compare_review(GOLD_REVIEWED, "S1", rows_of["S1"], lines)["adjudicated"]["pending"] == 4
    # The author's work is never written over.
    with pytest.raises(FileExistsError):
        write_comparison(comparison_path(tmp_path, "S1"), GOLD_REVIEWED, compared)
    assert pipeline_comparison_rows(compared["pipeline"], rows_of["S1"]) == [["g", CONCEPT, "Grafos", "", "", ""]]


def test_the_review_totals_wait_for_what_every_syllabus_has():
    rows_of = {"S1": REVIEWED}
    without = review(GOLD_REVIEWED, rows_of)
    assert without["syllabi"][0]["pipeline"] is None
    assert without["totals"]["pipeline_registered"] is None
    assert without["totals"]["adjudicated"]["reviewer_registered"] is None
    assert without["totals"]["reviewer_registered"]["proportion"] == 0.5

    report = review(GOLD_REVIEWED, rows_of, [accepted(1, "S1", concept("Recursividad"), concept("Listas"))], {},
                    {"S1": [adjudicated("revisor", "Stacks", "misma_nocion", notion="G3")]}, {"S1": []})
    assert report["totals"]["pipeline_registered"] == {"count": 1, "of": 2, "proportion": 0.5}
    assert report["totals"]["adjudicated"]["reviewer_registered"]["count"] == 3
    assert report["totals"]["adjudicated"]["pipeline_registered"]["count"] == 1


def test_the_empty_sheet_of_the_repository_exports_no_rows(tmp_path):
    syllabi = load_gold(ROOT / GOLD).syllabi
    written = export_review(ROOT / REVIEW_DIR / "hoja-de-extraccion.xlsx", tmp_path, syllabi)
    assert {path.name for path in written} == {"extraccion_1INF27.tsv", "extraccion_1INF37.tsv"}
    assert read_review(tmp_path, syllabi) == {"1INF27": [], "1INF37": []}


# --- The annotation of the repository -------------------------------------------


@pytest.fixture(scope="module")
def gold():
    return load_gold(ROOT / GOLD)


def test_the_consolidated_annotation_holds_the_entries_of_the_thirteen_case_files(gold):
    assert (len(gold.entries), len(gold.names), len(gold.syllabi)) == (745, 664, 13)
    for syllabus in gold.syllabi:
        (path,) = (ROOT / GOLD).parent.glob(f"{gold.case_of(syllabus)}-gold_{syllabus}.tsv")
        lines = path.read_text(encoding="utf-8").rstrip("\n").split("\n")[2:]
        in_file = [tuple(line.split("\t")[:5]) for line in lines]
        consolidated = [(e.id, e.kind, e.level, e.label, "|".join(e.aliases)) for e in gold.entries_of(syllabus)]
        assert [row[:4] for row in in_file] == [row[:4] for row in consolidated], syllabus
        assert [tuple(a for a in row[4].split("|") if a.strip()) for row in in_file] == [
            e.aliases for e in gold.entries_of(syllabus)], syllabus


def test_the_compound_headings_are_read_from_the_script_that_assigned_the_identifiers(gold):
    compound = load_compound_headings(ROOT / COMPOUND_HEADINGS)
    kinds = {e.id: e.kind for e in gold.entries}
    assert len(compound) == 27
    assert {kinds[entry_id] for entry_id in compound} == {"tema"}


def test_a_batch_built_from_the_labels_of_the_annotation_scores_a_hundred_percent(gold):
    label_of = {kind: label for label, kind in {TOPIC: "tema", CONCEPT: "concepto"}.items()}
    attempts = [
        Attempt(number, syllabus, True, Batch(tuple(
            NodeFact(e.id, label_of[e.kind], {PREF_LABEL_ES: e.label}) for e in gold.entries_of(syllabus))), COMPLETED)
        for number, syllabus in enumerate(gold.syllabi, start=1)
    ]
    report = evaluate(gold, attempts, read_reference(BACKBONE),
                      compound_headings=load_compound_headings(ROOT / COMPOUND_HEADINGS))
    for case in report["cases"]:
        assert (case["precision"], case["recall"], case["f1"], case["type_agreement"]) == (1, 1, 1, 1), case["case"]
        assert case["most_hits"] == case["hits"] == len(gold.entries_of(case["syllabus"]))
    everything = report["totals"]["all"]
    assert (everything["items"], everything["hits"], everything["precision"], everything["recall"]) == (745, 745, 1, 1)
    assert report["totals"]["held_out"]["items"] == 39 + 89
    assert report["passes"] is True
    # One node per entry: nothing was merged, so no node holds two notions.
    assert report["fusion"]["wrong_fusions"] == 0


def test_the_candidates_are_the_most_alike_names_and_never_the_unlike_ones():
    options = {"G1 · Pilas": {"pila"}, "G2 · Pila de llamadas": {"pila de llamada"}, "G3 · Grafos": {"grafo"}}
    assert closest("Pilas", options) == ["G1 · Pilas", "G2 · Pila de llamadas"]
    assert closest("Montículos", options) == []


def test_the_comparison_workbook_offers_the_categories_of_each_side_and_the_notions_of_the_syllabus(tmp_path):
    from openpyxl import load_workbook

    compared = compare_review(GOLD_REVIEWED, "S1", REVIEWED)
    path = comparison_path(tmp_path, "S1")
    write_comparison(path, GOLD_REVIEWED, compared)
    workbook = load_workbook(path)
    sheet = workbook["Adjudicación"]
    lists = {str(v.sqref): v.formula1 for v in sheet.data_validations.dataValidation}
    # Two rows of the reviewer (2-3), then two notions (4-5); categoria is column H.
    assert lists["H2:H3"] == '"misma_nocion,omision,criterio,no_sustentada"'
    assert lists["H4:H5"] == '"misma_nocion,no_extraida,inclusion_indebida,criterio"'
    assert lists["I2:I5"] == "'Nociones'!$A$2:$A$5"
    assert [row[0] for row in workbook["Nociones"].iter_rows(min_row=2, values_only=True)] == [
        "G1 · Recursión", "G2 · Grafos", "G3 · Pilas", "G4 · Montículos"]

    # The author's pick from the list counts as the identifier of the notion.
    line = {"lado": "revisor", "nombre": "Stacks", "categoria": "misma_nocion", "nocion": "G3 · Pilas"}
    assert compare_review(GOLD_REVIEWED, "S1", REVIEWED, [line])["adjudicated"]["notions_extracted"]["count"] == 3


def test_the_pipeline_workbook_offers_the_rows_of_the_reviewer(tmp_path):
    from openpyxl import load_workbook

    rows = [ReviewRow("Pilas"), ReviewRow("pilas"), ReviewRow("Recursión")]
    compared = pipeline_against_review([concept("Recursividad", key="r")], rows)
    path = pipeline_comparison_path(tmp_path, "S1")
    write_pipeline_comparison(path, compared, rows)
    assert [row[0] for row in load_workbook(path)["Filas del revisor"].iter_rows(min_row=2, values_only=True)] == [
        "Pilas", "pilas", "Recursión"]
    (line,) = read_adjudication(path)
    assert (line["clave"], line["candidatos"], line["fila_del_revisor"]) == ("r", "Recursión", "")


def test_two_reviewers_are_compared_both_ways_by_normalized_name():
    first = [ReviewRow("Pilas"), ReviewRow("pila"), ReviewRow("Colas"), ReviewRow("Grafos")]
    second = [ReviewRow("Grafos "), ReviewRow("Recursión")]
    compared = compare_reviewers(first, second)
    # "Pilas" and "pila" are one name.
    assert (compared["names"], compared["other_names"], compared["shared"]) == (3, 2, 1)
    assert compared["other_has"] == {"count": 1, "of": 3, "proportion": 1 / 3}
    assert compared["has_of_other"] == {"count": 1, "of": 2, "proportion": 0.5}

    report = agreement({"S1": first, "S2": second}, {"S1": second, "S2": second})
    assert [s["syllabus"] for s in report["syllabi"]] == ["S1", "S2"]
    assert report["totals"]["other_has"] == {"count": 3, "of": 5, "proportion": 0.6}


# --- Diagnostic: the items a batch does not place ---------------------------------


def test_a_concept_the_batch_only_requires_or_relates_is_set_apart_in_the_placed_precision():
    gold = Gold([entry(1, "G-1", "Grafos")])
    known = {"old": (CONCEPT, "Recursión"), "other": (CONCEPT, "Pilas"), "ku": (KNOWLEDGE_UNIT, "Algoritmos")}
    new, course = concept("Grafos", key="new"), Item("course", COURSE, "Algoritmia")
    linking = Batch((node(new), node(course)), (
        EdgeFact(PART_OF, "new", "ku"),
        EdgeFact(REQUIRES_CONCEPT, "course", "old"),
        EdgeFact(HAS_PREREQUISITE, "new", "other"),
    ))
    assert outside_of(linking) >= {"old", "other"} and "new" not in outside_of(linking)
    measured = measure(match(items_of(linking, known), gold, "S1"), gold, "S1", outside_of(linking))
    # The indicator counts the three items; the diagnostic, the one the syllabus places.
    assert (measured["items"], measured["hits"], measured["outside_items"], measured["outside_hits"]) == (3, 1, 2, 0)
    assert measured["precision"] == pytest.approx(1 / 3) and measured["placed_precision"] == 1.0
