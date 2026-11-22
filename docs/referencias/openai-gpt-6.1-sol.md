# GPT-6.1 Sol: parámetros de muestreo y cómo corrió la medición de R4

**Verificado:** 2026-11-21, contra la documentación de OpenAI listada al final y
contra `var/medicion-r4/operational.sqlite`. Antes de citar algo de aquí en la
tesis, volver a comprobarlo: la documentación del proveedor cambia sin aviso.

Nota de referencia interna. No es un ADR ni un entregable.

## Qué dice OpenAI

- **Esfuerzo de razonamiento.** GPT-6.1 Sol admite `low`, `medium` (el valor
  por defecto), `high`, `xhigh` y `max`. No admite `none` ni `minimal`.
  En Chat Completions el parámetro es `reasoning_effort`.
- **Temperatura y `top_p`.** La guía de migración de la familia GPT-6 dice que,
  cuando el esfuerzo no es `none`, se quitan `temperature`, `top_p` y
  `top_logprobs`, y en Chat Completions también `logprobs`. Como Sol no puede
  correr con `none`, **no hay forma de fijar la temperatura ni `top_p` con
  este modelo.** La guía no dice si mandarlos da error o se ignora. Un hilo del
  foro de desarrolladores dice que da error de petición (fuente gris).
- **Determinismo.** Ni la página del modelo ni la guía de razonamiento dicen
  nada de semilla (`seed`) ni de reproducibilidad.
- **Versiones.** La página del modelo lista una sola instantánea, `gpt-6.1-sol`,
  sin fecha, y no dice a qué versión resuelve el alias.
- **Salida estructurada.** La página del modelo lista `structured_outputs`
  entre las funciones admitidas y Chat Completions entre los endpoints. Ninguna
  página dice de forma explícita que `json_schema` con `strict` funcione en
  Chat Completions para Sol. Que funciona está medido: lo usaron las 13
  corridas de la medición. Las llamadas a herramientas (*function calling*)
  exigen la API Responses, pero el extractor no las usa.

## Con qué corrió la medición final

Fuente: la tabla `runs` de `var/medicion-r4/operational.sqlite`, que el
extractor llena al terminar cada corrida (RF-25), y `var/medicion-r4/run.sh`.

| Qué | Valor |
|---|---|
| Fecha | 2026-11-16, de 22:25 a 22:45 UTC |
| Código | tag `codigo-congelado-2026-11-16` |
| API | Chat Completions (`OpenAIChatModel` de PydanticAI), endpoint por defecto de OpenAI |
| Modelo pedido | `gpt-6.1-sol` |
| Modelo que respondió | `gpt-6.1-sol`: es el nombre que devolvió la API; no trae fecha de instantánea |
| `reasoning_effort` | `medium`, que es además el valor por defecto |
| `temperature`, `top_p`, `seed` | No se mandaron (`temperature: null` en el registro) |
| Salida | `NativeOutput(SyllabusOutput, strict=True)`: `json_schema` estricto |
| Versión del prompt | `501988180f16`, la misma en las 13 corridas |
| Reintentos | `max_retries: 3` del cliente, para errores transitorios; 0 reintentos de contenido en las 13 |
| Corridas | 13 completas (1 a 5 y 7 a 14). La 6 murió por un fallo de segmentación al leer 1INF30, antes de escribir; `resume.sh` siguió la cadena desde 1INF30 sin recargar |
| Tokens | 237 457 de entrada y 70 068 de salida en total |

## Qué implica para la tesis

La variación entre corridas no se puede controlar desde la petición. Con
GPT-6.1 Sol no hay temperatura ni semilla que fijar, y el alias puede cambiar
de versión sin aviso. Lo que sí queda fijo y registrado es lo que el sistema
controla: el código, el prompt, el esfuerzo de razonamiento, el esquema
estricto y el nombre del modelo que respondió.

Por eso, una sola corrida no separa tres causas de la diferencia entre los
sílabos retenidos y los del ajuste: el sobreajuste del prompt, la dificultad
propia de cada sílabo y la variación del modelo. Separarlas exige repetir
varias corridas por sílabo. Eso queda como trabajo futuro.

## Fuentes

- OpenAI, «GPT-6.1 Sol Model», <https://developers.openai.com/api/docs/models/gpt-6.1-sol>
  (esfuerzos admitidos, instantáneas, funciones y endpoints).
- OpenAI, «Reasoning models», <https://developers.openai.com/api/docs/guides/reasoning>
  («GPT-6.1 Sol does not support `none` or `minimal` and defaults to `medium`»).
- OpenAI, «Using GPT-6», <https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra>
  (sección «Unsupported parameters» y limitaciones de GPT-6.1 Sol).
- Fuente gris: OpenAI Developer Community, «Migrating to GPT-6.1 Sol / Astra:
  three API changes that cause errors», <https://community.openai.com/t/migrating-to-gpt-6-1-sol-astra-three-api-changes-that-cause-errors-effort-none-sampling-params-tools-in-chat-completions/1412047>.
  Sirve para decidir qué probar, no para citarla en la tesis.
