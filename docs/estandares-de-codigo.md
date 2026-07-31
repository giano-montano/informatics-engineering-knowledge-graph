# Estándares de código

Documento vivo. Decidido el 2026-07-31; si cambia una regla, se cambia aquí.

## 1. Idioma

La regla es **por tipo de artefacto**, no por archivo ni por gusto. Esto no es
spanglish: la frontera es explícita y no admite zona gris.

| Artefacto | Idioma |
|---|---|
| Directorios y nombres de archivo | Inglés |
| Módulos, clases, funciones, variables | Inglés |
| Claves e identificadores del YAML de reglas | Inglés |
| Etiquetas y tipos de relación del grafo | Inglés |
| Comentarios y docstrings dentro de `.py` | Inglés, breves |
| Salida por consola de los scripts | Inglés |
| `lab/findings/` | **Español** |
| `lab/docs/` | **Español** |
| Este documento y todo `docs/` | **Español** |

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

Los findings alimentan la tesis, que es en español, y varios ya contienen
párrafos redactados para la defensa. Escribirlos en inglés obligaría a
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
add integrity query compiler for schema rules
fix stale constraint names after language migration
docs: record Neo4j and Cypher walkthrough for 2026-07-31
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
| Propiedades de nodo | `camelCase` | `prefLabel`, `iri` |
| Identificadores de regla | `kebab-case` | `ku-in-single-ka` |
| Claves del YAML | `snake_case` | `allowed_pairs` |

Las propiedades de nodo van en `camelCase` porque replican los nombres de las
propiedades OWL (`prefLabel`, `resourceLocator`), no por preferencia estética.

## 3. Comentarios

Cortos y sobre **intención**, no sobre mecánica. El razonamiento largo va a
`lab/findings/`, con su fecha y su evidencia; el comentario solo apunta allí.

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
  identificador interpolado se valida antes contra la especificación.
- El LLM nunca escribe en la base. Genera datos; el Cypher lo construye código
  determinista.

## 5. Estructura del repositorio

```
docs/            Documentos de tesis y de proyecto. Español.
ontology/        Entregables R1 y R2 en Turtle.
schema/          Especificación declarativa de reglas de esquema.
src/iekg/        Código del paquete.
lab/scripts/     Scripts ejecutables del laboratorio.
lab/findings/    Hallazgos numerados y fechados. Español. No se actualizan.
lab/docs/        Registros de aprendizaje, fechados. Español. No se actualizan.
tests/           Pruebas, incluida la prueba negativa de integridad.
build/           Artefactos .cypher generados desde schema/. Versionados.
internal-notes/  Notas privadas. Ignorado por git.
```

`lab/findings/` y `lab/docs/` son **registros congelados**: llevan fecha y no se
mantienen al día. Si algo cambia, se escribe un documento nuevo. Un documento
obsoleto que aparenta estar vigente es peor que ninguno.

`build/` se versiona a propósito: los `.cypher` generados son evidencia citable
de cómo se validó el grafo, no un artefacto derivado desechable.

## 6. Pruebas

Una consulta de validación que no encuentra nada en datos limpios **no demuestra
nada**. Toda regla de integridad necesita su prueba negativa: se inyecta la
violación a propósito y se exige que la consulta la detecte.

Las pruebas que escriben en la base corren dentro de una transacción que se
revierte al terminar, de modo que la violación nunca persiste y el backbone
queda intacto.
