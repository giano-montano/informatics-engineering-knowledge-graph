# Grafo de conocimiento del currículo de Ingeniería Informática

Módulo de grafo de conocimiento de una tesis de Ingeniería Informática (PUCP).
Representa en Neo4j las áreas y unidades de conocimiento del estándar CS2023
y, más adelante, el contenido extraído de los sílabos de la carrera.

## Estado actual

| Funciona | Todavía no existe |
|---|---|
| Carga del backbone CS2023 en Neo4j, desde la ontología en Turtle | Ingesta de sílabos con modelo de lenguaje |
| Auditoría de integridad del grafo (15 reglas) al cerrar la carga | API, worker y aplicación web |
| Registro de cada reporte de auditoría en SQLite | Reaplicación de hechos guardados |

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), con Docker Compose.
- [uv](https://docs.astral.sh/uv/), que instala Python 3.11 o superior si hace falta.
- Node.js, solo para ver los diagramas de arquitectura (opcional).

## Puesta en marcha

```powershell
cp .env.example .env        # y cambia NEO4J_PASSWORD (mínimo 8 caracteres)
docker compose up -d        # Neo4j 5.26; tarda uno o dos minutos en estar listo
docker compose ps           # esperar a ver "(healthy)"
uv sync                     # dependencias de Python en .venv
uv run iekg-build load      # carga el backbone en Neo4j
```

Neo4j Browser queda en <http://localhost:7474>, con el usuario `neo4j` y la
contraseña de `.env`.

## Cargar el backbone

```powershell
uv run iekg-build load
```

> **La carga vacía la base.** Borra todo lo que haya en Neo4j antes de
> escribir.

La carga hace esto, en orden:

1. Lee `ontology/ontologia_informatica.ttl` y `ontology/backbone_cs2023.ttl`,
   y rechaza cualquier constructo que no sepa proyectar.
2. Valida en memoria lo que va a escribir.
3. Vacía la base, crea las restricciones de unicidad y escribe 180 nodos y 341
   aristas en una sola transacción.
4. Audita el grafo completo y guarda el reporte en `var/operational.sqlite`.

Si falla el paso 1 o el 2, la base queda como estaba.

Si todo sale bien, la salida termina así:

```
  committed: 180 nodes, 341 edges
  ...
  RM-05  ok               Every learning resource has a locator
Audit report 1 recorded in var\operational.sqlite: clean
```

| Código de salida | Significado |
|---|---|
| 0 | Cargado; auditoría limpia |
| 1 | Cargado; la auditoría encontró violaciones |
| 2 | Rechazado antes de tocar la base |
| 3 | Falló; el mensaje dice en qué estado quedó la base |

## Ver el resultado en Neo4j Browser

```cypher
// Nodos por etiqueta: 17 KnowledgeArea, 162 KnowledgeUnit,
// 179 KnowledgeElement, 1 LearningResource
MATCH (n) UNWIND labels(n) AS label RETURN label, count(*);

// Aristas por tipo: 162 PART_OF, 179 WAS_DERIVED_FROM
MATCH ()-[r]->() RETURN type(r), count(*);

// Las unidades del área de Inteligencia Artificial, como grafo
MATCH p = (:KnowledgeUnit)-[:PART_OF]->(a:KnowledgeArea)
WHERE a.key ENDS WITH '#KA-AI'
RETURN p;

// Restricciones de unicidad: 8, una por etiqueta
SHOW CONSTRAINTS;
```

## Limpiar y volver a cargar

Para comprobar que la carga reconstruye todo desde cero:

1. Vaciar la base. Hay dos opciones:
   - En el Browser: `MATCH (n) DETACH DELETE n`.
   - Para una base nueva del todo: `docker compose down -v` y luego
     `docker compose up -d`. Esto borra también las restricciones, los logs y
     los plugins del contenedor; `var/` no se toca.
2. Comprobar que quedó vacía: `MATCH (n) RETURN count(n)`.
3. Cargar de nuevo: `uv run iekg-build load`.

## Reportes de auditoría

Cada carga deja su reporte en `var/operational.sqlite`. Puedes abrirlo con
cualquier visor de SQLite, o listar los últimos así:

```powershell
uv run python -c "import sqlite3; print(sqlite3.connect('var/operational.sqlite').execute('SELECT id, created_at, origin, violations FROM audit_reports ORDER BY id DESC LIMIT 5').fetchall())"
```

## Pruebas

```powershell
uv run pytest tests/ -q                  # todas
uv run pytest tests/ -q -m "not neo4j"   # solo las que no necesitan Neo4j
```

Las pruebas marcadas `neo4j` se saltan si la base no responde. Escriben solo
dentro de transacciones que se revierten, así que no alteran lo cargado.
Ninguna prueba ejecuta la carga.

## Configuración

Todo se lee del entorno o de `.env`.

| Variable | Por defecto | Uso |
|---|---|---|
| `NEO4J_PASSWORD` | — (obligatoria) | Contraseña de Neo4j |
| `NEO4J_URI` | `bolt://localhost:7687` | Dirección de Neo4j |
| `NEO4J_USER` | `neo4j` | Usuario de Neo4j |
| `NEO4J_DATABASE` | `neo4j` | Base de datos |
| `IEKG_TBOX` | `ontology/ontologia_informatica.ttl` | Ontología (esquema) |
| `IEKG_BACKBONE` | `ontology/backbone_cs2023.ttl` | Backbone CS2023 |
| `IEKG_OPERATIONAL_DB` | `var/operational.sqlite` | Reportes de auditoría |

Las rutas relativas se resuelven desde el directorio actual: corre los
comandos desde la raíz del repositorio.

## Diagramas de arquitectura (opcional)

```powershell
npm install               # una vez
npm run arch:serve        # vista previa en el navegador
npm run arch:validate     # comprueba el modelo
```

## Estructura

```
ontology/            Ontología (esquema) y backbone CS2023, en Turtle
src/iekg/            Código: esquema del grafo, núcleo, carga, SQLite
tests/               Pruebas
docs/                Tesis, decisiones de arquitectura (ADR) y modelo C4
docker-compose.yml   Neo4j para desarrollo
var/                 Datos locales del sistema (no se versiona)
```

## Problemas frecuentes

- **Docker no responde** (`failed to connect to the docker API`): abre Docker
  Desktop y espera a que arranque.
- **Neo4j rechaza la contraseña después de cambiarla en `.env`:** Neo4j fija la
  contraseña la primera vez que crea su volumen. Ejecuta
  `docker compose down -v` y `docker compose up -d`.
- **Tildes mal impresas en la consola de Windows:** es solo la consola. Los
  datos están bien guardados y el Browser los muestra correctamente.
- **Edición de Neo4j:** el `docker-compose.yml` usa Neo4j Enterprise con
  licencia de evaluación, para desarrollo. El sistema solo usa funciones de la
  edición Community, que es la del despliegue.
