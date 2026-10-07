# Deuda

Discrepancias directas entre el código y la documentación, o entre documentos,
que exigen una corrección. No entran opiniones de diseño ni mejoras posibles:
esas van a un ADR o se descartan.

Antes de anotar algo aquí se comprueba que el anexo, la tesis o un ADR no lo
aclaren ya. Si mandan dos fuentes, prevalecen los ADR y el modelo C4 sobre la
tesis y el anexo, y el desfase se anota como deuda del documento que quedó
atrás.

Cada entrada dice qué está en conflicto y qué hay que decidir. **No trae la
decisión**: la decisión va a un ADR o a la corrección del documento, y la
entrada se cierra apuntando a ese lugar.

Origen de las entradas D-01 a D-08: auditoría del commit `1100451` (carga del
backbone), 2026-10-05.

---

## D-01 · RI-07 en la carga no está «validado en R2»

**Estado:** cerrada (2026-10-07), sin cambios: la afirmación es verdadera para
el R2 entregado, y un TTL editado ya no es R2 y lo detecta la auditoría de la
carga · **Gravedad:** baja

- **Alcance real.** El backbone entregado cumple la afirmación: sus 162
  unidades usan `knowledgeUnitInKnowledgeArea` y ninguna usa `isPartOf`.
  Lo que falla es la afirmación como garantía general, para un TTL futuro o
  editado. Si ese caso ocurre, la auditoría de la misma carga lo detecta
  (código 1) antes de cualquier ingesta.
- **Lo que dicen los documentos.** Anexo, Tabla 3, fila RI-07, columna de la
  carga: «Validado en R2». La tesis, §Reglas de integridad: «En la carga […]
  RI-07 descansa en la verificación con HermiT de R2».
- **Lo que pasa.** En la T-Box, solo `knowledgeUnitInKnowledgeArea` es
  funcional; `isPartOf` no lo es (`ontologia_informatica.ttl`, líneas 98-116).
  Por eso un backbone que afirme `:KU-X :knowledgeUnitInKnowledgeArea :KA-1` y
  `:KU-X :isPartOf :KA-2` es consistente para HermiT. Pero la proyección
  colapsa las dos propiedades en `PART_OF`, y el grafo queda con una unidad en
  dos áreas. La carga no lo impide: `LOAD_RULES` no incluye RI-07 y el
  validador no tiene una comprobación para esa regla
  (`src/iekg/core/validator.py:13`). Solo la auditoría lo detecta, después de
  vaciar y escribir la base.
- **Por qué es deuda.** Para RI-05, el anexo ya usa este mismo argumento: «R2
  no cubre los errores de la proyección». Con RI-07 pasa lo mismo, por culpa
  del colapso de la partonomía, y el anexo no lo dice.
- **Qué hay que decidir.** Hay dos salidas:
  - Corregir el anexo y la tesis para que digan «se detecta en la auditoría».
  - Agregar una comprobación de RI-07 al validador para la carga. Cambia la
    Tabla 3 del anexo y la Tabla 20 de la tesis, así que va en un ADR.

## D-02 · La condición de frontera de capas no tiene mecanismo

**Estado:** cerrada (2026-10-07), sin editar entregables. La impide la forma
de la escritura: el origen de cada arista debe tener la capa de la escritura
(`repository.py`, `_edge_template`). La auditoría la detecta como RI-09 (ver
D-05). Queda un requisito para el ADR del extractor, anotado en su
descripción en `docs/architecture/model.c4` ·
**Gravedad:** alta (para la ingesta)

- **Lo que dicen los documentos.**
  - Anexo, condición 6: «toda arista que escribe [la ingesta] sale de un nodo
    institucional».
  - Anexo, Tabla 3: RI-07 en la ingesta «no aplica: la condición de frontera
    de capas impide a la ingesta escribir aristas de unidad a área».
  - Anexo, Tabla 2: el par KnowledgeUnit → KnowledgeArea de `PART_OF` lo
    escribe solo la carga.
- **Lo que pasa.** La Tabla 20 de la tesis y la enmienda de ADR-005 reparten
  los mecanismos entre las reglas, pero la condición 6 no es una regla y
  ningún mecanismo la recibe. RM-02, la «forma consultable» de la frontera,
  solo prohíbe aristas de referencia a institucional
  (`validator.py:_check_layer_boundary`). Tomemos un lote de ingesta que trae
  `(KU existente)-[:PART_OF]->(KA existente)`, con ambos nodos de referencia
  en la instantánea:
  - pasa RI-05, porque el par está admitido;
  - pasa RM-02, porque la arista va de referencia a referencia;
  - pasa RI-08, porque no hay nodos nuevos.

  El repositorio lo escribe. Si la unidad ya tenía área, la auditoría encuentra
  RI-07 después del commit y la corrida queda *detenida por auditoría*. El
  extractor devuelve claves de nodos existentes (ADR-011), así que este camino
  es alcanzable.
- **Por qué es deuda.** El «no aplica» de RI-07 en la ingesta descansa en una
  condición que nada hace cumplir.
- **Qué hay que decidir.** Primero, si la condición 6 se impide al escribir.
  Si se impide, falta elegir cómo: con una comprobación del validador en la
  ingesta (que el origen de cada arista sea un nodo nuevo o institucional) o
  ampliando RM-02. Después, si la auditoría la comprueba. Es posible: una
  arista que sale de un nodo de referencia y lleva `provenance` la escribió la
  ingesta.

## D-03 · RM-03, en la parte de nodos, no la garantiza la forma de la escritura

**Estado:** cerrada (2026-10-07), sin editar entregables: la escritura que
crea un tema, concepto o curso institucional crea también su arista hacia el
recurso de la corrida, solo si el nodo es nuevo (`write_batch_in`) ·
**Gravedad:** media

- **Lo que dicen los documentos.** La Tabla 20 de la tesis, la enmienda de
  ADR-005, la descripción del repositorio en `model.c4` (líneas 245-247) y el
  docstring de `src/iekg/core/repository.py` atribuyen RM-03 completa a la
  forma de la escritura.
- **Lo que pasa.** RM-03 tiene dos partes:
  - «toda arista que escribe la ingesta lleva su procedencia». Esta sí la fija
    el repositorio.
  - «todo tema, concepto y curso institucional tiene al menos una arista de
    procedencia». Esta no la impone nadie. El repositorio escribe un `Topic`
    institucional sin `WAS_DERIVED_FROM` si el lote no la trae, y la prueba
    `test_institutional_edges_get_the_provenance_of_the_write` lo hace (el
    nodo `topic`). El validador tampoco lo comprueba.
- **Por qué es deuda.** Cuatro documentos afirman un mecanismo que el código no
  tiene.
- **Qué hay que decidir.** Dónde vive esa parte de RM-03. Puede ir en el
  validador, como regla de la ingesta, o en el orquestador, al «agregar los
  hechos declarados» (vista dinámica). En el segundo caso, la Tabla 20 y el C4
  deben nombrar ese mecanismo y no la forma de la escritura.

## D-04 · El último reporte no siempre describe el estado vigente del grafo

**Estado:** cerrada (2026-10-07), sin editar entregables: la carga abre su
reporte antes de tocar la base y lo completa al auditar, y un reporte abierto
no está limpio (`operational_store.py`) · **Gravedad:** media

- **Lo que dicen los documentos.**
  - Tesis, §Reglas del módulo: «Cada uno [de los tres caminos] termina en una
    auditoría, así que el último reporte describe siempre el estado vigente
    del grafo».
  - `requisitos-funcionales-de-referencia.md`, línea 118, dice lo mismo.
  - ADR-007 hace depender de ese reporte la compuerta del worker.
- **Lo que pasa.** En `src/iekg/build_tools/commands.py:98-122` hay tres casos
  en los que la base cambia sin que se registre un reporte. En los tres, el
  último reporte en `var/operational.sqlite` sigue siendo el de un estado
  anterior; si estaba limpio, la compuerta queda abierta.
  - **La escritura falla después de `reset()`.** La base queda vacía y la
    carga sale con código 3.
  - **La auditoría falla.** La base queda cargada y sin auditar.
  - **Falla la escritura en SQLite.** Esa llamada ni siquiera está dentro de
    un `try`.
- **Por qué es deuda.** Una afirmación que la tesis usa para sostener AC-02 no
  se cumple en los caminos de error.
- **Qué hay que decidir.** Hay dos salidas:
  - Una carga que toca la base y no termina registra algo que cierra la
    compuerta.
  - Se declara como limitación, apoyada en que los procesos de construcción
    corren con el sistema detenido y el desarrollador repite la carga. En ese
    caso, la frase de la tesis se matiza.

## D-05 · La procedencia se admite en cualquier arista

**Estado:** cerrada (2026-10-07), sin editar entregables: la procedencia se
admite según la capa del origen de la arista
(`EDGE_PROPERTIES_BY_SOURCE_LAYER`), y RI-09 la comprueba · **Gravedad:** baja

- **Lo que dicen los documentos.** Tesis, Tabla 17: la procedencia la lleva
  «toda arista que escribe la ingesta».
- **Lo que pasa.** `EDGE_PROPERTIES` (`src/iekg/graph_schema.py:103-105`)
  admite `provenance` en los ocho tipos de arista, sin distinguir la capa. El
  comentario de esa misma línea dice que solo las aristas de la ingesta la
  llevan. RI-09 no detectaría una arista de referencia con procedencia.
- **Matiz.** La Tabla 17 dice qué elemento lleva la propiedad, y eso sí se
  cumple: el repositorio rechaza procedencia en una escritura de referencia.
  Lo único más laxo es la auditoría. Es dudoso que sea deuda.
- **Qué hay que decidir.** Hay dos salidas:
  - La declaración expresa esa restricción y la auditoría la comprueba (encaja
    con D-02).
  - La Tabla 17 se reformula como lo que la escritura fija, no como lo que el
    grafo admite.

## D-06 · Ningún ADR descarta un estándar para las reglas

**Estado:** cerrada por ADR-014 · **Gravedad:** baja (sustentación)

- **Lo que dicen los documentos.**
  - `CLAUDE.md` §2 y `docs/decisiones/README.md`: la decisión se escribe
    antes de implementar.
  - `traspaso-del-laboratorio.md` §4.1, preguntas 2 y 3 («¿qué formato tiene
    esa especificación, y por qué ese y no un estándar existente?», «¿qué
    tipos de regla necesita expresar?»), y §4.3, pregunta 11 («¿qué hace el
    intérprete con una regla?»).
- **Lo que pasa.** ADR-008 decide el formato del **esquema** (un módulo de
  Python) y descarta YAML para él. Además, en sus consecuencias, ya deja la
  lógica de las reglas en el código: «La lógica que no es dato (clave única,
  procedencia, anclaje, ciclos) vive en el código del núcleo, no en la
  declaración». La decisión de fondo, por tanto, sí está escrita. Lo que falta
  es más acotado:
  - ningún ADR considera un estándar para expresar reglas (SHACL) ni dice por
    qué se descarta;
  - no hay un catálogo de reglas como dato. Las quince reglas viven repartidas
    entre `rules.py`, el validador y el auditor.
- **Por qué es deuda.** La pregunta del traspaso, «¿por qué ese y no un
  estándar existente?», no tiene respuesta escrita. Además, toca la
  restricción del asesor («especificación declarativa más intérprete
  pequeño»), que hay que poder defender regla por regla.
- **Qué hay que decidir.** Escribir el ADR con sus alternativas reales. El
  informe de revisión trae los argumentos.

## D-07 · El traspaso afirma que SHACL «no lee un LPG»

**Estado:** cerrada por ADR-014 · **Gravedad:** baja

- **Lo que dice el documento.** `traspaso-del-laboratorio.md` §1 lo lista
  entre los hechos medidos: «SHACL no sirve aquí […] no emite Cypher y no lee
  un LPG».
- **Lo que pasa.** La documentación oficial de Neo4j Labs describe el módulo de
  validación de neosemantics (n10s), que valida un grafo de Neo4j contra
  formas SHACL. Advierte que, en un grafo de propiedades puro, solo cuenta el
  nombre local de cada URI. Que SHACL siga sin convenir aquí puede ser cierto
  por otras razones: n10s es un plugin de Labs, ADR-002 descartó n10s y SHACL
  Core no expresa aciclicidad. Pero la razón que da el traspaso es inexacta.
- **Qué hay que decidir.** El traspaso no se reescribe. El ADR de D-06, si
  descarta SHACL, debe hacerlo con el motivo correcto y citar la fuente; con
  eso se cierra esta entrada.

## D-08 · Docstring en español

**Estado:** cerrada: corregido el docstring · **Gravedad:** baja

- **Lo que dice el documento.** `estandares-de-codigo.md` §1: los comentarios y
  docstrings dentro de `.py` van en inglés.
- **Lo que pasa.** `src/iekg/__init__.py` tiene su docstring en español, y sin
  tildes.
