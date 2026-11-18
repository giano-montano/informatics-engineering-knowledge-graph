# Estándares de código

Documento vivo. Decidido el 2026-07-31 y revisado el 2026-10-03; si cambia una
regla, se cambia aquí.

## 1. Idioma

La regla es **por tipo de artefacto**, no por archivo ni por gusto. Esto no es
spanglish: la frontera es explícita y no admite zona gris.

| Artefacto | Idioma |
|---|---|
| Directorios y nombres de archivo, salvo en `docs/` | Inglés |
| Módulos, clases, funciones, variables | Inglés |
| Constantes del esquema del grafo | Inglés |
| Etiquetas y tipos de relación del grafo | Inglés |
| Identificadores del modelo C4 (`.c4`) | Inglés; el texto visible, en español |
| Comentarios y docstrings dentro de `.py` | Inglés, breves |
| Salida por consola de los scripts | Inglés |
| Este documento, todo `docs/` y sus nombres de archivo | **Español** |

### Por qué el código va en inglés

1. **La ontología R1 ya está en inglés y es inmutable.** Sus identificadores
   vienen de CS2023 (`KnowledgeArea`, `conceptInTopic`, `prefLabel`). Código en
   español alrededor de datos en inglés crea una costura permanente.
2. **El esquema LPG es una proyección de la ontología.** Etiquetas en español
   exigirían una tabla de traducción entre IRIs de OWL y etiquetas del grafo:
   mantenible, capaz de desincronizarse, sin beneficio a cambio.
3. **La documentación de Neo4j, Cypher y Python está en inglés.** Escribir en el
   mismo vocabulario que se lee reduce fricción al aprender.
4. Si en el futuro sale un paper, no hay nada que traducir en el código.

### Por qué la prosa va en español

La documentación alimenta la tesis, que es en español, y varios documentos ya
contienen párrafos redactados para ella. Escribirlos en inglés obligaría a
traducirlos de vuelta: pérdida pura.

### Presentación al usuario final

El idioma de la interfaz **no es un problema de esquema**. Se resuelve con
literales etiquetados por idioma en SKOS, que es el patrón estándar y ya está
disponible en los datos:

```turtle
:KA-AI skos:prefLabel "Artificial Intelligence"@en ,
                      "Inteligencia Artificial"@es .
```

Identificador estable, presentación multilingüe **como dato**.

### Mensajes de commit y ramas

**En inglés**, junto con los nombres de rama. Los commits son metadatos del
código, no prosa de tesis: se leen desde GitHub, acompañan a identificadores que
ya están en inglés, y las convenciones de git son anglófonas de origen (modo
imperativo, *Conventional Commits*).

```
add snapshot read to the graph repository
fix stale constraint names after language migration
docs: record ADR for the fact store
```

Convención: asunto en **imperativo**, minúscula inicial, sin punto final, hasta
unos 72 caracteres. Si hace falta explicar el porqué, va en el cuerpo tras una
línea en blanco. El *qué* lo dice el diff; el commit explica el *porqué*.

### Excepción registrada

Los archivos `ontology/*.ttl` conservan sus nombres actuales
(`ontologia_informatica.ttl`, `backbone_cs2023.ttl`). Son entregables de R1 y R2,
ya validados y potencialmente referenciados en el documento de tesis y en sus
anexos. Renombrarlos tiene un costo fuera del repositorio que no compensa. El
**contenido** de ambos ya está en inglés.

## 2. Nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| Módulos y archivos `.py` | `snake_case` | `load_backbone.py` |
| Clases | `PascalCase` | `Spec`, `Violation` |
| Funciones y variables | `snake_case` | `read_turtle`, `known_labels` |
| Constantes | `UPPER_SNAKE` | `DEFAULT_URI` |
| Privados de módulo | prefijo `_` | `_safe_ident` |
| Etiquetas de nodo | `PascalCase` | `KnowledgeUnit` |
| Tipos de relación | `UPPER_SNAKE` | `PART_OF`, `WAS_DERIVED_FROM` |
| Propiedades de nodo | `camelCase` | `prefLabel`, `resourceLocator` |
| Códigos de regla | prefijo y número | `RI-05`, `RM-02`, `EX-01` |

Las propiedades de nodo van en `camelCase` porque replican los nombres de las
propiedades OWL (`prefLabel`, `resourceLocator`), no por preferencia estética.

Los códigos de regla vienen de la documentación y el código los usa tal cual:
`RI` del anexo de transición al grafo de propiedades, `RM` del capítulo de
arquitectura de la tesis y `EX` de ADR-010. Cada consulta de auditoría lleva el
código de la regla que comprueba.

## 3. Comentarios

Cortos y sobre **intención**, no sobre mecánica. El razonamiento largo va a un
ADR en `docs/decisiones/`; el comentario solo apunta allí.

```python
# Group by label set so each MERGE is typed: an unlabeled MERGE
# would scan the whole database.
```

No se comenta lo que el código ya dice. Sí se comenta lo que costó descubrir o
lo que parece arbitrario y no lo es.

## 4. Escritura en la base

- Toda escritura pasa por `MERGE`, nunca por `CREATE`. La ingesta debe ser
  idempotente: correrla dos veces deja el mismo estado que correrla una.
- El `MATCH` de los extremos de una relación usa siempre una etiqueta con
  restricción de unicidad, para que vaya por índice y no escanee.
- Las etiquetas y los tipos de relación se interpolan en el Cypher porque
  Cypher no admite parámetros ahí; todo lo demás va **parametrizado**. Cualquier
  identificador interpolado se valida antes contra el esquema del grafo
  (ADR-008).
- El LLM nunca escribe en la base. Genera datos; las escrituras son plantillas
  de forma fija que solo reciben valores (ADR-003, ADR-005).

## 5. Estructura del repositorio

```
docs/               Tesis, anexo de transición, atributos de calidad. Español.
docs/decisiones/    Un ADR por archivo.
docs/architecture/  Modelo C4 en LikeC4.
ontology/           Entregables R1 y R2 en Turtle.
src/iekg/           Código del paquete.
tests/              Pruebas, incluidas las negativas de integridad.
```

El laboratorio sigue congelado en el tag `lab-2026-09-01`; sus rutas (`lab/`,
`schema/`, `build/`) no existen en esta rama.

## 6. Pruebas

Una consulta de validación que no encuentra nada en datos limpios **no demuestra
nada**. Toda regla de integridad necesita su prueba negativa: se inyecta la
violación a propósito y se exige que la consulta la detecte.

Las pruebas que escriben en la base corren dentro de una transacción que se
revierte al terminar, de modo que la violación nunca persiste y el backbone
queda intacto. Las que necesitan Neo4j llevan la marca `neo4j` y se saltan si
la base no responde. Ninguna prueba ejecuta la carga, porque vacía la base: la
carga se verifica corriéndola.
