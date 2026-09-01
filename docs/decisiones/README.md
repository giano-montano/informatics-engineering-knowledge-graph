# Decisiones

Una decisión por archivo, numerada y fechada: `NNNN-titulo-en-kebab-case.md`.

En el laboratorio no había registros de decisión, y era correcto: ahí se
experimenta y casi todo se descarta. Aquí es al revés. **El registro es el
producto.** Sin él, dentro de tres meses no se sabrá por qué algo es así, y la
rama habrá vuelto al problema que vino a resolver: código que su autor no puede
defender.

Se escribe **antes** de implementar, no después. Ese orden es lo que evita que
el código viejo del laboratorio decida por uno.

## Forma

```markdown
# NNNN — Título en una línea

**Fecha:** AAAA-MM-DD · **Estado:** propuesta | vigente | reemplazada por NNNN

## Pregunta

Qué había que decidir, en una o dos frases. Si viene de
`docs/traspaso-del-laboratorio.md`, citar el número de pregunta.

## Alternativas

Cada una con su consecuencia. Como mínimo dos, y de verdad: una alternativa de
paja no cuenta como haber elegido.

## Decisión

Qué se hace y por qué. Si contradice algo escrito en `docs/tesis.md`, decirlo
aquí de forma explícita.

## Qué la falsaría

Qué habría que observar para tener que revisarla. Si no se puede contestar,
probablemente no era una decisión de ingeniería sino una preferencia.

## Evidencia

Medición propia, documentación oficial, o `git show lab-2026-09-01:<ruta>`.
Marcar lo que sea **fuente gris** (repos, foros, blogs, preprints): sirve para
decidir qué probar, no para sustentar la tesis.
```

## Estado

`vigente` es lo normal. `reemplazada por NNNN` mantiene el archivo viejo en su
sitio: **no se reescribe una decisión**, se escribe la que la sustituye. Un
documento obsoleto que aparenta estar vigente es peor que ninguno.
