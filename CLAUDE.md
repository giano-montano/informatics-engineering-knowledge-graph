# CLAUDE.md — rama `dev`

Instrucciones para sesiones de Claude Code en la **implementación de tesis**.

**Documento vivo.** Si algo aquí deja de ser cierto, se corrige aquí mismo.

---

## 1. Qué es esta rama, y qué no

`dev` es la implementación seria del módulo de grafo (R4), escrita paso a paso
por Giano. Nace de la rama `lab`, pero **vacía**: el primer commit borró todo
`src/`, `schema/`, `tests/` y `build/`.

Eso no fue higiene. El laboratorio se construyó a base de generación por IA a
una velocidad a la que su autor no llegó a revisar si la arquitectura era la que
él quería. Código que no se puede defender en una sustentación es pasivo, no
activo. Por eso se rehace.

El laboratorio sigue existiendo, congelado, en el tag **`lab-2026-09-01`**.

## 2. La regla que sostiene todo lo demás

**Se lee `lab`, nunca se trae de `lab`.**

```powershell
git show lab-2026-09-01:src/iekg/rules.py      # sí
git checkout lab-2026-09-01 -- src/iekg/       # NO
```

Y el orden importa: **primero se escribe la decisión en prosa, después se mira
el laboratorio** para ver si se pasó algo por alto. Al revés, el archivo viejo
resuelve el problema antes de que nadie lo haya pensado, y sale el mismo diseño
con otros nombres, sin la medición que lo justificaba.

Corolario para Claude: **no adelantes arquitectura.** Si falta una decisión, se
pregunta o se enuncia como pregunta abierta; no se rellena con lo que hacía el
laboratorio. Escribir código antes de que la decisión esté escrita es
exactamente el fallo que esta rama existe para corregir.

## 3. Con quién trabajas y cómo

Giano, tesista de Ingeniería Informática (PUCP). Aprendiendo Neo4j y Cypher
sobre la marcha: no asumas fluidez, pero tampoco expliques de menos.

- **Empezar por los huecos y los supuestos débiles. Sin halagos.**
- Proponer opciones **con recomendación explícita; él decide.** Antes de la
  pregunta, una explicación en prosa llana de cada opción y su consecuencia.
- Distinguir lo que sirve para **decidir qué probar** (fuente gris: repos,
  foros, blogs, preprints) de lo **sustentable en la tesis** (estándar, paper
  revisado, documentación oficial). Marcar lo gris fuente por fuente.
- Cuando algo **contradiga una decisión previa**, decirlo de frente.
- **Verificar versiones y estado del arte antes de recomendar.** No de memoria.
- **Leer `docs/tesis.md` antes de señalar algo como hueco de diseño.**

## 4. Antes de opinar, leer

| Archivo | Por qué |
|---|---|
| `docs/tesis.md` | Las decisiones de diseño ya tomadas y argumentadas. |
| `docs/estandares-de-codigo.md` | Idioma, nomenclatura, pruebas. **No dupliques sus reglas: síguelas.** |
| `docs/traspaso-del-laboratorio.md` | Lo que el laboratorio **midió** y lo que queda **por re-decidir**. |
| `docs/decisiones/` | Las decisiones ya rehechas, con sus alternativas descartadas. |

## 5. El proyecto en una pantalla

Resultados de tesis: **R1** ontología OWL validada · **R2** backbone de 17 áreas
y 162 unidades de CS2023 en Turtle · **R3** documentación del módulo de KG ·
**R4** módulo de KG y pipeline de ingesta (*lo que se construye aquí*) · **R5**
documentación de navegación · **R6** prototipo de navegación.

Restricción del asesor, vinculante: **especificación declarativa más intérprete
pequeño; nada hardcodeado, nada de ORM.**

## 6. Estado del árbol

Lo que hay:

```
docs/tesis.md                  El documento de tesis.
docs/estandares-de-codigo.md   Convenciones. Vinculantes.
docs/traspaso-del-laboratorio.md  Hechos medidos + preguntas abiertas.
docs/decisiones/               Un archivo por decisión rehecha.
ontology/*.ttl                 R1 (esquema OWL) y R2 (backbone CS2023).
docker-compose.yml             Neo4j 5.26 LTS.
src/iekg/__init__.py           Vacío a propósito.
```

Lo que **no** hay, y es deliberado: `schema/`, intérprete, validadores,
proyector, pruebas, `build/`, capa de LLM, ingesta. Nada de eso es un olvido.

## 7. Comandos

```powershell
docker compose up -d
uv sync
uv run pytest tests/ -q
start http://localhost:7474
```

La contraseña vive en `.env`, ignorado por git. Si falta: copiar `.env.example`,
poner una, `docker compose down -v` y volver a levantar.

**La base ya está cargada** con el backbone del laboratorio (17 `KnowledgeArea`
+ 162 `KnowledgeUnit` + 1 `LearningResource`). No hace falta recargarla para
trabajar; se recargará cuando exista un proyector propio que valide contra su
propia especificación.

## 8. Al escribir documentación

- `docs/decisiones/NNNN-*.md`: una decisión por archivo, en español, con las
  **alternativas descartadas** y por qué. Es el producto, no el adorno: sin
  ellas, en tres meses no se sabrá por qué algo es así.
- **Un documento obsoleto que aparenta estar vigente es peor que ninguno.** Si
  algo cambia, se escribe uno nuevo; no se reescribe el viejo. La excepción es
  este archivo y `docs/estandares-de-codigo.md`, que sí son vivos.
