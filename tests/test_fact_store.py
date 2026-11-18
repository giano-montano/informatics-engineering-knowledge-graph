import pytest

from iekg.core.batch import Batch, EdgeFact, NodeFact
from iekg.fact_store import FactStore, StoredFacts
from iekg.graph_schema import INSTITUTIONAL, PART_OF, PREF_LABEL_ES, TOPIC

BATCH = Batch(
    nodes=(NodeFact("t", TOPIC, {PREF_LABEL_ES: "Búsqueda heurística"}),),
    edges=(EdgeFact(PART_OF, "t", "ku"),),
)


def facts(run_id, batch=BATCH):
    return StoredFacts(run_id, INSTITUTIONAL, "doc", batch)


def test_the_facts_read_back_as_saved(tmp_path):
    store = FactStore(tmp_path / "facts")
    path = store.save(facts(7))
    assert path.name == "run-000007.json"
    assert store.load(7) == facts(7)
    assert list(tmp_path.joinpath("facts").iterdir()) == [path]


def test_the_file_of_a_run_is_never_replaced(tmp_path):
    store = FactStore(tmp_path)
    store.save(facts(1))
    with pytest.raises(FileExistsError):
        store.save(facts(1, Batch()))
    assert store.load(1) == facts(1)
    assert [p.name for p in tmp_path.iterdir()] == ["run-000001.json"]


def test_the_runs_are_listed_in_the_order_they_ran(tmp_path):
    store = FactStore(tmp_path / "facts")
    assert list(store.run_ids()) == []
    for run_id in (10, 2, 33):
        store.save(facts(run_id))
    assert list(store.run_ids()) == [2, 10, 33]
