"""Prueba negativa de las consultas de integridad.

Que una consulta no encuentre violaciones en datos limpios no demuestra nada.
Aqui se inyecta a proposito cada tipo de violacion y se exige que la consulta
correspondiente la encuentre.

Cada prueba corre dentro de una transaccion que se revierte al terminar, asi
que la violacion nunca llega a persistir y el backbone queda intacto. Esa es
la razon de usar transacciones explicitas en vez de crear y borrar.
"""

from __future__ import annotations

import pytest
from neo4j.exceptions import Neo4jError

from iekg import integridad, reglas
from iekg.db import BASE, driver


@pytest.fixture(scope="module")
def espec():
    return reglas.cargar()


@pytest.fixture(scope="module")
def consultas(espec):
    return {rid: cypher.rstrip().rstrip(";") for rid, cypher in integridad.compilar(espec)}


@pytest.fixture
def tx():
    d = driver()
    with d.session(database=BASE) as s:
        t = s.begin_transaction()
        try:
            yield t
        finally:
            t.rollback()      # la violacion inyectada nunca se persiste
    d.close()


def entidades(tx, consultas, regla_id) -> set[str]:
    return {f["entidad"] for f in tx.run(consultas[regla_id])}


# ---------------------------------------------------------------------------
# Control positivo: sin inyectar nada, ninguna regla debe disparar
# ---------------------------------------------------------------------------

def test_backbone_limpio_no_viola_ninguna_regla(tx, consultas):
    disparadas = {rid for rid in consultas if list(tx.run(consultas[rid]))}
    assert disparadas == set()


# ---------------------------------------------------------------------------
# etiquetas_disjuntas
# ---------------------------------------------------------------------------

def test_detecta_dos_etiquetas_disjuntas(tx, consultas):
    tx.run("CREATE (:KnowledgeElement:Topic:Concept {iri:'urn:test:doble'})")
    assert "urn:test:doble" in entidades(tx, consultas, "ke-subtipos-disjuntos")


def test_detecta_knowledge_element_sin_subtipo(tx, consultas):
    tx.run("CREATE (:KnowledgeElement {iri:'urn:test:huerfano'})")
    assert "urn:test:huerfano" in entidades(tx, consultas, "ke-subtipos-disjuntos")


def test_detecta_tipos_raiz_solapados(tx, consultas):
    tx.run("CREATE (:KnowledgeElement:Topic:LearningResource {iri:'urn:test:raiz'})")
    assert "urn:test:raiz" in entidades(tx, consultas, "tipos-raiz-disjuntos")


# ---------------------------------------------------------------------------
# relacion_funcional
# ---------------------------------------------------------------------------

def test_detecta_unidad_con_dos_areas(tx, consultas):
    tx.run(
        "CREATE (ku:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku2'}) "
        "CREATE (a:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka1'}) "
        "CREATE (b:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka2'}) "
        "CREATE (ku)-[:PART_OF]->(a) CREATE (ku)-[:PART_OF]->(b)"
    )
    assert "urn:test:ku2" in entidades(tx, consultas, "ku-en-una-sola-ka")


def test_detecta_unidad_sin_area(tx, consultas):
    tx.run("CREATE (:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku0'})")
    assert "urn:test:ku0" in entidades(tx, consultas, "ku-en-una-sola-ka")


# ---------------------------------------------------------------------------
# dominio_rango
# ---------------------------------------------------------------------------

def test_detecta_part_of_entre_par_no_permitido(tx, consultas):
    tx.run(
        "CREATE (c:KnowledgeElement:Concept {iri:'urn:test:c'}) "
        "CREATE (k:KnowledgeElement:KnowledgeArea {iri:'urn:test:ka3'}) "
        "CREATE (c)-[:PART_OF]->(k)"          # Concept -> KnowledgeArea: salta un nivel
    )
    assert "urn:test:c -> urn:test:ka3" in entidades(tx, consultas, "part-of-pares")


def test_detecta_derivacion_fuera_de_rango(tx, consultas):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku3'}) "
        "CREATE (b:KnowledgeElement:Concept {iri:'urn:test:c2'}) "
        "CREATE (a)-[:WAS_DERIVED_FROM]->(b)"  # el destino no es :LearningResource
    )
    assert "urn:test:ku3 -> urn:test:c2" in entidades(tx, consultas, "derivado-de-recurso")


def test_detecta_prerrequisito_entre_no_conceptos(tx, consultas):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku4'}) "
        "CREATE (b:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ku5'}) "
        "CREATE (a)-[:HAS_PREREQUISITE]->(b)"
    )
    assert "urn:test:ku4 -> urn:test:ku5" in entidades(
        tx, consultas, "prerrequisito-entre-conceptos"
    )


# ---------------------------------------------------------------------------
# aciclicidad
# ---------------------------------------------------------------------------

def test_detecta_ciclo_de_part_of(tx, consultas):
    tx.run(
        "CREATE (a:KnowledgeElement:KnowledgeUnit {iri:'urn:test:ciclo-a'}) "
        "CREATE (b:KnowledgeElement:KnowledgeArea {iri:'urn:test:ciclo-b'}) "
        "CREATE (a)-[:PART_OF]->(b) CREATE (b)-[:PART_OF]->(a)"
    )
    detectadas = entidades(tx, consultas, "part-of-dag")
    assert {"urn:test:ciclo-a", "urn:test:ciclo-b"} & detectadas


def test_detecta_ciclo_de_prerrequisitos(tx, consultas):
    tx.run(
        "CREATE (a:KnowledgeElement:Concept {iri:'urn:test:p1'}) "
        "CREATE (b:KnowledgeElement:Concept {iri:'urn:test:p2'}) "
        "CREATE (c:KnowledgeElement:Concept {iri:'urn:test:p3'}) "
        "CREATE (a)-[:HAS_PREREQUISITE]->(b) "
        "CREATE (b)-[:HAS_PREREQUISITE]->(c) "
        "CREATE (c)-[:HAS_PREREQUISITE]->(a)"
    )
    assert entidades(tx, consultas, "prerrequisitos-dag")


# ---------------------------------------------------------------------------
# clave_unica: la unica regla con restriccion nativa, asi que la violacion
# no llega a escribirse. Lo que se prueba es que la base la rechaza.
# ---------------------------------------------------------------------------

def test_la_restriccion_nativa_rechaza_iri_duplicado(tx):
    existente = tx.run(
        "MATCH (n:KnowledgeElement) RETURN n.iri AS iri LIMIT 1"
    ).single()["iri"]

    with pytest.raises(Neo4jError):
        tx.run(
            "CREATE (:KnowledgeElement:KnowledgeUnit {iri:$iri})", iri=existente
        ).consume()


# ---------------------------------------------------------------------------
# El backbone tiene que haber quedado intacto tras todas las reversiones
# ---------------------------------------------------------------------------

def test_el_backbone_sigue_intacto():
    d = driver()
    try:
        with d.session(database=BASE) as s:
            conteos = {
                f["label"]: f["n"]
                for f in s.run(
                    "MATCH (n) UNWIND labels(n) AS label "
                    "RETURN label, count(*) AS n"
                )
            }
    finally:
        d.close()

    assert conteos.get("KnowledgeArea") == 17
    assert conteos.get("KnowledgeUnit") == 162
    assert conteos.get("LearningResource") == 1
    assert "Topic" not in conteos and "Concept" not in conteos
