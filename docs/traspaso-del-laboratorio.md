# Traspaso del laboratorio a la implementación

**Fecha:** 2026-09-01 · **Origen:** tag `lab-2026-09-01`

---

## 0. Qué es y qué no es este documento

El laboratorio produjo dos cosas de naturaleza muy distinta, y mezclarlas es lo
que hace que "empezar limpio" parezca imposible:

- **Hechos medidos sobre el mundo.** Cómo se comporta Neo4j, qué contesta de
  verdad la API de Google, qué hace `torch.compile` en Windows. No son
  arquitectura de nadie: son propiedades de herramientas de terceros que
  costaron horas descubrir. **Re-derivarlas es quemar las mismas horas para
  llegar al mismo sitio.** Se conservan. Están en las secciones 1 a 3.
- **Decisiones de arquitectura.** Cómo se mapea la ontología al grafo, dónde
  vive la validación, qué emite el intérprete. Ahí es donde entra el criterio
  del autor, y por eso **se rehacen todas**. La sección 4 las enuncia como
  preguntas abiertas, deliberadamente **sin la respuesta que dio el
  laboratorio**: si el documento trajera las respuestas, no se re-decidiría
  nada.

Quien quiera ver qué contestó el laboratorio, y con qué argumento, tiene el tag.
La sección 5 dice dónde mirar. **Se lee; no se trae.**

---

## 1. Hechos medidos: Neo4j y Cypher

Verificados contra Neo4j 5.26 LTS, edición Enterprise en Docker.

- **`CREATE CONSTRAINT ... IF NOT EXISTS` compara el esquema, no el nombre.** Al
  renombrar una restricción, Neo4j ve una equivalente y no crea nada: la base se
  queda con el nombre viejo mientras el artefacto generado dice otro. Hay que
  `DROP CONSTRAINT` primero.
- **Solo la restricción de unicidad sobrevive a Community.** Existencia de
  propiedad, tipo y clave compuesta son de Enterprise. Medido ejecutando el
  mismo script contra las dos ediciones, no leído en la documentación.
- **Cypher 5 no tiene función de lista a cadena**, y `toString()` rechaza
  listas. Se resuelve con `reduce(...)`, sin depender de APOC.
- **Las etiquetas y los tipos de relación no admiten parámetros.** Hay que
  interpolarlos en el texto de la consulta, con lo que validar esos nombres es
  responsabilidad de quien genera el Cypher.
- **`OPTIONAL MATCH` es imprescindible al contar cardinalidades.** Con `MATCH`
  normal, un nodo con cero destinos desaparece del resultado y la violación
  "tiene menos de uno" pasa inadvertida.
- **SHACL no sirve aquí**, y no por calidad: no emite Cypher y no lee un LPG.
  Validaría el RDF antes de proyectar, no el grafo que después se consulta.

## 2. Hechos medidos: entorno

- **Encadenar comandos con saltos de línea en PowerShell no corta ante un
  fallo.** Un borrado encadenado detrás de un `git mv` fallido se ejecutó igual
  y borró dos `.ttl` sin versionar. Usar `&&`, y **verificar antes de borrar**.
- **Docling no arranca en Windows sin MSVC**: `torch.compile` invoca `cl.exe`.
  Se resuelve fijando `TORCHDYNAMO_DISABLE=1` antes de importarlo.

## 3. Hechos medidos: proveedores de LLM

Todos medidos en agosto de 2026 contra la capa gratuita. **Caducan**: son
política comercial, no física. Antes de apoyarse en cualquiera de ellos, volver
a medir.

### 3.1 Cuotas reales

| proveedor / modelo | lo que decía la documentación | lo que contestó la API |
|---|---|---|
| `gemini-3.7-flash` | 15 RPM / 1500 RPD | **20 peticiones por día y por modelo** |
| Groq (`gpt-oss-120b`, `qwen3.6-27b`) | — | **8K tokens/minuto, 200K/día, por modelo** |
| Embeddings Gemini | 100/minuto | 100/minuto **contando textos, no llamadas** |

Tres consecuencias que no se deducen de la tabla:

- Las bolsas de Groq son **por modelo, no por cuenta**: agotar uno deja el otro
  intacto. Eso salvó la última corrida del laboratorio.
- Que el cupo de embeddings cuente textos significa que **agrupar no compra
  holgura**: hay que espaciar en el tiempo.
- **Los cupos se miden, no se leen.** El catálogo decía 1500 al día; la API
  contestó 20. Toda cifra de cuota escrita en un archivo es una hipótesis.

### 3.2 Cómo fallan, que es lo que de verdad cuesta

- **Un 429 puede llegar disfrazado de fallo de red.** Si el transporte HTTP
  reintenta ante 429, cierra la respuesta antes de re-lanzar y el SDK del
  proveedor nunca ve un estado: reporta `APIConnectionError`. Medido lado a lado
  con el mismo prompt: sin transporte con reintentos, `ModelHTTPError:
  status_code: 429` en 0,3 s; con él, `APIConnectionError` en 1,6 s. **Regla de
  diagnóstico: si un error de conexión aparece solo con prompts grandes y nunca
  con pequeños, es cuota.**
- **Un fallback declarado no es un fallback probado.** El de PydanticAI vigila
  `ModelAPIError`; un transporte con reintentos lanza `httpx.HTTPStatusError`,
  que no lo es. Estuvo escrito, documentado y **inerte** hasta que se agotó una
  cuota de verdad.
- **Google manda el tiempo de espera en el cuerpo de la respuesta**, no en la
  cabecera `Retry-After`.
- **Un SDK puede devolver menos de lo que se le pidió sin lanzar error.**
  `gemini-embedding-2` devuelve **un solo vector para un lote de N**. Sin
  comprobar el largo de la respuesta contra el de la entrada, todos los vectores
  a partir del primero quedan mal asignados y nada avisa.
- **Con salida tipada, `run.all_messages()[-1]` no lleva `model_name`**: el
  último mensaje es el retorno de la herramienta. Hay que recorrer hacia atrás
  hasta encontrar uno que lo tenga.

### 3.3 Medidas de comportamiento, no de infraestructura

Sirven para calibrar expectativas, no como conclusión: salen de **un solo
documento**.

- **Sin esquema en el prompt no hay jerarquía.** El pipeline sin restricciones
  devolvió 34 elementos planos y **cero** conceptos: no distingue Tema de
  Concepto. Es la cota inferior contra la que se mide cuánto vale restringir.
- **Cómo se pide la etiqueta pesó más que la arquitectura del pipeline.**
  Cambiar solo la redacción de qué es un Tema movió la precisión exacta de 0,00
  a 0,38, sin tocar ninguna etapa. Con la redacción original salían los títulos
  del índice del documento ("CAPÍTULO 3 SQL DDL (3 horas)"), que no coinciden
  con ninguna etiqueta del backbone.
- **El coseno de embeddings no separa acierto de casi-acierto.** Valores
  observados contra el backbone: 0,733 el correcto, 0,708 un casi-acierto, 0,560
  uno no relacionado. Y en un caso real, `SQL DDL` daba 0,6481 al primer
  candidato y 0,6470 al segundo: **1,1 milésimas.**
- **Una etiqueta corta pierde su dominio.** `Triggers` a secas no dice "base de
  datos" y su vecino más cercano cae en un área de seguridad. Limpiar la
  etiqueta mejora unas cosas y empeora otras.
- **Reenviar el documento entero en cada llamada por tema atasca la corrida**
  contra un techo de tokens por minuto. Recortando por los encabezados del
  propio documento: 82.233 → 1.887 caracteres enviados, y de más de 30 minutos
  sin terminar a 101 segundos.

## 4. Lo que hay que re-decidir

Enunciado como preguntas. **El laboratorio contestó todas**, y sus respuestas
están en el tag con su argumento; pero fueron respuestas escritas a una
velocidad a la que no se revisaron. Contestarlas de nuevo, y escribir por qué en
`docs/decisiones/`, es el trabajo de esta rama.

### 4.1 Especificación y esquema

1. ¿Qué es exactamente la fuente única de verdad del esquema, y qué queda fuera
   de ella? La restricción del asesor fija "especificación declarativa más
   intérprete pequeño", pero no dice dónde termina la especificación.
2. ¿Qué formato tiene esa especificación, y por qué ese y no un estándar
   existente?
3. ¿Qué tipos de regla necesita expresar? Unicidad, dominio y rango,
   cardinalidad, disyunción, aciclicidad, existencia... ¿cuáles hacen falta de
   verdad para esta ontología, y cuáles se estarían copiando de un catálogo
   teórico?

### 4.2 Proyección de la ontología al grafo

4. ¿Cómo se representa una subclase OWL en un grafo de propiedades, que no tiene
   herencia? Etiqueta adicional, propiedad, nodo aparte: cada opción cambia cómo
   se escribe toda consulta posterior.
5. ¿Qué se hace con varias subpropiedades de una misma relación: se conservan
   como tipos distintos, o colapsan en uno?
6. Las inversas: ¿se materializan las dos direcciones, una, o ninguna?
7. La clausura transitiva: ¿se materializa, se calcula al consultar, o no se
   ofrece?
8. Un literal con etiqueta de idioma (`@en`, `@es`) no tiene equivalente en un
   LPG. ¿Dos propiedades, una con sufijo de idioma, un nodo de etiqueta aparte?
9. ¿La T-box se materializa en la base junto a los datos, o vive fuera?

### 4.3 Validación

10. ¿Qué se valida **antes** de escribir y qué **después**, y por qué esa
    frontera y no otra?
11. ¿Qué hace el intérprete con una regla: la ejecuta, o emite un artefacto que
    alguien ejecuta? Y si emite, ¿el artefacto se versiona?
12. ¿Cómo se prueba una regla de integridad? Una consulta que no encuentra nada
    en datos limpios no prueba nada.
13. ¿Qué se hace con los axiomas OWL que ninguna restricción nativa puede
    sostener —funcionalidad, existencia, disyunción—? Son la mayoría.

### 4.4 Ingesta

14. ¿Qué produce el LLM y qué produce el código determinista? Es la frontera que
    define la contribución del trabajo, y hay que poder defender exactamente
    dónde se pone.
15. ¿La ingesta escribe en la base, o emite algo que se revisa antes de
    escribirse?
16. ¿Qué entidades puede acuñar la ingesta y cuáles son de solo lectura por
    pertenecer a la capa de referencia? ¿Cómo se garantiza eso
    estructuralmente, y no por convención?
17. ¿Qué significa que una mención "coincide" con una unidad del backbone? Y
    cuando no está claro: ¿se elige el mejor candidato, o se admite abstenerse?
    Si se abstiene, ¿quién resuelve, y dónde queda registrado?
18. ¿Dos sílabos que enseñan lo mismo producen un `Topic` o dos?
19. ¿Cómo se mide la calidad de una extracción sin que la medida acabe siendo el
    objetivo?

### 4.5 Método

20. ¿Cómo se evita que quien diseña el sistema contamine la referencia contra la
    que se mide? El laboratorio construyó una compuerta para esto y **la abrió a
    propósito**; el problema sigue en pie.
21. ¿Qué se versiona y qué no, de todo lo que el código genera?

## 5. Dónde mirar en el laboratorio

Todo con `git show lab-2026-09-01:<ruta>`. Se lee para contrastar **después** de
haber decidido, nunca antes.

| Ruta en el tag | Qué contiene |
|---|---|
| `CLAUDE.md` | Tabla de decisiones del laboratorio con su argumento (sección 6) y las trampas encontradas (sección 9). |
| `lab/findings/0001` | Restricciones nativas por edición, medido. |
| `lab/findings/0002` | Por qué no SHACL. |
| `lab/findings/0003` | Arquitectura de ingesta contra la literatura revisada. |
| `lab/findings/0004` | Salida estructurada tipada en capa gratuita. |
| `lab/findings/0005` | La escalera de pipelines y los techos reales de cuota. |
| `lab/docs/2026-08-07-*` | Modelo de datos y qué se ve dentro de Neo4j. |
| `lab/docs/2026-08-15-*` | Los cuatro pipelines de punta a punta y sus números. |
| `lab/docs/research_pipelines.md` | Revisión de literatura sobre ingesta. |
| `schema/schema_rules.yaml` | La especificación declarativa, 11 reglas. |
| `src/iekg/` | 15 módulos. |
| `tests/` | 77 pruebas, incluidas las negativas de integridad. |
| `build/runs/` | Seis corridas completas, con sus prompts y manifiestos. |

## 6. Estado del mundo, al empezar

- **La base de datos está cargada** con el backbone: 17 `KnowledgeArea`, 162
  `KnowledgeUnit`, 1 `LearningResource`, 4 restricciones de unicidad sobre
  `iri`. Ningún `Topic` ni `Concept`: nunca se ejecutó una carga de ingesta.
  Sirve para trabajar mientras no exista un proyector propio.
- **`ontology/` tiene dos archivos describiendo la capa de referencia**
  (`backbone_cs2023.ttl` y `backbone_cs2023_es.ttl`, este último con
  `skos:prefLabel` en `@en` y `@es`). Son dos fuentes de verdad para lo mismo,
  justo lo que el proyecto prohíbe en todo lo demás. **Deben colapsar en uno**,
  y es una decisión pendiente, no un arreglo mecánico: hay que elegir cuál
  sobrevive y qué se hace con el idioma.
- **El sílabo 1INF33 no puede ser la referencia ciega de R4.** Durante el
  laboratorio se vieron extracciones reales de ese documento, así que cualquier
  anotación posterior sobre él está contaminada. Queda como **sílabo de
  desarrollo** —ya cumplió ese papel y lo hizo bien— y la referencia ciega debe
  levantarse sobre otro. El PDF está en `data/raw/`, fuera de git.
- **Neo4j 5.26 LTS** (soporte hasta junio de 2028), Enterprise en desarrollo.
  **Nada puede depender de multi-base ni de Enterprise**: el despliegue es
  Community.
