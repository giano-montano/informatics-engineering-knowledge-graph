# Diseño de las rutas de navegación

**Fecha:** 2026-10-09, revisado el mismo día al implementarlo · **Requisitos:** RF-11 a RF-18 · **Atributos:** AC-05, AC-03

Documento interno. Reúne las decisiones de diseño de las rutas de navegación de la API, con sus alternativas descartadas. No es un ADR: ninguna cambia la arquitectura, que ya fija el componente de rutas de navegación del modelo C4. Es insumo para la tesis y para la implementación.

Las derivaciones son las del Paso 5 de R1 (`ontology/aplicacion_od101_r1.md`), tal como están escritas; este diseño no agrega ninguna.

---

## 1. Forma de la respuesta: un subgrafo

Todas las rutas devuelven la misma forma, `{nodes, edges}`: un trozo del grafo tal como está guardado, sin aristas ni nodos que la API invente. R6 lo dibuja o lo convierte en lista.

```json
{
  "nodes": [
    {"key": "15d8…", "label": "Concept", "name_es": "Variables estáticas", "name_en": null, "layer": "institutional", "depth": 0},
    {"key": "9a1c…", "label": "Concept", "name_es": "Punteros", "name_en": null, "layer": "institutional", "depth": 1},
    {"key": "fadc…", "label": "LearningResource", "name_es": "Sílabo 1INF25", "name_en": null, "layer": "institutional",
     "locator": "https://…/resources/fadc…"}
  ],
  "edges": [
    {"type": "HAS_PREREQUISITE", "source": "15d8…", "target": "9a1c…", "provenance": "fadc…"},
    {"type": "WAS_DERIVED_FROM", "source": "15d8…", "target": "fadc…", "provenance": "fadc…"},
    {"type": "WAS_DERIVED_FROM", "source": "9a1c…", "target": "fadc…", "provenance": "fadc…"}
  ]
}
```

- **Nodo:** su clave, su etiqueta de clase (la más específica, no `KnowledgeElement`), sus etiquetas preferidas en español e inglés, su capa y las propiedades de la Tabla 17 que le corresponden: el código del curso o el localizador del recurso. Lo propio de cada patrón va como dato del nodo: la distancia (`depth`) o el puntaje de la búsqueda (`score`).
- **Arista:** su tipo, sus extremos y su procedencia, que es nula en la capa de referencia.
- Una relación derivada se muestra por su evidencia, no por una arista nueva. Que un curso preceda a otro se ve en el concepto que uno enseña y el otro requiere.

| Alternativa | Motivo del descarte |
|---|---|
| Una forma por ruta (listas, árboles) | R6 tendría que conocer cada forma; el subgrafo sirve para dibujar y para listar. |
| Aristas derivadas en la respuesta (p. ej. `PRECEDES` entre cursos) | Una arista que el grafo no tiene; la evidencia ya la muestra. |

## 2. Procedencia (RF-17)

Todo nodo de la respuesta llega con sus aristas `WAS_DERIVED_FROM` y los recursos de aprendizaje a los que apuntan, con su localizador. Toda arista institucional lleva en `provenance` la clave de su recurso, que está entre los nodos de la misma respuesta. R6 abre el documento de un nodo siguiendo su `WAS_DERIVED_FROM` y el de una arista buscando su `provenance` entre los nodos.

En la capa de referencia, el recurso es CS2023 con su URL pública: la regla es la misma para las dos capas.

| Alternativa | Motivo del descarte |
|---|---|
| El localizador copiado en cada nodo y cada arista | Repite el recurso en cada elemento y mezcla en la respuesta el grafo con anotaciones derivadas. |

## 3. Consultas en dos pasos

Un recorrido de longitud variable que devuelve caminos los enumera todos; uno que devuelve nodos distintos visita cada nodo una vez. Por eso cada patrón calcula primero los nodos alcanzados y después, en la misma consulta, las aristas entre ellos.

Medido el 2026-10-09 sobre Neo4j 5.26.28. El plan, con `EXPLAIN`, en Community (contenedor temporal) y en Enterprise: `VarLengthExpand(Pruning,BFS)` para los nodos distintos y `VarLengthExpand(All)` para los caminos, con y sin cota. Los conteos, con `PROFILE` en Enterprise, en una transacción revertida, sobre 16 rombos de prerrequisitos en cadena:

| Consulta | Resultado | Accesos a la base |
|---|---|---|
| Nodos distintos | 48 nodos | 115 |
| Caminos | 262 140 caminos | 524 283 |
| Nodos, y luego las aristas entre ellos | 49 nodos, 64 aristas | 228 |

| Alternativa | Motivo del descarte |
|---|---|
| Devolver los caminos | Crecen de forma exponencial con los rombos; un solo nodo de partida así rompe el percentil 95 de AC-05. |

La distancia de cada nodo (`depth`) se obtiene agrupando por el nodo alcanzado con `min(length(path))`: el planificador mantiene la expansión con poda, porque solo necesita el camino más corto a cada nodo. Medido en los mismos 16 rombos: 115 accesos, igual que con `DISTINCT`. `SHORTEST 1` hacia cada nodo cuesta 4297, y calcular primero los nodos y después la distancia a cada uno, 3456.

Cuando la consulta agrupa por otra cosa (en el elevado, la distancia del prerrequisito y no la del camino), el planificador vuelve a enumerar caminos (`VarLengthExpand(All)`). Ahí se calculan antes los nodos distintos por cada punto de partida.

## 4. Profundidad máxima (RF-11)

Los recorridos transitivos llevan una sola cota, declarada como una constante con nombre en la cabecera del módulo de navegación, fuera del Cypher (ADR-014: la especificación es lo que es dato). No va en el esquema del grafo, que declara lo que el grafo admite (ADR-008). Valor provisional: 10. Se cambia con un commit. El script de medición reporta la cota usada y la mayor profundidad alcanzada en el piloto; si son iguales, hubo recorte.

Con las consultas de la sección 3, la cota no cambia el costo: acota el tamaño de la respuesta.

| Alternativa | Motivo del descarte |
|---|---|
| Parámetro `depth` en cada ruta | Más superficie que probar, y la medición usaría el máximo de todos modos. |
| Variable de entorno | El valor no queda en el historial y la medición podría hacerse con uno distinto al desplegado. |
| Sin cota | RF-11 la exige. |

## 5. Rutas

Bajo `/api`, públicas (ADR-013), en un router distinto del de operación, que exige el token a nivel de router. La clave va como parámetro de consulta y no en la ruta, porque las claves de referencia son IRIs con `#` y `/`.

Una clave que no existe, o que es de otra clase que la que la ruta espera (un curso en `/api/concepts/prerequisites`), responde 404; el mensaje dice qué clase esperaba. 422 queda para los parámetros mal formados.

| Ruta | Requisito | Patrón medido |
|---|---|---|
| `GET /api/search?q=` | RF-18 | — |
| `GET /api/nodes?key=` | Detalle de un nodo | — |
| `GET /api/concepts/prerequisites?key=` | RF-11 | — |
| `GET /api/courses/prerequisites?key=` | RF-12 | Prerrequisito entre cursos |
| `GET /api/elements/location?key=` | RF-13 | Área de un concepto |
| `GET /api/elements/resources?key=` | RF-14 | Recursos agregados sobre las partes |
| `GET /api/learning-path?key=&grain=` | RF-15 | Prerrequisito elevado |
| `GET /api/concepts/specializations?key=` | RF-16 | Cierre de especialización |

Las rutas solo leen, en sesiones de lectura. Su Cypher es de forma fija y solo recibe valores; las etiquetas y los tipos de arista salen del esquema del grafo.

| Alternativa | Motivo del descarte |
|---|---|
| Lenguaje de consulta expuesto (Cypher, GraphQL) | Sin patrones fijos, AC-05 no tiene qué medir; y exponer Cypher abre la base. |
| OGM (neomodel) | Es un ORM de grafos; la restricción del asesor lo excluye. |
| La clave en la ruta (`/api/nodes/{key}`) | Las IRIs llevan `#` y `/`. |

## 6. Patrones

Nodos de partida: aquellos desde los que el script de medición ejecuta cada patrón (Tabla 15: todos los válidos).

| Patrón | Qué calcula (derivación del Paso 5) | Nodos de partida |
|---|---|---|
| Prerrequisito entre cursos (PC2) | El curso X precede al curso Z si X enseña un concepto que Z requiere. La respuesta trae los conceptos que Z enseña y los que requiere (RF-12), y los cursos que enseñan estos últimos. | Todo `Course` |
| Área de un concepto (PC3) | Subir por `PART_OF` hasta el área. La ruta, para cualquier elemento, trae también su composición descendente (RF-13), sin cota, y los `HAS_PREREQUISITE` entre sus partes, que dan el orden en que conviene aprenderlas (PC4). El patrón medido parte de los conceptos. | Todo `Concept` |
| Recursos agregados (PC5) | Los recursos que tratan sobre X (`IS_ABOUT`) más los que tratan sobre cualquier parte de X (`PART_OF` hacia abajo). La respuesta trae las partes que llevan a cada recurso y el tipo de cada recurso (`HAS_RESOURCE_TYPE`), por el que PC5 filtra. | Todo elemento de conocimiento y todo curso |
| Prerrequisito elevado (PC6) | Ver abajo. | Cada par (objetivo, grano) |
| Cierre de especialización (PC7) | `SPECIALIZES` transitivo en ambos sentidos, con la cota. | Todo `Concept` |

RF-11 (prerrequisitos de un concepto, transitivo y con la cota) no es uno de los cinco patrones medidos.

### Prerrequisito elevado (RF-15, PC6)

PC6 pregunta qué debe aprenderse para abordar un concepto, tema, curso o área. El **objetivo** es ese elemento, y también una unidad de conocimiento, que se trata como un tema o un área; el **grano** es la unidad en que se responde: tema, curso o área (tesis, l. 1035).

1. Bajar del objetivo a sus conceptos: él mismo si es un concepto, sus partes por `PART_OF` si es un tema, una unidad o un área, los que enseña si es un curso.
2. Seguir sus prerrequisitos por `HAS_PREREQUISITE`, con la cota, y descartar los que ya están dentro del objetivo.
3. Subir cada prerrequisito al grano: a su tema o a su área por `PART_OF`, o a los cursos que lo enseñan. Con grano curso, el propio curso objetivo queda fuera.

Con objetivo curso y grano curso, este patrón da el prerrequisito entre cursos derivado de las dependencias conceptuales (tesis, l. 998), que complementa el del Paso 5 por concepto requerido.

| Alternativa | Motivo del descarte |
|---|---|
| Grano igual al nivel del objetivo | No responde qué cursos llevar para abordar un tema. |
| Objetivo limitado a la lista de PC6 | La unidad es el nivel en que el estudiante recorre CS2023, y bajar de ella a sus conceptos es lo mismo que desde un tema o un área. Cuesta más pares (objetivo, grano) en la medición. |
| Todos los granos en una respuesta | La respuesta más pesada, y el patrón medido deja de ser «elevar a un grano». |
| Ampliar el prerrequisito entre cursos con `HAS_PREREQUISITE` | Cambia la derivación del Paso 5; el elevado con grano curso ya la cubre. |

### Recursos de los temas (RF-14)

La ingesta declara `IS_ABOUT` del sílabo a cada tema de su salida, además de a su curso. DD-05 define el tema como lo que el material presenta como unidad, semana o encabezado de un sílabo: el sílabo lo aborda directamente (DD-07). La arista se arma con los temas de la salida, sin que el modelo de lenguaje la proponga, y no repite la procedencia: un tema que ya existía conserva la suya, pero el segundo sílabo también trata sobre él.

Un concepto no tiene partes: sus recursos son los que tratan sobre él, y en el MVP no hay ninguno. R6 llega a los del tema subiendo con RF-13.

| Alternativa | Motivo del descarte |
|---|---|
| `IS_ABOUT` solo al curso | Con el sílabo como único tipo de recurso, el patrón devuelve vacío para todo elemento de conocimiento. |
| Sumar los sílabos de los cursos que enseñan una parte | Extiende la derivación del Paso 5. |
| `IS_ABOUT` del sílabo a cada concepto | Repite lo que dice `TEACHES_CONCEPT`, y el sílabo aborda conceptos dentro de sus temas. |

## 7. Búsqueda (RF-18)

Un índice de texto completo con el analizador `standard-folding`, declarado en el esquema del grafo y creado por la carga. Cubre las etiquetas preferidas de los elementos de conocimiento y de los cursos, y el código del curso.

Medido el 2026-10-08 en `neo4j:5.26.28-community`: el índice existe en Community; ignora tildes y mayúsculas; busca palabras enteras salvo con comodín (`arbol*`); los comodines no pasan por el analizador (`árbol*` no encuentra nada). Por eso la API quita las tildes del texto, lo pasa a minúsculas, lo separa en palabras donde el tokenizador del índice lo separa y agrega `*` a cada una antes de consultar con `db.index.fulltext.queryNodes`. El tokenizador separa en todo lo que no es letra ni dígito, salvo un punto, un apóstrofo o un guion bajo entre ellos: «node.js», «802.11» y «o'reilly» son una palabra cada una (medido: separándolas, esos nombres escritos completos no se encuentran a sí mismos). Ninguno de esos caracteres está entre los especiales de la sintaxis de Lucene (documentación del analizador sintáctico clásico de Lucene, «Escaping Special Characters»), así que no queda nada que escapar. Todas tienen que aparecer (cada una con `+`, no con el OR por omisión de Lucene), salvo las palabras vacías. Devuelve los nodos ordenados por puntaje y, a igual puntaje, por clave, con un máximo de 20.

**Palabras vacías.** Medido el 2026-10-09: `standard-folding` descarta al indexar 33 palabras vacías del inglés, y varias son también palabras del español («a», «no», «as»). Exigirlas no encuentra nada: `+programacion* +orientada* +a* +objetos*` no encuentra «Programación orientada a objetos». La API pide la lista a la base (`db.index.fulltext.listAvailableAnalyzers`, para el analizador declarado) y deja esas palabras como cláusulas opcionales, que solo suman puntaje. Así «an», sola, sigue sirviendo de prefijo de «Análisis».

| Alternativa | Motivo del descarte |
|---|---|
| `toLower(...) CONTAINS` | No ignora tildes: `arbol` no encuentra «Árboles». Y recorre todos los nodos. |
| Analizador `spanish` | Con lematización y palabras vacías; no evaluado. |
| Escapar la sintaxis de Lucene en cada palabra separada por espacios | El índice parte «cliente-servidor» en dos palabras; `cliente\-servidor*` no encuentra nada (medido con `e\-learning*`). |
| Quitar las palabras vacías de la consulta | Una palabra vacía que se está escribiendo puede ser el prefijo de otra («an» de «Análisis»). |
| Analizador `standard-no-stop-words` | No quita tildes. |
| Lista de palabras vacías escrita en el código | Puede separarse de la del analizador; la base ya la declara. |

## 8. Medición de AC-05

`scripts/measure_navigation.py` usa las mismas funciones de consulta que las rutas. Las pruebas comprueban resultados; el script mide.

El tiempo en el motor es la suma de `result_available_after` y `result_consumed_after` del `ResultSummary` del driver, medidos por el servidor. El reporte lleva, por patrón, la mediana y el percentil 95 de diez ejecuciones desde cada nodo de partida, la primera ejecución en frío aparte y sin umbral, el tamaño del grafo, el entorno (procesador, memoria, versión del motor), la cota de profundidad y la mayor profundidad alcanzada.

Ese tiempo incluye la compilación del plan. Medido el 2026-10-09 en Enterprise, con solo el backbone: vaciada la caché de planes, la primera ejecución del elevado con grano área tardó 1541 ms y la de los recursos agregados, 897 ms; las cinco siguientes de cada una, entre 0 y 3 ms. El driver da milisegundos enteros, así que la resolución del reporte es de 1 ms.

**En frío.** Es la primera ejecución de cada patrón con la caché de planes de consulta vacía: el script la vacía al empezar, con `db.clearQueryCaches()`. No reinicia el motor. Neo4j vuelve a cargar al arrancar las páginas que tenía en uso (`db.memory.pagecache.warmup.enable`, que `SHOW SETTINGS` da por activo en las dos ediciones), así que un reinicio tampoco deja fría la caché de páginas, y un grafo del orden de mil nodos cabe entero en ella.

**Orden.** Por patrón, una ronda de calentamiento y diez rondas medidas. Cada ronda ejecuta el patrón una vez desde cada nodo de partida, en orden de clave; en el elevado, cada clave con sus tres granos, en el orden tema, curso, área. Entre dos ejecuciones desde el mismo nodo pasan todas las demás. La primera ejecución de la ronda de calentamiento es la ejecución en frío. En el elevado cada grano es una consulta distinta, con su propio plan: el reporte guarda los tiempos de la ronda de calentamiento, en los que se ve la compilación de los tres.

**Estadísticos.** Por patrón, sobre todas sus ejecuciones medidas: la mediana; el percentil 95 por rango más cercano, es decir, el valor en la posición ⌈0,95·n⌉ de los tiempos ordenados; y el máximo. El patrón cumple si la mediana y el percentil 95 quedan por debajo de 1000 ms. Un patrón sin nodos de partida se reporta sin cifras.

**Reporte.** Un JSON en `var/measurements/ac05-<fecha y hora>.json` con: los tiempos de cada ejecución, por nodo de partida; el resumen por patrón; el tamaño del grafo, en nodos por etiqueta y aristas por tipo; el entorno; la cota; y la mayor profundidad alcanzada, en el elevado y en la especialización, pues la ubicación tiene profundidad fija. El script imprime además el resumen como tabla Markdown. `var/` no se versiona: la medición formal se copia a la tesis.

**Entorno.** Del motor, lo que él mismo informa: versión y edición (`dbms.components`); procesadores, memoria y sistema operativo que ve (`dbms.queryJmx`); y tamaño del heap y de la caché de páginas (`SHOW SETTINGS`). Del host, el modelo del procesador, que el motor no informa.

**Planes.** El reporte lleva los operadores del plan de cada consulta medida (`EXPLAIN`) y señala una expansión variable sin poda o un recorrido de todos los nodos, de la base o de una etiqueta. Así, la corrida formal en Community comprueba lo de la sección 3. Verificado el 2026-10-09 en un contenedor temporal de `neo4j:5.26.28-community` con el backbone: en los siete planes, toda expansión variable es `VarLengthExpand(Pruning,BFS,All)` y el nodo de partida se busca con `NodeUniqueIndexSeek`. Una prueba exige lo mismo sobre un grafo pequeño que cubre los cinco patrones.

| Alternativa | Motivo del descarte |
|---|---|
| Reiniciar el motor antes de medir | Paso manual fuera del script; el precalentado de páginas lo deja menos frío de lo que parece. |
| Las diez ejecuciones de un nodo seguidas | Mide la misma consulta repetida: el escenario más optimista. |
| Percentil interpolado | Puede dar un tiempo que no se observó; con resolución de 1 ms no cambia la conclusión. |
| Reporte versionado en el repositorio | Es medición, no especificación. |
| Tiempo medido en el cliente | Suma serialización y transporte, que AC-05 excluye. |

## 9. Detalle de un nodo

Devuelve el nodo con todas sus propiedades, sus vecinos directos y algunos vecinos de esos vecinos: lo que rodea al elemento en pantalla y desde donde el estudiante sigue explorando, a la manera de una enciclopedia. Cuenta como vecino todo nodo unido por una arista de cualquier tipo salvo `WAS_DERIVED_FROM`, que llega por la regla de la sección 2: de lo contrario, el detalle de CS2023 traería los 179 elementos de referencia.

Dos cotas, declaradas junto a la de profundidad, acotan la respuesta: un máximo de vecinos directos (provisional: 25) y un máximo de vecinos de segundo nivel por cada vecino directo (provisional: 5), sin contar el nodo ni sus vecinos directos. Cuando hay más, se eligen en un orden fijo, para que la misma consulta dé siempre la misma respuesta: primero los unidos por una arista que sale del nodo, después por tipo de arista, por nombre en español y por clave. Las aristas que salen dicen de qué es parte el nodo, qué requiere y de qué es tipo: son pocas, y un recorte por nombre las perdería entre las partes de un tema. La respuesta indica, por nodo, si tiene vecinos que no están en la respuesta (`more_neighbors`), para que R6 ofrezca expandirlo con otra llamada.

No es uno de los cinco patrones medidos: su recorrido tiene longitud fija y no deriva un cierre ni un agregado.

| Alternativa | Motivo del descarte |
|---|---|
| Solo el nodo y su procedencia | R6 no tendría desde dónde explorar sin una llamada por vecino. |
| Solo los vecinos directos | Un nodo con pocos vecinos se ve aislado en pantalla. |
| Vecinos sin cota | Un área, un curso o un recurso arrastran cientos de nodos. |

## 10. Evidencia del prerrequisito elevado

La respuesta del elevado trae, además de los temas, cursos o áreas del grano, los conceptos prerrequisito y las aristas que los justifican: `HAS_PREREQUISITE` entre conceptos, y `PART_OF` o `TEACHES_CONCEPT` hacia el grano. Es la regla de la sección 1, y es lo que permite mostrar por qué un curso precede a otro.

Del lado del objetivo trae los conceptos de los que sale una arista `HAS_PREREQUISITE` hacia fuera de él, y lo que los une con el objetivo dentro de su partonomía; no todos sus conceptos. Con grano área, trae también el tema y la unidad de cada prerrequisito, por los que pasa su `PART_OF` hasta el área.

`depth` distingue la respuesta de la evidencia: es 0 en el objetivo y en lo que está dentro de él; en un prerrequisito, su distancia al objetivo; en un tema, curso o área del grano, la de su prerrequisito más cercano. El tema y la unidad intermedios del grano área no la llevan.
