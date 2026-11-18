# Operación del sistema

Cómo levantar, cargar, ingestar, reconstruir, medir y probar el módulo de grafo
y su aplicación web, en local o con Docker. El despliegue en el servidor de AWS
está en [`DEPLOYMENT.md`](../DEPLOYMENT.md); la presentación del proyecto, en
el [README](../README.md).

Los comandos se corren desde la raíz del repositorio.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), con Docker Compose.
- [uv](https://docs.astral.sh/uv/), que instala Python 3.11 o superior si hace falta.
- Node.js 20.19, 22.12 o 24 en adelante, para desarrollar la aplicación web y
  para ver los diagramas de arquitectura. Para desplegar con Docker no hace falta.

## Puesta en marcha

```powershell
cp .env.example .env        # y cambia NEO4J_PASSWORD (mínimo 8 caracteres)
docker compose up -d neo4j  # solo Neo4j 5.26; tarda uno o dos minutos en estar listo
docker compose ps           # esperar a ver "(healthy)"
uv sync                     # dependencias de Python en .venv
uv run iekg-build load      # carga el backbone en Neo4j
```

Neo4j Browser queda en <http://localhost:7474>, con el usuario `neo4j` y la
contraseña de `.env`.

`docker compose up -d`, sin nombrar un servicio, levanta el sistema completo en
contenedores (ver «Desplegar con Docker»). Para desarrollar con `uv run` se
levanta solo `neo4j`: una API en un contenedor y otra con `uv run` serían dos
escritores sobre el mismo grafo.

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
3. Vacía la base, crea las restricciones de unicidad y el índice de la
   búsqueda por nombre, y escribe 180 nodos y 341 aristas en una sola
   transacción.
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

// El índice de la búsqueda: name_search, de tipo FULLTEXT
SHOW INDEXES;
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

## La API

```powershell
uv run iekg-api             # http://localhost:8000, un solo proceso
```

Necesita `IEKG_OPERATOR_TOKEN` en `.env` (ver `.env.example`): sin él no
arranca. La documentación de cada ruta y del esquema de sus respuestas, con
ejemplos, la genera la propia API en <http://localhost:8000/docs> (OpenAPI en
`/openapi.json`).

| Ruta | Token | Qué hace |
|---|---|---|
| `POST /api/runs` | sí | Sube un PDF: registra la corrida como pendiente y lanza el worker si no hay uno activo. 202 con el id |
| `GET /api/runs` | sí | Lista las corridas |
| `GET /api/runs/{id}` | sí | Una corrida completa, con el reporte de auditoría que la cerró |
| `GET /api/runs/{id}/discards` | sí | Descartes de una corrida rechazada, con su lote o su salida cruda |
| `GET /api/audit-reports/latest` | sí | Último reporte de auditoría y estado de la compuerta |
| `GET /api/search?q=` | no | Elementos y cursos cuyo nombre o código empieza por cada palabra, por puntaje (RF-18) |
| `GET /api/nodes?key=` | no | Un nodo con sus propiedades, sus vecinos y algunos vecinos de estos |
| `GET /api/concepts/prerequisites?key=` | no | Prerrequisitos de un concepto, transitivos (RF-11) |
| `GET /api/courses/prerequisites?key=` | no | Lo que un curso enseña y requiere, y los cursos que enseñan lo requerido (RF-12) |
| `GET /api/elements/location?key=` | no | De qué es parte un elemento, hasta su área, y qué lo compone (RF-13) |
| `GET /api/elements/resources?key=` | no | Recursos de un elemento o curso y de sus partes (RF-14) |
| `GET /api/learning-path?key=&grain=` | no | Qué aprender antes de un concepto, tema, unidad, área o curso, por tema, curso o área (RF-15) |
| `GET /api/concepts/specializations?key=` | no | De qué es tipo un concepto y qué es tipo de él, transitivo (RF-16) |
| `GET /resources/{clave}` | no | El PDF de un recurso, solo si el grafo lo tiene |

Ejemplos, con el token de `.env` (en PowerShell, `curl.exe`; en Linux, `curl`):

```powershell
$H = "Authorization: Bearer $env:IEKG_OPERATOR_TOKEN"

# Subir un sílabo
curl.exe -H $H -F "file=@SILABO.pdf" -F "resource_type=Sílabo" -F "course_code=1INF33" -F "course_name=Bases de Datos" http://localhost:8000/api/runs
# {"run_id":2,"worker_launched":true}

# Seguir la corrida y ver sus descartes
curl.exe -H $H http://localhost:8000/api/runs/2
curl.exe -H $H http://localhost:8000/api/runs/2/discards

# ¿Está abierta la compuerta?
curl.exe -H $H http://localhost:8000/api/audit-reports/latest
# {"gate":{"state":"open","reason":null},"report":{...}}

# El documento, en la dirección de su localizador (pública)
curl.exe -O http://localhost:8000/resources/fadc83a6-a59e-47c9-a82d-8471fecb6178

# Navegación (pública). La clave va como parámetro: las de referencia son IRIs con '#'
curl.exe -G --data-urlencode "q=inteligencia artif" http://localhost:8000/api/search
$KA = "http://www.informatics-engineering-kms.org/ontology/informatic-engineering#KA-AI"
curl.exe -G --data-urlencode "key=$KA" http://localhost:8000/api/elements/location
curl.exe -G --data-urlencode "key=$KA" -d "grain=course" http://localhost:8000/api/learning-path
```

Sin token, o con otro, las rutas de `/api` responden 401. Un archivo que no
es PDF (por extensión o por contenido), un tipo de recurso desconocido o un
sílabo sin código o nombre de curso responden 422 y no registran nada. Si la
API no logra lanzar el worker, responde 503 y tampoco registra nada, ni la
corrida ni el PDF: hay que volver a subirlo.

`/resources/{clave}` responde 404 mientras el grafo no tenga el recurso: antes
de que la corrida escriba, y después de una carga hasta reaplicar.

Las rutas de navegación devuelven siempre `{nodes, edges}`: un trozo del grafo
tal como está guardado, con la procedencia de cada nodo y de cada arista entre
sus nodos. Una clave que no existe, o que es de otra clase que la que la ruta
espera (un curso en `/api/concepts/prerequisites`), responde 404. Las cotas de
profundidad, de vecinos y de resultados están en la cabecera de
`src/iekg/api/navigation.py`; el diseño, en
`docs/diseño-de-las-rutas-de-navegación.md`.

El worker corre como proceso hijo de la API y su salida aparece en la consola
de la API. Si termina sin error y quedan corridas pendientes con la compuerta
abierta, la API lanza otro. Hace lo mismo al arrancar, y así recoge lo que
quedó pendiente durante una carga o una reaplicación. Detener la API
interrumpe al worker (ADR-007).

## InfoKnows, la aplicación web

La aplicación de navegación está en [`web/`](../web/README.md). Con la API
corriendo (`uv run iekg-api`):

```powershell
cd web
npm ci
npm run dev                 # http://localhost:5173
```

El inicio pide `GET /api/overview`: las áreas, con cuántas unidades, temas y
conceptos son parte de cada una, y los cursos. El panel del operador se abre
con el botón «Operador» y pide el token de `.env`.

## Desplegar con Docker

`docker-compose.yml` levanta el sistema completo en un host, configurado solo
por `.env` (ADR-007 y ADR-013):

| Servicio | Qué es |
|---|---|
| `neo4j` | La base de grafos, en un volumen administrado por Docker |
| `api` | La imagen de la aplicación (`Dockerfile`): la API, que lanza el worker como proceso hijo |
| `web` | nginx (`web/Dockerfile`): sirve InfoKnows y reenvía `/api` y `/resources` a la API |
| `build` | La misma imagen con los procesos de construcción; no arranca con `up` |

```powershell
cp .env.example .env        # contraseña, token y dirección pública
docker compose up -d --build
docker compose ps           # neo4j y api "(healthy)", web "Up"
```

La aplicación queda en `http://<host>` (puerto 80, o el de `IEKG_WEB_PORT`).
Los puertos de Neo4j se publican solo en el loopback del host: en un servidor,
el Browser se alcanza con un túnel SSH (`ssh -L 7474:localhost:7474 -L 7687:localhost:7687 …`).
La primera construcción tarda unos minutos. La imagen de la aplicación instala
las dependencias en las versiones de `uv.lock`, con PyTorch en su compilado
solo para CPU y sin las bibliotecas de CUDA: queda en unos 2,5 GB. Para
instalar el bloqueo tal cual, que pesa varias veces más y solo sirve en un
host con GPU: `docker compose build --build-arg IEKG_TORCH=locked api`.

Con `IEKG_REHEARSAL=1` en `.env`, el panel del operador funciona en **modo
ensayo**: las corridas recorren sus estados en `var/ensayo/` sin leer el PDF,
sin llamar al modelo y sin tocar el grafo (enmienda 2026-11 de ADR-013). Se
activa o desactiva con `docker compose up -d api`.

Los procesos de construcción se ejecutan a demanda, con la API detenida
(ADR-007):

```powershell
docker compose stop api
docker compose run --rm build load        # vacía la base y carga el backbone
docker compose run --rm build reapply     # reescribe la capa institucional
docker compose start api
```

Lo que hay que poner en `.env` en cada máquina:

- `NEO4J_PASSWORD` e `IEKG_OPERATOR_TOKEN`.
- `IEKG_PUBLIC_BASE_URL`: la dirección por la que los estudiantes llegan a la
  web, por ejemplo `http://<IP fija>`. Queda escrita en el localizador de
  cada documento que se suba (ADR-009), así que se fija **antes** de ingestar.
  InfoKnows abre los documentos por su ruta, de modo que los enlaces siguen
  funcionando aunque esa dirección cambie; el localizador guardado, no.
- `IEKG_WEB_PORT`, si la web no va en el 80.
- El proveedor del modelo de lenguaje (`IEKG_LLM_*`), solo si se va a ingestar.
  Si el proveedor corre en el propio host, dentro del contenedor se llega a él
  con `IEKG_LLM_BASE_URL_IN_CONTAINER=http://host.docker.internal:8765/v1`.
- En una máquina con poca memoria, `NEO4J_HEAP_INITIAL`, `NEO4J_HEAP_MAX` y
  `NEO4J_PAGECACHE` (por omisión 2G, 4G y 2G).

Los tres almacenes de archivos —operacional, de documentos y de hechos— son la
carpeta `var/` del host (`IEKG_DATA_DIR`), montada en `api` y en `build`:
respaldar el sistema es copiar esa carpeta (ADR-013). Para llevar un grafo ya
ingestado a otra máquina se copia `var/` y se ejecutan `load` y `reapply`.

## Ingestar un sílabo

Por la API (arriba), o sin ella con un script de desarrollo que llama a la
misma función de registro y corre el worker en su propio proceso:

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

Para ver las corridas sin la API:

```powershell
uv run python -c "import sqlite3; print(*sqlite3.connect('var/operational.sqlite').execute('SELECT id, status, course_code, model, content_retries, error FROM runs ORDER BY id').fetchall(), sep=chr(10))"
```

La ingesta escribe en la base de desarrollo. `uv run iekg-build load` la deja
otra vez solo con el backbone; `var/` no se toca.

## Reaplicar los hechos

Ejecuta la carga y la reaplicación con la API y el worker detenidos; Neo4j
debe seguir encendido.

```powershell
uv run iekg-build load      # vacía la base y carga el backbone
uv run iekg-build reapply   # reescribe la capa institucional desde var/facts/
```

La reaplicación repite, en el orden de las corridas, el lote de cada corrida
que tiene archivo de hechos, sin volver a llamar al modelo de lenguaje. Salta
las corridas detenidas por la auditoría y cierra con una sola auditoría. Se
rechaza si la base ya tiene nodos institucionales: va justo después de una
carga. Los códigos de salida son los de la carga.

Puedes reconstruir el grafo desde un historial guardado eligiendo sus
almacenes. Por ejemplo, desde la raíz del repositorio, en PowerShell:

```powershell
$env:IEKG_OPERATIONAL_DB="var/chain-sonnet-2/operational.sqlite"
$env:IEKG_FACTS_DIR="var/chain-sonnet-2/facts"
$env:IEKG_DOCUMENTS_DIR="var/chain-sonnet-2/documents"
uv run iekg-build load
if ($LASTEXITCODE -eq 0) { uv run iekg-build reapply }
```

Conserva juntos el SQLite y los hechos de ese historial: la reaplicación
necesita ambos. Los documentos permiten seguir sirviendo los PDF. La carga
sustituye el grafo activo, pero conserva los almacenes locales; la reaplicación
usa todos los archivos de hechos elegibles, sin seleccionar una corrida de corte.
Comprueba que termine con auditoría limpia antes de reiniciar la API con esas
mismas rutas. Las variables permanecen en esa sesión de PowerShell.

La reconstrucción requiere hechos compatibles con el esquema y las claves
vigentes; los cambios de claves o de la T-Box exigen una migración (ADR-004).

## Medir la navigación (AC-05)

```powershell
uv run python scripts/measure_navigation.py
```

Script de desarrollo, que solo lee. Vacía la caché de planes de consulta y
ejecuta los cinco patrones medidos con las mismas funciones que las rutas,
desde todos sus nodos de partida: una ronda de calentamiento, cuya primera
ejecución es la de frío, y diez rondas medidas. Mide el tiempo en el motor que
informa el servidor, con resolución de 1 ms. Imprime una tabla Markdown por
patrón y escribe el reporte completo en
`var/measurements/ac05-<fecha-hora>.json`: tiempos de cada ejecución, tamaño
del grafo, entorno, cota de profundidad y planes. Sale con 0 si todos los
patrones quedan bajo 1 s en mediana y percentil 95; con 1 si alguno no, o si
alguno no tiene nodos de partida, como pasa con solo el backbone. El protocolo
está en `docs/diseño-de-las-rutas-de-navegación.md`, sección 8.

## Pruebas

```powershell
uv run pytest tests/ -q                  # todas
uv run pytest tests/ -q -m "not neo4j"   # solo las que no necesitan Neo4j
```

Las pruebas marcadas `neo4j` se saltan si la base no responde. Escriben solo
dentro de transacciones que se revierten, así que no alteran lo cargado.
Ninguna prueba ejecuta la carga, llama al proveedor del modelo de lenguaje ni
lanza el worker.

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
| `IEKG_OPERATOR_TOKEN` | — (obligatoria para la API) | Token de las rutas de operación |
| `IEKG_API_HOST` | `127.0.0.1` | Dirección en la que escucha la API |
| `IEKG_API_PORT` | `8000` | Puerto de la API |
| `IEKG_LLM_MODEL` | — (obligatoria para ingestar) | Modelo, tal como lo nombra el proveedor |
| `IEKG_LLM_API_KEY` | — (obligatoria para ingestar) | Clave del proveedor |
| `IEKG_LLM_BASE_URL` | la de OpenAI | Cualquier servidor con la API Chat Completions |
| `IEKG_LLM_REASONING_EFFORT` | — | Esfuerzo de razonamiento, si el modelo lo admite |
| `IEKG_LLM_TEMPERATURE` | — | Temperatura, si el modelo la admite |
| `IEKG_LLM_MAX_RETRIES` | `3` | Reintentos ante errores transitorios del proveedor |
| `IEKG_LLM_TIMEOUT_SECONDS` | `900` | Tiempo máximo por llamada |

Solo las lee `docker-compose.yml`:

| Variable | Por defecto | Uso |
|---|---|---|
| `IEKG_WEB_PORT` | `80` | Puerto del host en que nginx publica la web |
| `IEKG_DATA_DIR` | `./var` | Carpeta del host con los tres almacenes de archivos |
| `IEKG_LLM_BASE_URL_IN_CONTAINER` | la de `IEKG_LLM_BASE_URL` | Dirección del proveedor vista desde el contenedor |
| `NEO4J_IMAGE` | `neo4j:5.26.28-community` | Imagen de Neo4j |
| `NEO4J_HEAP_INITIAL`, `NEO4J_HEAP_MAX`, `NEO4J_PAGECACHE` | `2G`, `4G`, `2G` | Memoria de Neo4j |

En los contenedores, `IEKG_PUBLIC_BASE_URL` vale por omisión
`http://localhost`, la dirección de la web.

Las rutas relativas se resuelven desde el directorio actual: corre los
comandos desde la raíz del repositorio.

## Diagramas de arquitectura (opcional)

```powershell
npm install               # una vez
npm run arch:serve        # vista previa en el navegador
npm run arch:validate     # comprueba el modelo
```

## Commits

- **Un commit, una razón para cambiar.** Van juntos el código, sus pruebas y
  la documentación que pasa a ser cierta con él (README, `CLAUDE.md`).
- **La decisión va antes que el código**, en su propio commit `docs:` (ADR y
  `.c4`), porque se escribe antes de implementar.
- **Cada commit deja las pruebas en verde.** No se separa «código» de
  «documentación»: el commit intermedio dejaría documentos que mienten.
- **Mensaje en inglés**, en imperativo y minúscula, de hasta 72 caracteres; el
  porqué va en el cuerpo (`docs/estandares-de-codigo.md` §1).

## Estructura

```
ontology/            Ontología (esquema) y backbone CS2023, en Turtle
src/iekg/            Código: esquema del grafo, núcleo, carga, ingesta, API, SQLite
scripts/             Ayudas de desarrollo (no son puntos de entrada del sistema)
tests/               Pruebas
web/                 InfoKnows, la aplicación web (Svelte, Vite y D3), con su Dockerfile y su nginx
docs/                Tesis, decisiones de arquitectura (ADR) y modelo C4
Dockerfile           Imagen única de la aplicación: API, worker y procesos de construcción
docker-compose.yml   El sistema completo: Neo4j, API, web y procesos de construcción
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
- **Edición de Neo4j:** el `docker-compose.yml` usa Neo4j Community. Un
  volumen creado antes con Enterprise no abre con Community (el contenedor se
  reinicia sin llegar a «healthy»): o se pone
  `NEO4J_IMAGE=neo4j:5.26.28-enterprise` en `.env`, o se crea un volumen nuevo
  con `docker compose down -v` y se reconstruye el grafo con `load` y
  `reapply`.
- **`NOT NULL constraint failed: audit_reports.violations`:** el
  `var/operational.sqlite` es anterior a los reportes abiertos. Muévelo o
  bórralo, y la siguiente carga crea uno nuevo. La base no se toca.
