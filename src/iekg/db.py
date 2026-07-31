"""Conexion a Neo4j.

Las credenciales salen de .env, nunca del codigo. La instancia del laboratorio
es la que levanta docker-compose.yml en la raiz del repo.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

RAIZ = Path(__file__).resolve().parents[2]

URI_POR_DEFECTO = "bolt://localhost:7687"
USUARIO_POR_DEFECTO = "neo4j"

# Community solo admite una base de datos de usuario, y el despliegue final
# va a Community. Por eso todo vive en `neo4j` y nada depende de multi-base.
BASE = "neo4j"


def _password() -> str:
    load_dotenv(RAIZ / ".env")
    pw = os.getenv("NEO4J_PASSWORD")
    if not pw:
        raise RuntimeError(
            "Falta NEO4J_PASSWORD. Copia .env.example a .env y pon la "
            "contrasena de la instancia del laboratorio."
        )
    return pw


def driver() -> Driver:
    uri = os.getenv("NEO4J_URI", URI_POR_DEFECTO)
    usuario = os.getenv("NEO4J_USER", USUARIO_POR_DEFECTO)
    return GraphDatabase.driver(uri, auth=(usuario, _password()))


@contextmanager
def sesion() -> Iterator:
    """Sesion contra la base del laboratorio, cerrando driver y sesion."""
    d = driver()
    try:
        with d.session(database=BASE) as s:
            yield s
    finally:
        d.close()
