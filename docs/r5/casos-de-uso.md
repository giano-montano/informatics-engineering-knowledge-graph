# Casos de uso del mecanismo de navegación

Casos de uso **comunes a las tres propuestas**. Dicen qué quiere lograr cada actor y qué responde
el sistema, sin suponer pantallas ni tecnología: son casos de uso esenciales (Constantine y Lockwood,
*Software for Use*, 1999). Cómo los resuelve cada interfaz está en la sección «Flujos» del README de
cada propuesta: un flujo por caso de uso.

- **Actores:** el **estudiante**, que consulta y navega el grafo sin escribir en él, y el **operador**,
  que carga documentos y revisa la ingesta.
- **Condición de todas las pantallas (RF-22):** lo que viene del estándar CS2023 y lo que viene de los
  sílabos se distingue a simple vista, y no solo por el color.
- **Escenario:** los pasos esenciales de cada caso de uso, en dos columnas, intención y respuesta. La
  palabra «flujo» se reserva para los pasos de una interfaz concreta.

## Resumen

| Caso de uso | Actor | Necesidad que atiende (E16) | Pregunta de competencia | Requisitos | Ruta de la API |
|---|---|---|---|---|---|
| CU-1 · Encontrar por dónde empezar | Estudiante | Descubrir temas (52,6 %) | — | RF-18, RF-19 | `/api/search`; portada: ruta nueva |
| CU-2 · Explorar lo que rodea a un elemento | Estudiante | Entender cómo se conectan las áreas (61,0 %) | — | RF-19 | `/api/nodes` |
| CU-3 · Saber qué conceptos necesito antes de aprender uno | Estudiante | Ver qué conceptos previos necesito (83,1 %) | PC1 | RF-11, RF-20 | `/api/concepts/prerequisites` |
| CU-4 · Saber qué pide un curso y qué curso conviene llevar antes | Estudiante | Ver qué conceptos previos necesito (83,1 %) | PC2 | RF-12 | `/api/courses/prerequisites` |
| CU-5 · Ubicar un concepto o tema dentro de la carrera | Estudiante | Entender cómo se conectan las áreas (61,0 %) | PC3 | RF-13, RF-20 | `/api/elements/location` |
| CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo | Estudiante | Ver qué conceptos previos necesito (83,1 %) | PC4 | RF-13 | `/api/elements/location` |
| CU-7 · Encontrar material de estudio sobre algo | Estudiante | Encontrar recursos de estudio (72,1 %) | PC5 | RF-14, RF-20 | `/api/elements/resources` |
| CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas | Estudiante | Ver qué conceptos previos necesito (83,1 %) | PC6 | RF-15, RF-20 | `/api/learning-path` |
| CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene | Estudiante | Descubrir temas (52,6 %) | PC7 | RF-16 | `/api/concepts/specializations` |
| CU-10 · Comprobar de dónde sale un dato | Estudiante | — | — | RF-21 | procedencia en toda respuesta; `/resources/{key}` |
| CU-11 · Cargar un documento y revisar su ingesta | Operador | — | — | RF-23 | rutas de operación, con token |

Las preguntas de competencia son las de R1 (Paso 1 de Ontology Development 101,
`ontology/aplicacion_od101_r1.md`). Los requisitos son los de
`docs/requisitos-funcionales-de-referencia.md`, y las rutas, las de
`docs/diseño-de-las-rutas-de-navegación.md` §5.

## CU-1 · Encontrar por dónde empezar

El estudiante llega con un nombre en mente, o sin ninguno, y necesita un elemento desde el cual navegar.

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Escribe un nombre, o parte de él. | Muestra los elementos cuyo nombre coincide (hasta 20), con su clase y su origen. |
| O pide ver lo que hay, sin escribir. | Muestra las áreas de la carrera y los cursos, y distingue las áreas que ya tienen contenido de los sílabos. |
| Elige uno. | Lo muestra como elemento en foco. |

Si nada coincide, el sistema lo dice y ofrece recorrer las áreas.

## CU-2 · Explorar lo que rodea a un elemento

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Con un elemento en foco, quiere ver con qué se relaciona. | Muestra sus vecinos directos, el nombre de cada relación y algunos vecinos de esos vecinos. |
| Elige un vecino. | El vecino pasa a estar en foco; el sistema permite volver al anterior. |
| Quiere ver más de lo que se muestra. | Indica qué vecinos tienen más relaciones y las agrega a pedido. |

## CU-3 · Saber qué conceptos necesito antes de aprender uno

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Elige un concepto y pregunta qué necesita saber antes. | Muestra sus prerrequisitos, ordenados por distancia: los directos y los que están más pasos atrás. |
| Quiere saber por qué uno de ellos va antes. | Muestra la relación que lo justifica y su fuente (CU-10). |

Si el concepto no tiene prerrequisitos registrados, el sistema lo dice y muestra qué depende de él.

## CU-4 · Saber qué pide un curso y qué curso conviene llevar antes

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Elige un curso. | Muestra los conceptos que enseña y los que asume. |
| Pregunta qué curso conviene llevar antes. | Muestra los cursos que enseñan lo que este asume, cada uno con esos conceptos como evidencia. |

## CU-5 · Ubicar un concepto o tema dentro de la carrera

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Con un concepto o un tema en foco, pregunta dónde está. | Muestra la cadena tema › unidad › área de CS2023 a la que pertenece. |
| Elige un eslabón. | Lo pone en foco. |

## CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Elige un tema, una unidad o un área y pregunta qué contiene. | Muestra sus partes, nivel por nivel: unidades, temas y conceptos. |
| Pregunta en qué orden conviene aprenderlas. | Agrupa los conceptos en pasos según sus prerrequisitos internos. |

## CU-7 · Encontrar material de estudio sobre algo

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Elige un elemento o un curso y pide material de estudio. | Muestra los recursos que tratan sobre él o sobre sus partes, con su tipo y por qué parte llega cada uno. |
| Elige un recurso. | Lo abre. |

Un concepto no tiene recursos propios: el sistema lo dice y ofrece los de su tema. El filtrado por
tipo de recurso que menciona PC5 está fuera de alcance; hoy el único tipo es el sílabo.

## CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Elige una meta (un concepto, tema, unidad, área o curso). | Muestra lo que conviene aprender antes, ordenado por distancia. |
| Elige verlo por temas, por cursos o por áreas. | Agrupa ese camino en temas, cursos o áreas. |
| Pregunta por qué un paso va antes que otro. | Muestra las relaciones que lo justifican, con su fuente (CU-10). |

Si el camino sale vacío, el sistema explica por qué. Si la meta es un curso, remite a CU-4.

## CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Con un concepto en foco, pregunta por sus tipos. | Muestra el concepto más general del que es un tipo y los conceptos que son tipos de él. |

## CU-10 · Comprobar de dónde sale un dato

| Intención del estudiante | Respuesta del sistema |
|---|---|
| Ante un elemento o una relación, pregunta de dónde sale. | Nombra el documento que la afirma: el sílabo del curso, o CS2023. |
| Pide verlo. | Abre el documento. |

## CU-11 · Cargar un documento y revisar su ingesta

| Intención del operador | Respuesta del sistema |
|---|---|
| Se identifica con su token. | Da acceso a las funciones de operación, o lo rechaza. |
| Carga un documento con su tipo, el código y el nombre del curso. | Registra una corrida y la deja pendiente. |
| Sigue el estado de sus corridas. | Muestra cada corrida con su estado y su resultado. |
| Revisa una corrida. | Muestra sus descartes, si los hubo, y el reporte de auditoría por regla. |
