# 0003 — Arquitectura preliminar del algoritmo de ingesta, validada contra la literatura

- **Fecha:** 2026-07-31
- **Estado:** arquitectura preliminar de un spike. **No es un ADR** y no pretende serlo; se espera que cambie al implementar.
- **Sustentabilidad:** mixta, marcada fuente por fuente más abajo. La estructura del pipeline y la terminología sí son sustentables; los números concretos vienen de preprints de arXiv y deben tratarse como indicativos hasta que pasen revisión por pares.
- **Afecta a:** R4 (módulo de KG y pipeline de ingesta).

---

## 1. La arquitectura tal como está planteada

> Sílabos en PDF → parseo con Docling consciente de layout → extracción con LLM de salida estructurada, validada contra la ontología con Pydantic → enlace de entidades contra el backbone CS2023 → Cypher MERGE parametrizado generado de forma determinista. El LLM nunca escribe en la base.

Más una consideración añadida: recuperar un subgrafo de lo que ya existe para detectar nodos ya presentes y trabajar sobre ellos, en vez de proponer duplicados.

---

## 2. Lo que la literatura valida

### 2.1 La forma del pipeline es la canónica

La revisión de Bian (2025) sobre construcción de grafos de conocimiento con LLM describe el pipeline clásico en tres capas: **ingeniería de ontología → extracción de conocimiento → fusión de conocimiento**. La arquitectura planteada mapea uno a uno sobre esas tres capas, con R1 cubriendo la primera. No es una estructura improvisada.

*Sustentabilidad: media. Preprint de arXiv (2510.20345), sin revisión por pares aún.*

### 2.2 "Ontología como restricción de primera clase" tiene evidencia cuantitativa fuerte

OntoMetric (Yu et al., UNSW Sydney / Adelaide / CSIRO Data61) construye grafos de conocimiento ESG desde documentos regulatorios con una arquitectura **muy cercana** a la planteada aquí:

| OntoMetric | Equivalente en este proyecto |
|---|---|
| Segmentación consciente de estructura | Docling consciente de layout |
| Extracción con LLM restringida por la ontología | Salida estructurada validada contra la T-Box |
| Identificadores deterministas | IRI como clave, MERGE idempotente |
| **Validación en dos fases**: verificación de tipos semánticos + comprobación de esquema basada en reglas | Validación previa a la escritura + consultas de integridad |
| Preservación de procedencia a nivel de segmento y página | Propiedad `layer` y `wasDerivedFrom` |

Los números que reporta son el argumento más fuerte disponible para justificar la restricción ontológica: **65–90 % de exactitud semántica y más del 80 % de conformidad de esquema, frente a 3–10 % en extracción no restringida**. Es un orden de magnitud, no una mejora marginal.

Que exista un trabajo tan cercano es bueno y malo a la vez: valida el enfoque, y obliga a citarlo y a diferenciarse de él. La diferenciación disponible: dominio distinto (currículo, no ESG), alineación con un estándar disciplinar (CS2023), capa operativa LPG en vez de triplestore, y la restricción explícita de que el LLM nunca escribe.

*Sustentabilidad: media. arXiv 2512.01289, 1 dic 2025 (v2: 26 ene 2026). Preprint.*

### 2.3 Docling sigue siendo una elección vigente

Docling está mantenido por IBM Research bajo la LF AI & Data Foundation, con el modelo `granite-docling-258M` (Apache-2.0) y un modelo de layout por defecto (`heron`) que reporta +23,5 % de mAP. Reconocimiento de estructura de tablas vía TableFormer, recuperación de orden de lectura y manejo de layouts científicos multicolumna. Para sílabos en PDF con tablas, es la opción correcta hoy.

*Sustentabilidad: alta para la elección técnica (proyecto de fundación, documentación oficial). Los números de rendimiento son del proyecto, no de un tercero independiente.*

### 2.4 Salida estructurada es el patrón estándar — con una advertencia importante

Pydantic más decodificación restringida es el patrón habitual, y los proveedores principales reportan conformidad de esquema cercana al 100 %. Pero hay un matiz que **refuerza** la decisión de validar aparte: la evidencia disponible indica que forzar formato puede **reducir la exactitud** en escenarios complejos respecto a extracción por prompt libre, y la recomendación explícita es no confiar nunca en la salida del LLM aunque venga estructurada.

Es decir: la salida estructurada garantiza que el JSON *tenga la forma correcta*, no que el contenido *sea correcto*. La capa de validación contra la ontología no es redundante con Pydantic; cubre exactamente lo que Pydantic no cubre.

*Sustentabilidad: media-alta. JSONSchemaBench (arXiv 2501.10868) y "Let Me Speak Freely?" (arXiv 2408.02442) son preprints, pero el punto es metodológico y no depende de sus cifras.*

---

## 3. Lo que la literatura corrige

### 3.1 Esto no es GraphRAG

**GraphRAG** (Edge et al., Microsoft Research, 2024 — *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*) hace lo contrario de lo que se necesita aquí: **deriva** un grafo de conocimiento a partir de documentos fuente, agrupa entidades en comunidades jerárquicas, pregenera resúmenes de esas comunidades, y los usa para responder preguntas globales del tipo "¿cuáles son los temas principales del corpus?". Es *query-focused summarization*, no anclaje de extracción.

Aquí el grafo **ya existe** y se quiere usar para condicionar la extracción. Citar GraphRAG como método invitaría a un revisor a preguntar por qué se cita algo que resuelve otro problema.

*Sustentabilidad: alta. Publicación de Microsoft Research, ampliamente citada.*

### 3.2 El término correcto tiene dos niveles

La literatura distingue dos cosas que la formulación actual junta en "enlace de entidades":

- **Enlace de entidades (*entity linking*)**, cuyo pipeline canónico es **detección de menciones → generación de candidatos → desambiguación de entidades** (Sevgili et al., *Neural Entity Linking: A Survey*, Semantic Web Journal, 2022). Es lo que ocurre al conectar una mención del sílabo con un nodo del backbone.
- **Fusión de conocimiento (*knowledge fusion*)**, término que usa la revisión de Bian (2025) para la tercera capa: reconciliar lo extraído con lo que ya está en el grafo.

En este pipeline ocurren **las dos, en secuencia**: primero se enlaza cada mención contra el backbone, luego se fusiona el resultado con el grafo existente mediante MERGE. Nombrarlas por separado da referencias sólidas para cada una.

Nota: "recuperar un subgrafo para anclar" es **generación de candidatos**, la segunda etapa del enlace de entidades. Ese es su nombre.

*Sustentabilidad: alta. Survey en revista con revisión por pares.*

### 3.3 El término global ya estaba bien elegido

La tesis ya llama al procedimiento ***Ontology Population*** (Tabla de R4). Es el término estándar y es correcto. Conviene usarlo como paraguas y reservar "enlace de entidades" y "fusión" para las etapas internas.

### 3.4 Recuperar el subgrafo no evita que el Cypher crezca

Dos preocupaciones distintas que conviene no mezclar:

- **Alcance de la recuperación** → acota lo que el LLM ve, y por tanto cuántas entidades distintas puede proponer. Controla la **calidad del anclaje** y evita duplicados inventados.
- **Volumen del Cypher** → lo controla el proyector, con `UNWIND` más `MERGE` por lotes. Ya está implementado y no depende del anclaje.

El subgrafo recuperado no impide que el Cypher explote; impide que el LLM proponga nodos que ya existen.

---

## 4. Lo que queda abierto

La tesis ya especifica la estrategia de reconciliación: un concepto extraído que **coincide** con un nodo del backbone se enlaza en lugar de duplicarse; si no hay correspondencia se crea como instancia institucional colgada de su unidad de conocimiento; y el pipeline nunca crea ni modifica nodos de la capa de referencia.

Lo que la literatura señala como la parte difícil, y que queda por definir al implementar:

1. **Qué significa "coincide".** Es la función de emparejamiento del enlace de entidades: coincidencia léxica, similitud de embeddings, o un umbral combinado. De esto depende toda la precisión del pipeline, y es donde los trabajos revisados en el EdA declaran sus fallos (sobre-extracción y control de granularidad en Xu & Che, 2025; relaciones ambiguas en Li et al., 2026).
2. **Deduplicación dentro de la capa institucional.** La reconciliación está descrita contra el backbone, que es estático. Pero los `Topic` y `Concept` acuñados desde el sílabo A también deben reconciliarse contra los acuñados desde el sílabo B, y ese conjunto **crece con cada ingesta**. La literatura reciente trata esto como un paso propio, con detección de conflictos separada de la resolución de conflictos.
3. **Umbral de decisión y qué pasa cuando no se alcanza.** Si ninguna estrategia de emparejamiento supera el umbral, ¿se crea el nodo, se descarta, o se marca para revisión humana? El EdA concluye que la supervisión experta sigue siendo indispensable; este es el punto natural donde insertarla.

---

## 5. Referencias

| Fuente | Tipo | Sustentabilidad |
|---|---|---|
| Edge, D. et al. (2024). *From Local to Global: A Graph RAG Approach to Query-Focused Summarization*. Microsoft Research. | Publicación | Alta |
| Sevgili, Ö. et al. (2022). *Neural Entity Linking: A Survey of Models Based on Deep Learning*. Semantic Web Journal. | Revista con revisión por pares | Alta |
| Bian, H. (2025). *LLM-empowered Knowledge Graph Construction: A Survey*. arXiv:2510.20345, 23 oct 2025. | Preprint | Media |
| Yu, M., Rabhi, F., Xia, B., Yang, Z., Tan, F., Lu, Q. (2025). *OntoMetric: An Ontology-Driven LLM-Assisted Framework for Automated ESG Metric Knowledge Graph Generation*. arXiv:2512.01289, 1 dic 2025 (v2: 26 ene 2026). | Preprint | Media |
| *JSONSchemaBench* arXiv:2501.10868; *Let Me Speak Freely?* arXiv:2408.02442. | Preprints | Media |
| Docling — docling.org, LF AI & Data Foundation. | Documentación oficial | Alta para la elección; sus métricas son autoreportadas |

**Nota operativa, no de tesis (gris):** la tabla de R4 fija el LLM como "GPT-4o/Gemini". A julio de 2026 conviene revisar esa elección antes de implementar; no afecta a la arquitectura, que es agnóstica al modelo, pero sí a los resultados que se reporten.
