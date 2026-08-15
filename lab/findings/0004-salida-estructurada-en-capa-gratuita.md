# 0004 — Qué modelos de capa gratuita soportan realmente la salida estructurada

- **Fecha:** 2026-08-14
- **Sustentabilidad:** alta para las mediciones (medición propia reproducible con
  `lab/scripts/probe_models.py` y con llamadas crudas al SDK de Groq); alta
  también para la atribución de causas, que se aisló con experimentos A/B
  controlados y no por inspección.
- **Afecta a:** R4 (pipeline de ingesta), elección de modelo para O2, y el diseño
  de los modelos Pydantic que definen el contrato de extracción.

> **Corrección interna, mismo día.** Una primera versión de este documento
> atribuyó el fallo de Qwen3.6 a `$ref`/`$defs`. Era incorrecto: ese experimento
> estaba mal controlado, porque al pasar el perfil de Groq a mano se eliminaba
> sin querer el transformador que PydanticAI ya aplica por defecto. La causa
> real de Qwen es otra y está en el Resultado 2. Se deja constancia porque la
> conclusión equivocada llegó a estar escrita.

## Pregunta

La tesis compromete PydanticAI y salida tipada como mecanismo para que el LLM
nunca escriba en la base. Antes de construir los cuatro pipelines de O2: ¿qué
modelos de capa gratuita soportan esa salida tipada de forma fiable, con qué
techo operativo, y es PydanticAI un obstáculo?

## Método

Dos instrumentos. `lab/scripts/probe_models.py` prueba cinco propiedades por
modelo (alcance, razonamiento, salida estructurada, abstención y traducción
cross-lingual). Aparte, llamadas crudas al SDK de Groq para aislar lo que
PydanticAI oculta. Los A/B son de 5 o 6 intentos por celda, `retries=0` para
medir fiabilidad cruda.

El texto de prueba es un fragmento **inventado** sobre redes, nunca el sílabo de
Bases de Datos: mostrar extracciones reales antes de que exista la anotación de
referencia destruiría su ceguera.

## Resultado 0 — La causa es distinta en cada modelo

Es el punto central. Dos modelos servidos por el mismo proveedor fallaban en la
misma comprobación **por razones no relacionadas**, y cada uno necesita un
arreglo distinto.

| Modelo | Por defecto | Corregido | Arreglo |
|---|---|---|---|
| `qwen/qwen3.6-27b` | 3/6 · 2.025 tok | **5/6 · 599 tok** | `thinking: false` |
| `openai/gpt-oss-120b` | 0/6 | **6/6 · 745 tok** | `inline_schema_defs: true` |

Aplicar el arreglo del otro a cada uno no sirve: Qwen ya recibía el inlining, y
gpt-oss no puede apagar el razonamiento.

## Resultado 1 — `$ref` rompe el tool calling de Groq, y el perfil de PydanticAI se equivoca de proveedor

A nivel de la API de Groq, con llamadas crudas y el mismo esquema:

| Esquema enviado | Éxito |
|---|---|
| Todo en línea | **4/4** |
| Con `$defs` + `$ref` | **0/4** |

El error es `400 tool_use_failed` con `failed_generation` **vacío**: el modelo no
produce nada, no produce algo inválido.

Pydantic emite `$defs` + `$ref` para todo modelo anidado, así que un `Extraction`
con `list[Topic]` —el patrón natural de una partonomía, que es este dominio—
genera una referencia sin pedirlo.

**PydanticAI ya mitiga esto, pero elige mal a quién aplicárselo.** Escoge el
transformador de esquema según el prefijo de *vendor* del identificador del
modelo, no según quién lo sirve:

| Modelo en Groq | Transformador que recibe | ¿Inlinea? |
|---|---|---|
| `qwen/qwen3.6-27b` | `InlineDefsJsonSchemaTransformer` | sí |
| `openai/gpt-oss-120b` | `OpenAIJsonSchemaTransformer` | **no** |

`gpt-oss-120b` lleva prefijo `openai/`, así que recibe el transformador de
OpenAI, que conserva `$defs` porque la API de OpenAI sí los resuelve. Pero aquí
lo sirve **Groq**, que no. De ahí el 0/6.

El arreglo es forzar `InlineDefsJsonSchemaTransformer`, que PydanticAI ya
exporta. En el catálogo es `inline_schema_defs: true`.

## Resultado 2 — El razonamiento de Qwen le impide emitir el tool call

Qwen ya recibía el inlining, así que su fallo era otro. Aislado apagando el
razonamiento, que en Groq **solo la familia qwen3 permite** desactivar:

| Configuración | Éxito | Tokens | Tokens de razonamiento |
|---|---|---|---|
| Por defecto (razonando) | 3/6 | 2.025 | ~826 |
| `thinking: false` | **5/6** | **599** | 0 |

Su flujo de razonamiento interfiere con la emisión de la llamada a herramienta.
Apagarlo no solo lo hace fiable: reduce los tokens **3,4×**, lo que importa
directamente por el techo de TPM del Resultado 3.

Queda en ~83 % por intento, así que necesita reintentos igual. Con `retries=2`
el probe pasa las cinco comprobaciones.

## Resultado 3 — El TPM se cobra por adelantado sobre `max_tokens`

Pedir `max_tokens=8192` en Groq devuelve **HTTP 413**, no un truncamiento:

```
Limit 8000, Requested 8390, please reduce your message size
```

Groq reserva `max_tokens` contra el techo de 8.000 tokens por minuto **antes** de
generar. No se puede pedir presupuesto amplio "por si acaso". Con la varianza
medida de Qwen razonando —entre **433 y 5.745 tokens de completado para el mismo
prompt trivial**— no existía un `max_tokens` seguro. Apagar el razonamiento
elimina el problema de raíz, no lo esquiva.

Un 413 **no es reintentable** y por eso queda fuera de la política de reintentos:
la misma petición fallaría idéntica.

## Resultado 4 — Modos de salida soportados

| Modo de PydanticAI | Groq / Qwen3.6 |
|---|---|
| `tool` (por defecto) | funciona |
| `NativeOutput` (`response_format: json_schema`) | **no soportado** |
| `PromptedOutput` | funciona |

## Resultado 5 — Dos identificadores de modelo de la investigación previa no existen

Verificado listando la API de Google:

| En `lab/docs/llms/gemini.md` y `.env` | Realidad |
|---|---|
| `gemini-3.1-flash` | **no existe**; solo variantes `-lite`, `-image`, `-tts` |
| `gemini-3.1-pro` | **404**; el identificador servido es `gemini-3.1-pro-preview` |

Confirma la advertencia que ya estaba en `lab/docs/llms/nvidia-build.md` sobre
nombres de modelo inconsistentes entre documentación y API, y la extiende a
Google. Un identificador se verifica listando la API, no leyendo una tabla.

## Resultado 6 — Estado final de los seis modelos

Con las correcciones del catálogo aplicadas y `retries=2`, **los seis pasan las
cinco comprobaciones**, incluidas las dos críticas: abstención correcta (ninguno
inventó prerrequisitos) y traducción real al inglés en vez de copia.

| Modelo | Latencia por llamada | Conceptos extraídos | Observación |
|---|---|---|---|
| `gemini-3.7-flash` | 1,5–4 s | 13 | Principal |
| `gemini-3.6-flash` | 2–4 s | 13 | Fallback del principal |
| `qwen/qwen3.6-27b` | 0,3–0,7 s | 12 | Preview; puede desaparecer |
| `openai/gpt-oss-120b` | 0,4–1,1 s | 14 | Estable en producción |
| `nvidia/nemotron-3-ultra` | 1–21 s | **25** | Más extractivo de todos |
| `z-ai/glm-5.2` | **~70 s** | 15 | Inusable para iterar |

`gemini-3.1-pro-preview` devolvió 429 y no pudo medirse: 2 RPM lo hace inviable
salvo para una corrida final.

Nota de calidad, no de fallo: la cantidad de conceptos varía de 12 a 25 sobre el
mismo texto. Todos conformaron el contrato. **Un esquema válido no es una
extracción útil**, y eso es precisamente lo que la comparación de pipelines
tiene que medir aparte.

## Respuesta a la pregunta de si PydanticAI estorba

No, y conviene dejarlo por escrito porque la alternativa era cambiar la tesis.

- Ninguno de los tres fallos lo causa PydanticAI: el `$ref` se reprodujo contra
  el SDK crudo de Groq, el 413 es contabilidad de Groq y el 503 es capacidad de
  Google.
- Los dos arreglos que resolvieron todo —`InlineDefsJsonSchemaTransformer` y
  `thinking`— **son piezas de PydanticAI**. La librería no solo no era el
  problema: es donde vivía la solución.
- Su sistema de perfiles por modelo es lo que permitió corregir el caso
  `gpt-oss` sin tocar el código de los experimentos. Con llamadas crudas habría
  que reimplementar eso.

El único defecto atribuible es el del Resultado 1, elegir el transformador por
prefijo de vendor y no por proveedor servidor. Es un caso de borde de modelos
abiertos servidos por terceros, y se corrige declarativamente en una línea.

**Sigue siendo legítimo variar el framework como eje experimental** —salida
tipada vía PydanticAI contra decodificación restringida por gramática, por
ejemplo— pero como una pregunta de investigación elegida, no como huida de un
bloqueo. Bloqueo no hay.

## Qué se decide con esto

1. **Gemini 3.7 Flash queda como modelo principal**, con `gemini-3.6-flash` como
   fallback automático ante 503, y reintento con espera en el transporte.
2. **La matriz de comparación mantiene `workhorse` + `reasoner_fallback`**
   (gpt-oss-120b): 6/6 de fiabilidad, estable en producción y 10× más rápido que
   Qwen razonando. Qwen queda disponible y arreglado, pero es preview.
3. **Toda opción de modelo vive en `lab/models.yaml`**, no en el código de los
   experimentos, y las dos que sostienen la fiabilidad están marcadas como tales.
4. **Los identificadores de modelo se verifican contra la API** antes de entrar
   al catálogo.

## Trampas encontradas al medir

- **Un experimento A/B puede quitar sin querer la configuración por defecto.**
  Pasar `profile=groq_model_profile(...)` a mano parecía "el control", y en
  realidad eliminaba el transformador que el proveedor ya aplicaba. Produjo una
  conclusión causal falsa. Al comparar contra "por defecto", hay que obtener el
  defecto del mismo camino que usa la librería.
- **`run.usage` es propiedad, no método**, en PydanticAI 2.x. Envuelto en un
  `try/except Exception` amplio, el `TypeError` se tragaba y el probe reportaba
  0 tokens en todo. Un `except` ancho convirtió un bug en un dato falso.
- **Los modelos emiten U+202F** (espacio fino sin salto) entre número y unidad.
  Rompe la consola cp1252 de Windows y rompe cualquier comparación de subcadena:
  `"3 hour" in "3 hours"` es falso si el espacio es U+202F. Normalizar antes de
  comparar; si no, se puntúa como incorrecta una respuesta correcta.
- **`failed_generation` vacío** en el error de Groq significa que el modelo no
  emitió nada, no que emitió algo inválido.
