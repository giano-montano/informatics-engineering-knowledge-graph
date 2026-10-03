# Decisiones

Una decisión por archivo, numerada: `NNNN-titulo-en-kebab-case.md`.

En el laboratorio no había registros de decisión, y era correcto: ahí se
experimenta y casi todo se descarta. Aquí es al revés. **El registro es el
producto.** Sin él, dentro de tres meses no se sabrá por qué algo es así, y la
rama habrá vuelto al problema que vino a resolver: código que su autor no puede
defender.

Se escribe **antes** de implementar, no después. Ese orden es lo que evita que
el código viejo del laboratorio decida por uno.

## Forma

```markdown
# ADR-NNN: Título en una línea

**Estado:** Aceptada
**Fecha:** AAAA-MM
**Atributos:** AC-0X (principal), AC-0Y

## Contexto

Qué hay que decidir y por qué, en uno o dos párrafos. Si la decisión
reemplaza parte de otra, se dice aquí.

## Decisión

Qué se hace. Si contradice algo escrito en `docs/tesis.md`, se dice de forma
explícita.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|

Como mínimo dos, y de verdad: una alternativa de paja no cuenta como haber
elegido.

## Consecuencias

Lo que se gana, lo que se pierde y las limitaciones que se declaran.
```

Si la decisión se apoya en una medición o en una fuente, se cita. Lo que sea
**fuente gris** (repositorios, foros, blogs, preprints) se marca como tal:
sirve para decidir qué probar, no para sustentar la tesis.

## Estado

| Estado | Cuándo |
|---|---|
| `Aceptada` | Lo normal. |
| `Aceptada (enmendada AAAA-MM)` | Tiene una o más enmiendas al final. |
| `Aceptada, en parte reemplazada por ADR-NNN` | Otro ADR invalida una parte; lo que dice ese ADR prevalece. |
| `Reemplazada por ADR-NNN` | Otro ADR la invalida por completo. |

Un ADR que todavía no se ha subido al repositorio es un borrador y se edita
libremente.

## Enmiendas

Una decisión aceptada no se reescribe. Cuando cambia algo, se elige entre dos
caminos:

- **Enmienda**, si el cambio es menor: una aclaración, una precisión o un
  ajuste que deja en pie lo decidido. Se agrega al final una sección
  `## Enmienda (AAAA-MM)` y el estado lo indica.
- **ADR nuevo**, si el cambio no es menor o invalida la decisión original,
  aunque sea en parte. El ADR nuevo dice en su contexto qué reemplaza, y el
  viejo se queda en su sitio con el estado que lo apunta.

Una enmienda nunca dice «donde dice X, debe leerse Y»: eso es reescribir. Un
documento obsoleto que aparenta estar vigente es peor que ninguno.
