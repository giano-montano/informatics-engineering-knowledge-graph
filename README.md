# Grafo de conocimiento del currículo de Ingeniería Informática

Módulo de grafo de conocimiento de una tesis de Ingeniería Informática (PUCP).
Representa en Neo4j las áreas y unidades de conocimiento del estándar CS2023
y, más adelante, el contenido extraído de los sílabos de la carrera.

## Estado actual

| Funciona | Todavía no existe |
|---|---|
| Carga del backbone CS2023 en Neo4j, desde la ontología en Turtle | API y aplicación web |
| Auditoría de integridad del grafo (15 reglas) al cerrar cada escritura | Imagen de Docker del sistema |
| Ingesta de sílabos con modelo de lenguaje: worker, corridas, descartes y hechos | |
| Reaplicación de los hechos guardados después de una carga | |
| Registro de corridas, descartes y reportes de auditoría en SQLite | |

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
     `docker compose up -d`. Esto borra también las restricciones y los logs del
     contenedor; `var/` no se toca.
2. Comprobar que quedó vacía: `MATCH (n) RETURN count(n)`.
3. Cargar de nuevo: `uv run iekg-build load`.

## Reportes de auditoría

Cada carga deja su reporte en `var/operational.sqlite`. Puedes abrirlo con
cualquier visor de SQLite, o listar los últimos así:

```powershell
uv run python -c "import sqlite3; print(sqlite3.connect('var/operational.sqlite').execute('SELECT id, created_at, origin, violations FROM audit_reports ORDER BY id DESC LIMIT 5').fetchall())"
```

Un reporte con `violations` en `None` quedó abierto: la carga tocó la base y
no terminó. Mientras sea el último, la compuerta de auditoría sigue cerrada.

## Ingestar un sílabo (desarrollo)

Mientras no exista la API, un script hace lo mismo que hará ella: registra la
corrida como pendiente, guarda el PDF en `var/documents/` y lanza el worker.

```powershell
uv run python scripts/submit_document.py RUTA\AL\SILABO.pdf --course 1INF33 --name "Bases de Datos"
```

Hace falta configurar antes el proveedor del modelo de lenguaje en `.env`
(ver `.env.example`) y que la última auditoría esté limpia: el worker no toma
corridas si el último reporte tiene violaciones o quedó abierto. Con
`--no-worker` solo registra la corrida; `uv run iekg-worker` procesa después
las pendientes.

Cada corrida termina en uno de estos estados:

| Estado | Qué pasó | Qué queda |
|---|---|---|
| `completed` | Escrita y auditada sin violaciones | Archivo de hechos en `var/facts/` |
| `rejected` | Salida no conforme (EX-01 a EX-03) o lote con violaciones | Descartes y lote o salida cruda, en SQLite |
| `failed` | Falló el proveedor o la escritura, que se revirtió | El error, en SQLite |
| `stopped_by_audit` | Escrita, pero la auditoría encontró violaciones: la compuerta se cierra | Archivo de hechos y reporte |
| `written_not_persisted` | Escrita, sin archivo de hechos o sin auditar | El error, en SQLite |

Para ver las corridas:

```powershell
uv run python -c "import sqlite3; print(*sqlite3.connect('var/operational.sqlite').execute('SELECT id, status, course_code, model, content_retries, error FROM runs ORDER BY id').fetchall(), sep=chr(10))"
```

La ingesta escribe en la base de desarrollo. `uv run iekg-build load` la deja
otra vez solo con el backbone; `var/` no se toca.

## Reaplicar los hechos

```powershell
uv run iekg-build load      # vacía la base y carga el backbone
uv run iekg-build reapply   # reescribe la capa institucional desde var/facts/
```

La reaplicación repite, en el orden de las corridas, el lote de cada corrida
que tiene archivo de hechos, sin volver a llamar al modelo de lenguaje. Salta
las corridas detenidas por la auditoría y cierra con una sola auditoría. Se
rechaza si la base ya tiene nodos institucionales: va justo después de una
carga. Los códigos de salida son los de la carga.

## Pruebas

```powershell
uv run pytest tests/ -q                  # todas
uv run pytest tests/ -q -m "not neo4j"   # solo las que no necesitan Neo4j
```

Las pruebas marcadas `neo4j` se saltan si la base no responde. Escriben solo
dentro de transacciones que se revierten, así que no alteran lo cargado.
Ninguna prueba ejecuta la carga ni llama al proveedor del modelo de lenguaje.

La primera ingesta descarga los modelos de Docling (unos minutos). En Windows
sin compilador de C++, Docling necesita `TORCHDYNAMO_DISABLE=1`; el extractor
la fija por su cuenta.

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
| `IEKG_OPERATIONAL_DB` | `var/operational.sqlite` | Corridas, descartes y reportes de auditoría |
| `IEKG_FACTS_DIR` | `var/facts` | Un archivo de hechos por corrida escrita |
| `IEKG_DOCUMENTS_DIR` | `var/documents` | Los PDF subidos, nombrados con su clave |
| `IEKG_PUBLIC_BASE_URL` | `http://localhost:8000` | Base del localizador de cada documento subido |
| `IEKG_LLM_MODEL` | — (obligatoria para ingestar) | Modelo, tal como lo nombra el proveedor |
| `IEKG_LLM_API_KEY` | — (obligatoria para ingestar) | Clave del proveedor |
| `IEKG_LLM_BASE_URL` | la de OpenAI | Cualquier servidor con la API Chat Completions |
| `IEKG_LLM_REASONING_EFFORT` | — | Esfuerzo de razonamiento, si el modelo lo admite |
| `IEKG_LLM_TEMPERATURE` | — | Temperatura, si el modelo la admite |
| `IEKG_LLM_MAX_RETRIES` | `3` | Reintentos ante errores transitorios del proveedor |
| `IEKG_LLM_TIMEOUT_SECONDS` | `900` | Tiempo máximo por llamada |

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
src/iekg/            Código: esquema del grafo, núcleo, carga, ingesta, SQLite
scripts/             Ayudas de desarrollo (no son puntos de entrada del sistema)
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
- **`NOT NULL constraint failed: audit_reports.violations`:** el
  `var/operational.sqlite` es anterior a los reportes abiertos. Muévelo o
  bórralo, y la siguiente carga crea uno nuevo. La base no se toca.
