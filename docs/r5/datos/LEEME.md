# Datos capturados para las maquetas de R5

Respuestas **reales** de la API de R4 sobre el grafo de desarrollo (backbone CS2023 + 4 sílabos:
1INF01, INF144, INF238, 1INF35), capturadas el 2026-10-29 con la API en el puerto 8790. Solo se
llamaron rutas GET. Las maquetas no necesitan la API para funcionar.

## Archivos

| Archivo | Qué es |
|---|---|
| `datos.js` | Todo junto, para `<script src="../datos/datos.js">`. Define `window.IEKG_DATOS`, `window.IEKG_OPERACION` y `window.IEKG_SIMULADO`. 7,8 MB: se carga en menos de un segundo desde disco. |
| `operacion.json` | = `IEKG_OPERACION`. Rutas de operación (con token). |
| `simulado.json` | = `IEKG_SIMULADO`. **No sale de ninguna ruta** (ver abajo). |

## Cómo se indexa `IEKG_DATOS`

```js
IEKG_DATOS["/api/search"]["redes"]                     // por texto buscado
IEKG_DATOS["/api/nodes"][clave]                        // detalle: los 491 nodos
IEKG_DATOS["/api/concepts/prerequisites"][clave]       // 263 conceptos
IEKG_DATOS["/api/concepts/specializations"][clave]     // 263 conceptos
IEKG_DATOS["/api/courses/prerequisites"][clave]        // 4 cursos
IEKG_DATOS["/api/elements/location"][clave]            // 481 elementos de conocimiento (un curso da 404)
IEKG_DATOS["/api/elements/resources"][clave]           // 485: elementos y cursos
IEKG_DATOS["/api/learning-path?grain=topic"][clave]    // también ?grain=course y ?grain=area
```

Se capturaron **todas** las claves válidas de cada ruta: cualquier clic de la maqueta sobre un nodo
real tiene respuesta. Una clave ausente en una ruta significa que la API responde 404 para esa clase
(p. ej. un curso en `/api/concepts/prerequisites`).

Búsquedas capturadas (claves de `/api/search`): `árbol`, `arbol`, `redes`, `programación`, `pila`,
`sistemas operativos`, `INF144`, `arreglo`, `puntero`, `lógica`, `ethernet`, `subred`, `seguridad`,
`algoritmo`, `datos`. **`árbol`, `arbol` y `pila` devuelven 0 nodos**: los 4 sílabos no tratan esos
temas: muestran el estado vacío. Un texto no capturado no tiene respuesta real: las maquetas lo
filtran en el cliente sobre los nombres de `/api/nodes` y lo rotulan «búsqueda simulada».

## Forma de toda respuesta de navegación: `{nodes, edges}`

```json
{"nodes": [
   {"key": "ce8cd4d1-…", "label": "Concept", "name_es": "Contradicción", "name_en": null,
    "layer": "institutional", "depth": 0},
   {"key": "29a47e34-…", "label": "Concept", "name_es": "Tabla de verdad", "name_en": null,
    "layer": "institutional", "depth": 1},
   {"key": "5a791a78-…", "label": "LearningResource", "name_es": "Sílabo 1INF01", "name_en": null,
    "layer": "institutional", "locator": "http://localhost:8000/resources/5a791a78-…"}],
 "edges": [
   {"type": "HAS_PREREQUISITE", "source": "ce8cd4d1-…", "target": "29a47e34-…", "provenance": "5a791a78-…"},
   {"type": "WAS_DERIVED_FROM", "source": "ce8cd4d1-…", "target": "5a791a78-…", "provenance": "5a791a78-…"}]}
```

- `label`: `KnowledgeArea`, `KnowledgeUnit`, `Topic`, `Concept`, `Course`, `LearningResource`, `ResourceType`.
- `layer`: `reference` (CS2023: las 17 áreas y 162 unidades) o `institutional` (lo que sale de los sílabos:
  temas, conceptos, cursos, sílabos). **RF-22** se apoya en este campo.
- Campos opcionales por nodo: `course_code` (curso), `locator` (recurso), `depth` (rutas transitivas),
  `score` (búsqueda), `description` y `more_neighbors` (solo en `/api/nodes`).
- `edges[].provenance`: clave del sílabo del que sale la arista; `null` en la capa de referencia.
  El sílabo está entre los `nodes` de la misma respuesta. **RF-21**: el documento de un nodo se
  encuentra siguiendo su arista `WAS_DERIVED_FROM`; el de una arista, buscando su `provenance`.
- Tipos de arista: `PART_OF` (Concept→Topic→KnowledgeUnit→KnowledgeArea), `HAS_PREREQUISITE` y
  `SPECIALIZES` (Concept→Concept), `TEACHES_CONCEPT` y `REQUIRES_CONCEPT` (Course→Concept),
  `IS_ABOUT` (recurso→elemento o curso), `HAS_RESOURCE_TYPE`, `WAS_DERIVED_FROM`.
- Las aristas **no tienen peso** ni ningún otro atributo.

### Por ruta, lo que conviene saber

- **`/api/nodes`** (detalle): el nodo en foco es `nodes[0]`, con `description` (casi siempre `null`) y
  `more_neighbors`. Trae hasta 25 vecinos directos y 5 de segundo nivel por vecino, más sus sílabos.
  `more_neighbors: true` en un vecino = tiene más vecinos no incluidos (ofrecer «expandir»).
- **`/api/concepts/prerequisites`**: `depth` = distancia al foco (0 = foco).
- **`/api/courses/prerequisites`** (PC2): lo que el curso enseña (`TEACHES_CONCEPT`) y requiere
  (`REQUIRES_CONCEPT`), y los cursos que enseñan lo requerido. **Aquí está el prerrequisito real
  entre cursos**: INF144 requiere *Algoritmia*, *Estructuras de control de flujo* y *Subprogramas*,
  que enseña 1INF01; 1INF35 requiere *Virtualización* y *Computación en la nube*, que enseña INF238.
- **`/api/elements/location`** (PC3, PC4): sube por `PART_OF` hasta el área y baja la composición.
  Para un área grande es pesada (KA-NC: 158 nodos).
- **`/api/elements/resources`** (PC5): recursos que tratan sobre el elemento o sus partes, con
  `IS_ABOUT` y `HAS_RESOURCE_TYPE`. El único tipo de recurso es «Sílabo». Un **concepto** solo no
  tiene recursos (devuelve el concepto y su sílabo de procedencia): se llega a los del tema subiendo.
- **`/api/learning-path?grain=`** (PC6): `depth` 0 en el objetivo; en un prerrequisito, su distancia;
  en un tema/curso/área del grano, la de su prerrequisito más cercano. Trae los conceptos prerrequisito
  y las aristas que lo justifican (evidencia).
  **Ojo:** con objetivo *curso*, los 4 cursos dan ruta vacía (sus prerrequisitos están dentro del mismo
  curso). Para el prerrequisito entre cursos, usar `/api/courses/prerequisites`. Hay 35 objetivos con
  ruta no vacía, todos temas o conceptos.
- **`/api/concepts/specializations`** (PC7): solo 6 aristas `SPECIALIZES` en todo el grafo.

### Claves de ejemplo

| Para | Nombre | Clave |
|---|---|---|
| Concepto con prerrequisitos transitivos (prof. 2) | Contradicción | `ce8cd4d1-77f1-4ec1-b10f-d8b87dabe678` |
| Ídem | Estructuras selectivas anidadas | `2e4249c1-16b4-43f4-968d-db223f07a606` |
| Ídem, en redes | CIDR | `0b7a767c-9a32-4239-afc8-843201be6288` |
| Concepto con 3 prerrequisitos directos | Tabla de verdad | `29a47e34-1d18-4962-9501-c4f5b960003c` |
| Ruta que cruza dos cursos (grano curso) | Entrada y salida de datos desde archivos | `9a161bca-1a01-43de-8875-7bdfb53ebd84` |
| Ídem, Redes → Adm. de SO | Zonas DNS integradas al Directorio Activo | `39173978-d32d-4b06-9883-f5edc303456c` |
| Especialización (padre con 3 hijos) | Ethernet IEEE 802.3 (buscar «ethernet») | ver `/api/search` «ethernet» |
| Tema | Lógica proposicional | `40347f92-1123-45ef-8225-b77837c551d7` |
| Tema | Subredes y enrutamiento | `e1c009b2-578c-48a4-8299-d4cba0917530` |
| Tema con ruta (grano tema) | Cadenas de caracteres | buscar en `/api/nodes` por `name_es` |
| Curso | Fundamentos de Programación (1INF01) | `2c4f27fc-7945-5378-95ed-9180df25e348` |
| Curso con prerrequisito real | Técnicas de Programación (INF144) | `b2d9c106-684d-58b8-8462-4dc0c3b8d90c` |
| Curso | Redes de Computadoras (INF238) | `c5405343-8817-5bd7-820c-8013c9bbfeee` |
| Curso | Administración de Sistemas Operativos (1INF35) | `555619e3-bbe6-5c80-be31-97f8a1449c0a` |
| Área (referencia) poblada | Redes y Comunicación | `http://www.informatics-engineering-kms.org/ontology/informatic-engineering#KA-NC` |
| Área poblada | Fundamentos del Desarrollo de Software | `…#KA-SDF` (mismo prefijo) |
| Área vacía de institucional | Inteligencia Artificial | `…#KA-AI` |

## Datos reales que condicionan el diseño

- **`description`: solo 1 nodo la tiene** (CS2023). Ninguna ficha puede depender de una descripción.
- **`name_en`** solo existe en la capa de referencia (áreas, unidades, CS2023).
- 263 conceptos, 39 temas, 4 cursos, 4 sílabos; 33 `HAS_PREREQUISITE`, profundidad máxima 2.
- Solo 7 de las 17 áreas tienen contenido institucional (ver `IEKG_SIMULADO.areas`). Las otras 10
  son solo backbone: las maquetas las muestran como «existe en CS2023, pero aún no en la malla».
- **PDF (RF-21):** el `locator` de cada sílabo es `http://localhost:8000/resources/<clave>`: abre el
  PDF real **solo si la API corre en el puerto por omisión** (`uv run iekg-api`).
  El de CS2023 es `https://dl.acm.org/doi/book/10.1145/3664191`.

## `IEKG_SIMULADO` (no es de la API)

Sale de una consulta Cypher de solo lectura. Las propuestas que lo usan lo declaran como **ruta nueva
necesaria** y lo rotulan «simulado» en pantalla.

```js
IEKG_SIMULADO.areas   // 17: {key, name_es, name_en, units, topics, concepts}  (conteos bajo cada área)
IEKG_SIMULADO.courses // 4:  {key, name_es, code}
```

## `IEKG_OPERACION` (rutas con token)

Claves: `"GET /api/runs"`, `"GET /api/runs/1"` … `"GET /api/runs/4"`, `"GET /api/runs/N/discards"`,
`"GET /api/audit-reports/latest"`, `"GET /api/runs (sin token)"` (= `[401, {"detail": "missing or wrong operator token"}]`).

- `GET /api/runs`: lista de `{id, status, created_at, finished_at, resource_type, course_code, course_name, file_name}`.
  Las 4 corridas están `completed`. Estados posibles (ADR-010): ver `src/iekg/api/models.py` (`_STATES`).
- `GET /api/runs/{id}`: además `started_at, resource_key, model, model_settings, prompt_version,
  content_retries, error, audit_report{id, created_at, origin, run_id, completed, violations, rules[{rule, violations, sample[]}]}`.
- `GET /api/runs/{id}/discards`: `{discards: [{rule, fact, message}], batch, raw_output}`. **Las 4 están
  vacías.** Una corrida con descartes se muestra con el ejemplo de la documentación de la API
  (`{"rule": "RI-05", "fact": "(a)-[:PART_OF]->(b)", "message": "Concept PART_OF Course"}`),
  rotulado **ejemplo, no real**.
- `GET /api/audit-reports/latest`: `{gate: {state, reason}, report}`; hoy `gate.state = "open"`, 15 reglas, 0 violaciones.
- `POST /api/runs` (no se llamó): multipart con el archivo, tipo de recurso, código y nombre del curso;
  responde 202. Ver `src/iekg/api/app.py` y el `README.md` raíz para los campos exactos.
