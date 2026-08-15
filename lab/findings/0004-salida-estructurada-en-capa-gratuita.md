# 0004 — Qué modelos de capa gratuita soportan realmente la salida estructurada

- **Fecha:** 2026-08-14
- **Sustentabilidad:** alta para las mediciones (medición propia reproducible con
  `lab/scripts/probe_models.py` y llamadas crudas al SDK de Groq); media para la
  interpretación de la causa, que es inferencia a partir del comportamiento
  observado y no de documentación del proveedor.
- **Afecta a:** R4 (pipeline de ingesta), elección de modelo para O2, y el diseño
  de los modelos Pydantic que definen el contrato de extracción.

## Pregunta

La tesis compromete PydanticAI y salida tipada como mecanismo para que el LLM
nunca escriba directamente en la base. Antes de construir los cuatro pipelines
de comparación: ¿qué modelos de capa gratuita soportan esa salida tipada de
forma fiable, y con qué techo operativo?

## Método

Dos instrumentos. El primero, `lab/scripts/probe_models.py`, prueba cinco
propiedades por modelo (alcance, razonamiento, salida estructurada, abstención
y traducción cross-lingual) usando PydanticAI. El segundo, llamadas crudas al
SDK de Groq, para aislar variables que PydanticAI oculta.

El texto de prueba es un fragmento **inventado** sobre redes, nunca el sílabo de
Bases de Datos: mostrar extracciones reales antes de que exista la anotación de
referencia destruiría su ceguera.

## Resultado 1 — `$ref`/`$defs` rompe el tool calling en Groq

Es el hallazgo principal. Mismo modelo, mismo prompt, misma información en el
esquema; la única diferencia es si el JSON Schema usa una referencia o está
todo en línea.

| Esquema enviado a `openai/gpt-oss-120b` | Éxito |
|---|---|
| Todo en línea (sin referencias) | **4/4** |
| Con `$defs` + `$ref` | **0/4** |

El error es `400 tool_use_failed` con el campo `failed_generation` **vacío**: el
modelo no produce nada, no produce algo inválido.

Esto importa porque **Pydantic genera `$defs` + `$ref` para todo modelo anidado**.
Un `Extraction` que contenga `list[Topic]` produce una referencia
automáticamente, sin que el código lo pida. Es decir: el patrón natural para
representar una partonomía —que es exactamente el dominio de esta tesis— es el
que falla.

Vía PydanticAI el fallo no es determinista: con esquemas anidados cortos a veces
pasa. La lectura correcta no es "a veces funciona" sino que **la fiabilidad cae
de ~100 % a casi 0 % y algunos intentos tienen suerte**.

### Consecuencia de diseño

Los modelos Pydantic del contrato de extracción deben ser **planos** cuando el
destino es Groq, o hay que aplanar las referencias antes de enviarlas. Un
esquema plano usa arreglos paralelos (`topic_labels_es`, `topic_labels_en`) en
vez de una lista de objetos: más feo, y no reproduce la forma de la partonomía.

Esto contradice el supuesto implícito del `research_pipelines.md`, que trata la
salida estructurada como resuelta ("conformidad de formato prácticamente total,
<0,1 % de fallo"). Ese número viene del modo *strict* de OpenAI y **no se
transfiere** a modelos abiertos servidos por terceros.

## Resultado 2 — El TPM se cobra por adelantado sobre `max_tokens`

Pedir `max_tokens=8192` en Groq devuelve **HTTP 413**, no un truncamiento:

```
Limit 8000, Requested 8390, please reduce your message size
```

Groq reserva `max_tokens` contra el techo de 8.000 tokens por minuto **antes**
de generar. No se puede reservar presupuesto amplio de razonamiento "por si
acaso": el techo de TPM lo prohíbe estructuralmente.

Combinado con la varianza medida de Qwen3.6-27B —entre **433 y 5.745 tokens de
completado para el mismo prompt trivial**— resulta que no existe un `max_tokens`
seguro: el suficientemente alto para su peor caso es rechazado por 413, y el que
cabe trunca su razonamiento y produce `tool_use_failed`.

## Resultado 3 — Fiabilidad y costo por modelo

Seis intentos por modelo, esquema en línea, texto idéntico:

| Modelo | Éxito | Tokens de completado (mediana) | Latencia (mediana) |
|---|---|---|---|
| `openai/gpt-oss-120b` | **6/6** | 465 | 2,0 s |
| `qwen/qwen3.6-27b` | 5/6 | 1.341 | 6,2 s |

Qwen gasta **2,9× más tokens** y **3× más tiempo** para la misma tarea, y falla
más. Su ventaja de inteligencia (índice 38 vs 24, `lab/docs/llms/groq.md`) no se
manifiesta en esta tarea, que es de conformidad a un contrato y no de
razonamiento abierto.

## Resultado 4 — Modos de salida soportados

| Modo de PydanticAI | Groq / Qwen3.6 |
|---|---|
| `tool` (por defecto) | funciona |
| `NativeOutput` (`response_format: json_schema`) | **no soportado** |
| `PromptedOutput` | funciona |

Groq no acepta el modo nativo de esquema JSON con este modelo, así que la única
garantía disponible es el tool calling — que es justamente el que rompe con
`$ref`.

## Resultado 5 — Gemini 3.7 Flash pasa todo, pero no siempre responde

Pasa las cinco comprobaciones, incluidas las dos que más importan:

- **Abstención:** ante un texto sin prerrequisitos, devolvió lista vacía en vez
  de inventar. Es la propiedad de la que depende el criterio de aceptación de
  R4 (precisión ≥ 75 %).
- **Cross-lingual:** `'enrutamiento entre sistemas autónomos'` →
  `'Routing Between Autonomous Systems'`. Tradujo en vez de copiar.
- Aceptó el esquema anidado sin problema: 4 temas y 13 conceptos.

Pero devolvió **HTTP 503 "high demand" en 2 de 3 intentos** de ejecutar el probe
completo. No es un límite de cuota, es falta de capacidad del proveedor. Un
pipeline de varias etapas necesita reintento con espera exponencial o se caerá a
mitad de corrida por una razón ajena al diseño.

Nota de calidad, no de fallo: `gpt-oss-120b` devolvió 4 temas con **0 conceptos**
en el mismo esquema donde Gemini devolvió 13. Conformó el contrato y no extrajo
el contenido. Un esquema válido no es una extracción útil.

## Qué se decide con esto

1. **Gemini 3.7 Flash queda como modelo principal.** Es el único que combina
   esquema anidado, abstención correcta y traducción, y su cuota (1.500 RPD) es
   la única que aguanta iteración.
2. **El segundo modelo de la matriz de comparación pasa de `qwen/qwen3.6-27b` a
   `openai/gpt-oss-120b`.** Contradice la recomendación de
   `lab/docs/llms/groq.md`, que eligió Qwen por índice de inteligencia. Ese
   documento es un registro congelado y no se corrige; esta medición lo
   reemplaza para efectos de decisión.
3. **Todo modelo Pydantic del pipeline se prueba plano y anidado** antes de
   fijarlo, y el probe se corre contra cualquier modelo nuevo antes de meterlo
   en una corrida.
4. **Hace falta reintento con espera** en la capa de llamada, por el 503 de
   Gemini y por el `tool_use_failed` de Groq.

## Trampas encontradas al medir

- **`run.usage` es propiedad, no método**, en PydanticAI 2.x. Envuelto en un
  `try/except Exception` amplio, el `TypeError` se tragaba y el probe reportaba
  0 tokens en todo. Un `except` ancho convirtió un bug en un dato falso.
- **Los modelos emiten U+202F** (espacio fino sin salto) entre número y unidad.
  Rompe la consola cp1252 de Windows, y rompe cualquier comparación de
  subcadena: `"3 hour" in "3 hours"` es falso. Normalizar espacios antes de
  comparar.
- **`failed_generation` vacío** en el error de Groq significa que el modelo no
  emitió nada, no que emitió algo inválido. Distinguirlo ahorra buscar el bug en
  el lado equivocado.
