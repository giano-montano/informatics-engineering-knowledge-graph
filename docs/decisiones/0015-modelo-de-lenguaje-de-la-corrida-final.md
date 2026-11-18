# ADR-015: Modelo de lenguaje de la corrida final y salida estricta

**Estado:** Aceptada
**Fecha:** 2026-11
**Atributos:** AC-01 (principal), AC-02

## Contexto

El extractor se desarrolló contra Sonnet, servido por una sesión local de Claude Code que se expone como servidor compatible con OpenAI. Esa vía no sirve para medir: el arnés agrega comportamiento que no se conoce y no se puede reproducir. Claude por API se descartó por costo (2026-11-13). Queda elegir entre OpenAI y DeepSeek para la corrida de medición de los 13 sílabos. El criterio que pesa más es que **el modelo sirva**: que devuelva la salida con la forma que exige el esquema y extraiga bien.

Al revisarlo aparecieron dos hechos que reordenan la pregunta:

- **Ningún modelo reciente se puede pedir por una versión fechada.** RF-25 exigía fijar el modelo «por su versión exacta, no por un alias que el proveedor pueda mover». Al 2026-11-14 solo las familias GPT-5.5 y anteriores publican versiones fechadas. GPT-6 y GPT-6.1 publican un solo nombre, y DeepSeek, dos alias. Mantener RF-25 dejaba fuera los modelos actuales por un motivo que no es su desempeño. RF-25 se reformula en la misma fecha (ver Decisión).
- **La salida no era estricta.** El extractor pide la salida con `NativeOutput` de PydanticAI, que en Chat Completions envía `response_format` de tipo `json_schema`. El esquema de salida tiene campos con valor por defecto, así que no es compatible con el modo estricto, y PydanticAI lo envía con `strict: false` sin avisar. En OpenAI, sin modo estricto, la conformidad con el esquema no está garantizada. Se comprobó capturando la petición sin enviarla.

El prompt se ajustó con Sonnet, y ese ajuste no se transfiere a otro modelo. El rendimiento de un formato de prompt se correlaciona poco entre modelos (Sclar et al., 2024), y la propia guía de OpenAI pide tratar cada modelo nuevo como uno que hay que ajustar desde una línea base, no como un reemplazo directo.

## Decisión

- **La corrida final usa `gpt-6.1-sol`** por la API Chat Completions de OpenAI. Basta con configurarlo: `IEKG_LLM_MODEL`, `IEKG_LLM_API_KEY` y `IEKG_LLM_BASE_URL`, que queda vacía.
- **La salida se pide en modo estricto:** `NativeOutput(SyllabusOutput, strict=True)`. PydanticAI transforma el esquema para que sea compatible: todo campo pasa a ser obligatorio, y los opcionales admiten `null`. El modelo Pydantic sigue validando después igual que antes, de modo que EX-01 conserva su significado. Una prueba comprueba, sin llamar al proveedor, que la petición sale con `strict: true`.
- **El esfuerzo de razonamiento se escribe en la configuración**, nunca se deja al valor predeterminado del proveedor, que no quedaría registrado. Su valor se fija al congelar el código, después del ajuste. `gpt-6.1-sol` no admite `none`. La temperatura no se envía.
- **El ajuste fino del prompt se repite con este modelo** antes de congelar el código. Los cambios de estructura pueden hacerse antes con el servidor de desarrollo, sin costo.
- **RF-25 se reformula:** se invoca el modelo por el nombre más específico que publique el proveedor (la versión fechada, si existe). Con cada ejecución se registran el nombre que devuelve la API, los parámetros de generación y la versión del prompt. La corrida de medición se hace en una sola sesión, y el registro anota la fecha y la versión que el proveedor declare servir en esa fecha.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| DeepSeek (`deepseek-flash` o `deepseek-v4-pro`) | **No devuelve la salida con el esquema por ninguna vía documentada estable.** Su Chat Completions solo admite `response_format` de tipo `text` o `json_object`, y el extractor actual fallaría en la primera llamada. Su API Responses acepta `json_schema`, pero no lo hace cumplir: en una llamada de prueba (2026-11-14) cuyas instrucciones contradecían el esquema, respondió siguiendo las instrucciones, dentro de un bloque de código. Quedan dos vías y ninguna sirve: el modo JSON no garantiza el esquema, y las herramientas en modo estricto son beta y no admiten `minItems`, que el esquema usa. Además, la respuesta informa solo el alias, no la versión servida. Con un precio unas veinte veces menor, se reconsidera si el modo estricto de herramientas sale de beta. |
| `gpt-6.1-terra` | Cuesta la mitad que `sol` y PydanticAI lo reconoce desde la versión 2.65. Pero OpenAI lo presenta para razonamiento visual, uso de computadora y redacción, y a `sol`, para «trabajo complejo» con un rendimiento cercano al de Astra. La extracción de relaciones que el sílabo no hace explícitas es trabajo complejo, y la diferencia de costo en la corrida es de centavos. |
| `gpt-6-astra` | Es el modelo insignia, pero cuesta cinco veces más que `sol` por token, y OpenAI presenta a `sol` con un rendimiento cercano. |
| `gpt-5.5-2026-04-23`, para conservar la versión fechada | Cumplía RF-25 en su redacción original. Pero cuesta más que `sol` por token, es una generación anterior y quedaría elegido por cómo se nombra, no por si sirve. |
| Comparar los candidatos sobre los sílabos de ajuste antes de elegir | Daría una elección medida, pero el prompt está ajustado con Sonnet, y comparar con un prompt fijo puede favorecer a un modelo por el formato y no por su capacidad (Sclar et al., 2024). Se pospone; la elección descansa en lo que declara el proveedor. |

## Consecuencias

- **La versión no queda fijada.** `gpt-6.1-sol` es un nombre sin fecha: OpenAI podría servir otro modelo detrás de él sin cambiar el nombre. Correr la medición en una sola sesión acorta esa ventana, pero no la cierra. Se declara como limitación.
- **Costo.** Sin tokens registrados (las corridas de desarrollo son anteriores a ese registro), se estimó sin llamar al proveedor. Para los 13 sílabos, la entrada ronda los 250 000 tokens, y la salida visible unos 45 000, con evidencia y justificación. A USD 2 por millón de entrada y USD 10 por millón de salida, la corrida cuesta entre USD 1 y USD 4, según el razonamiento (de 0 a 20 000 tokens por llamada). Si cada sílabo agotara sus tres intentos con su reintento interno, el costo se multiplicaría por seis, hasta unos USD 21. Todo cabe en la Tabla A.3.
- **Modo estricto.** La salida que el proveedor completa tiene la forma del esquema, y EX-01 queda, sobre todo, para lo que el esquema JSON no puede expresar: las condiciones del `model_validator`, como un tema nuevo sin unidad o una relación con un extremo desconocido. El servidor de desarrollo puede no respetar `strict`. Lo que mide la corrida es el proveedor final.
- Antes de congelar, la primera llamada del ajuste confirma qué nombre devuelve la API. Es el valor que registra el almacén operacional.
- El sistema depende de un proveedor de pago externo. La clave vive en `.env`, como las demás.

## Fuentes

Consultadas el 2026-11-14. Las de los proveedores son documentación oficial. Describen el estado de esa fecha y pueden cambiar sin aviso.

- OpenAI, índice de modelos y páginas de `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-astra`, `gpt-6-luna` y `gpt-5.5` (oficial): nombres y versiones publicadas, precios, salida estructurada, esfuerzos admitidos, Chat Completions. <https://developers.openai.com/api/docs/models>
- OpenAI, *Structured Outputs* (oficial): el modo estricto exige todos los campos obligatorios y `additionalProperties: false`; admite `minItems`. <https://developers.openai.com/api/docs/guides/structured-outputs>
- OpenAI, guía de GPT-5.5 (oficial): un modelo nuevo no es un reemplazo directo; partir de una línea base nueva. <https://developers.openai.com/api/docs/guides/latest-model/gpt-5.5>
- Endpoint `/models` de OpenAI, consultado por el autor sin costo el 2026-11-14: `gpt-6-sol`, `gpt-6.1-sol`, `gpt-6.1-terra`, `gpt-6-luna` y `gpt-6-astra`, ninguno con fecha (medición propia).
- DeepSeek, *Models & Pricing*, *Create Chat Completion*, *Create Response* y *Tool Calls* (oficial): alias y versión servida; `response_format` de Chat Completions solo admite `text` y `json_object`; la API Responses acepta `json_schema` sin campo `strict`; el modo estricto de herramientas es beta y no admite `minItems`. <https://api-docs.deepseek.com/>
- Llamada de prueba a la API Responses de DeepSeek (`deepseek-flash`, 2026-11-14), autorizada por el autor: 115 tokens de entrada y 69 de salida. El esquema exigía `{"animal": "cat" | "dog"}`, y la respuesta fue `{"color": "blue"}` dentro de un bloque de código (medición propia).
- APIYI, documentación de DeepSeek V4 Flash por la API Responses (gris: revendedor, sin fecha): reporta el mismo comportamiento. <https://docs.apiyi.com/en/api-capabilities/deepseek-v4-flash/responses.md>
- Sclar, M., Choi, Y., Tsvetkov, Y. y Suhr, A. (2024). *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting*. ICLR 2024 (revisado por pares). Midió modelos abiertos, entre ellos LLaMA-2-13B, con prompts de pocos ejemplos: respalda el principio, no una medida sobre `gpt-6.1-sol`. <https://arxiv.org/abs/2310.11324>
- PydanticAI 2.54.0, `profiles/openai.py` y `profiles/__init__.py` (código de la dependencia instalada): `NativeOutput` envía `strict: false` cuando el esquema no es compatible con el modo estricto, y `strict=True` lo transforma.
