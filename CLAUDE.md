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
- **Cada propuesta técnica lleva su costo documental** (ver §8, «Documentos que
  son entregables»).

## 4. Antes de opinar, leer

| Archivo | Por qué |
|---|---|
| `docs/tesis.md` | Las decisiones de diseño ya tomadas y argumentadas. |
| `docs/estandares-de-codigo.md` | Idioma, nomenclatura, pruebas. **No dupliques sus reglas: síguelas.** |
| `docs/decisiones/` | Las decisiones ya rehechas, con sus alternativas descartadas. |

Al diseñar la ingesta, leer además §3 (proveedores de LLM) y las preguntas 17 y
18 de §4.4 de `docs/repositorio/traspaso-del-laboratorio.md`. El resto de ese
documento está archivado.

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
README.md                      Cómo levantar el sistema y qué se puede probar.
docs/tesis.md                  El documento de tesis.
docs/estandares-de-codigo.md   Convenciones. Vinculantes.
docs/decisiones/               Un archivo por decisión rehecha.
docs/repositorio/              Auditorías con su deuda, y el traspaso del
                               laboratorio, archivado.
docs/architecture/             Modelo C4 en LikeC4 (*.c4).
ontology/*.ttl                 R1 (esquema OWL) y R2 (backbone CS2023).
docker-compose.yml             Neo4j 5.26 LTS.
src/iekg/graph_schema.py       Esquema del grafo: la declaración única (ADR-008).
src/iekg/core/                 Núcleo (#nucleo del C4): validador, repositorio,
                               auditor, lote e instantánea, códigos de regla.
src/iekg/build_tools/          Procesos de construcción: proyección TTL → lote
                               y el comando `iekg-build load`.
src/iekg/operational_store.py  Almacén operacional (SQLite): por ahora, solo
                               los reportes de auditoría.
src/iekg/settings.py           Configuración desde el entorno y `.env`.
tests/                         Pruebas; una negativa por cada forma de violar
                               cada regla.
var/                           Almacenes locales del sistema. Ignorado por git.
```

Lo que **no** hay, y es deliberado: API, worker, extractor, capa de LLM,
ingesta, reaplicación, lectura de la instantánea desde la base, tablas de
corridas y descartes, imagen de Docker propia. Nada de eso es un olvido: llega
con la ingesta.

## 7. Comandos

```powershell
docker compose up -d
uv sync
uv run pytest tests/ -q                  # las marcadas neo4j se saltan si la base no responde
uv run pytest tests/ -q -m "not neo4j"   # solo las que no necesitan Neo4j
uv run iekg-build load                   # vacía la base y carga el backbone
start http://localhost:7474

npm install               # una vez: LikeC4 fijado en package.json
npm run arch:validate     # sintaxis y referencias del modelo C4
npm run arch:export       # PNG en docs/architecture/images/, solo en hitos
npm run arch:serve        # vista previa en el navegador
```

La contraseña vive en `.env`, ignorado por git. Si falta: copiar `.env.example`,
poner una, `docker compose down -v` y volver a levantar.

**La carga del backbone** (`iekg-build load`) revisa los dos TTL contra la
Tabla 1 del anexo, proyecta el backbone y lo valida en memoria; recién entonces
vacía la base, crea las 8 restricciones de unicidad, escribe 180 nodos y 341
aristas en una transacción y audita las 15 reglas. El reporte queda en
`var/operational.sqlite`. Códigos de salida: 0 limpio; 1 cargado, con
violaciones en la auditoría; 2 rechazado sin tocar la base; 3 fallido.

Para verificarla desde cero:

1. Vaciar. En el Browser, `MATCH (n) DETACH DELETE n`: la carga borra y crea
   las restricciones por su cuenta. Para una base nueva del todo,
   `docker compose down -v` y `docker compose up -d`, que borra también
   restricciones y logs del contenedor. `var/` no se toca.
2. Comprobar que quedó vacía: `MATCH (n) RETURN count(n)`.
3. `uv run iekg-build load`.
4. Ver el resultado en el Browser:
   - `MATCH (n) UNWIND labels(n) AS label RETURN label, count(*)`: 17, 179,
     162 y 1.
   - `MATCH ()-[r]->() RETURN type(r), count(*)`: 162 `PART_OF` y 179
     `WAS_DERIVED_FROM`.
   - `MATCH p = (:KnowledgeUnit)-[:PART_OF]->(a:KnowledgeArea) WHERE a.key ENDS WITH '#KA-AI' RETURN p`
   - `SHOW CONSTRAINTS`: 8, con nombre `<Etiqueta>_key_unique`.

La consola de Windows puede mostrar mal las tildes de la salida; los datos
están bien guardados y el Browser los muestra correctamente.

## 8. Al escribir documentación

### Documentos que son entregables

Cuatro grupos de documentos no son documentación interna del repositorio:
`docs/tesis.md`, el anexo de transición al grafo de propiedades,
`docs/decisiones/` y `docs/architecture/`. Salen del razonamiento de la tesis y
se plasman como entregables o anexos en los documentos oficiales, que viven
fuera del repositorio (Google Docs). Cambiar uno de ellos obliga a replicar el
cambio allá y a mantener alineados todos los que dicen lo mismo. 
`docs/atributos-de-calidad.md` es solo para tener a mano lo que ya se dice en el
documento oficial de tesis respecto a atributos de calidad, mantenerlo actualizado 
considerando que tesis prima.
`docs/requisitos-funcionales-de-referencia.md` ahora es documentación interna
del repo, para guiar mejor los requerimientos del módulo de grafo de
conocimiento; su única fuente de verdad es el repositorio. Ahí se anota también
lo que el protocolo de medición de la tesis exige al sistema.

Por eso, ante una discrepancia entre el código y estos documentos, las salidas
se prefieren en este orden:

1. **Que el código cumpla lo escrito.** No cuesta ninguna edición.
2. **Declararlo en el repositorio** (`docs/repositorio/`, un archivo de deuda
   por auditoría), como limitación o como matiz conocido, cuando el riesgo
   real es bajo.
3. **Editar los entregables** solo si lo escrito es falso y la falsedad
   importa para la sustentación. En ese caso, la propuesta nombra cada
   documento afectado.

Toda propuesta técnica dice cuál de las tres implica y qué documentos toca.

- `docs/decisiones/NNNN-*.md`: una decisión por archivo, en español, con las
  **alternativas descartadas** y por qué. Es el producto, no el adorno: sin
  ellas, en tres meses no se sabrá por qué algo es así.
- Diagramas C4: el fuente es `docs/architecture/*.c4`, un solo modelo con una
  vista por nivel, más el flujo de la ingesta (vista dinámica) y el
  despliegue. No se agrega otra herramienta de diagramas. Durante el trabajo se ven en la vista previa de la
  extensión LikeC4, no en imágenes. Tras cada cambio, `arch:validate`. Los PNG
  se exportan solo en hitos (entregas de tesis, revisiones con el asesor), y
  cuando se exportan van en el mismo commit que el `.c4` del que salen. Claude
  edita a partir de una decisión ya escrita; Giano revisa el diff y la vista
  previa antes de hacer commit. Claude no hace push.
- **Un documento obsoleto que aparenta estar vigente es peor que ninguno.** Si
  algo cambia, se escribe uno nuevo; no se reescribe el viejo. La excepción es
  este archivo y `docs/estandares-de-codigo.md`, que sí son vivos. Los ADR
  admiten enmiendas solo para cambios menores; lo que invalida una decisión,
  aunque sea en parte, va en un ADR nuevo. El criterio está en
  `docs/decisiones/README.md`.
