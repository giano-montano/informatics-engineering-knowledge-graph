## NVIDIA Build (NIM) — modelo más inteligente gratis + consideraciones de código

**El hueco antes de recomendar nada:** "gratis" en NVIDIA Build no es lo mismo que en Groq. No es una cuota que se renueva cada día — es un **trial de créditos** (1,000 al registrarte, hasta 5,000 si pides más por el foro con correo corporativo). Cuando se acaban, la API tira `402 Payment Required`, no un simple rate-limit. Si vas a integrar esto en algo que uses seguido, ese es el problema real, no cuál modelo es más listo.

### Modelo más inteligente con Free Endpoint

Comparando el Artificial Analysis Intelligence Index (mismo índice que usé para Groq, así que es comparable directo):

| Modelo | Intelligence Index | Contexto | Parámetros |
|---|---|---|---|
| **GLM-5.2 (Z.ai)** | **51–53** (líder open-weight, top-4 global) | 1M | 753B (MoE) |
| Nemotron 3 Ultra 550B-A55B | 38–48 (líder open-weight *estadounidense*) | 1M | 561B (MoE) |
| gpt-oss-120b (referencia Groq) | 24 | 131K | 120B |

GLM-5.2 le gana claramente a Nemotron 3 Ultra en el índice. La única razón para preferir Nemotron pese al puntaje menor: es modelo NVIDIA-nativo en su propia plataforma (soporte de primera mano), mientras GLM-5.2 es de Z.ai (China) y está bajo revisión del US CAISI (Center for AI Standards and Innovation) desde julio 2026 — dato a considerar si el proyecto tiene requisitos de compliance.

```python
# GLM-5.2 — el más inteligente en el catálogo free de NVIDIA Build
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="$NVIDIA_API_KEY"
)

completion = client.chat.completions.create(
    model="z-ai/glm-5.2",
    messages=[{"role": "user", "content": "tu prompt aquí"}],
    temperature=1,
    top_p=1,
    max_tokens=16384,
    stream=True
)

for chunk in completion:
    if chunk.choices and chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

```python
# Nemotron 3 Ultra 550B-A55B — alternativa NVIDIA-nativa (Frontier, razonamiento)
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="$NVIDIA_API_KEY"
)

completion = client.chat.completions.create(
    model="nvidia/nemotron-3-ultra-550b-a55b",
    messages=[{"role": "user", "content": "tu prompt aquí"}],
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384},
    stream=True
)

for chunk in completion:
    if not chunk.choices:
        continue
    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    if reasoning:
        print(reasoning, end="")
    if chunk.choices[0].delta.content is not None:
        print(chunk.choices[0].delta.content, end="")
```

### Consideraciones al codificar (según foros de dev de NVIDIA y issues públicos)

1. **Rate limit real: 40 RPM por cuenta**, no por modelo — reportado repetidamente en el foro de NVIDIA (varios devs pidiendo subirlo a 200 RPM sin respuesta consistente; a veces NVIDIA escala internamente, a veces no). Si tu flujo hace loops agénticos (tool calls encadenados), lo tocas rápido.
2. **Créditos se gastan distinto por modelo**: modelos grandes como GLM-5.2 (753B) o Nemotron 3 Ultra (561B) consumen mucho más crédito por llamada que algo chico como Llama 3.1 8B. Con 1,000 créditos iniciales, en un modelo grande se te acaba en poco tiempo de pruebas reales — no es "gratis ilimitado", es "gratis para prototipar".
3. **Tool calling con GLM-5.2 es inestable**: hay un reporte abierto en el foro de NVIDIA (feb 2026) de JSON truncado/malformado en argumentos de tool calls (falta el `}` de cierre) al usarlo vía cliente OpenAI-compatible (OpenCode). Si vas a usar function calling en producción con GLM-5.2 en NIM, valida/repara el JSON antes de parsearlo.
4. **`tool_choice='required'` rompe con GPT-OSS en el endpoint NVIDIA** (no aplica a tus dos candidatos arriba, pero si terminas probando gpt-oss-120b/20b vía NIM): un dev reportó `TypeError: 'NoneType' object is not subscriptable` porque el endpoint devuelve `response.choices` vacío cuando se fuerza tool_choice. Workaround reportado: usar `tool_choice='auto'`.
5. **Nombres de modelo inconsistentes entre docs y API real**: varios hilos de "model does not exist" al llamar desde LangChain (`ChatNVIDIA`) o SDKs de terceros porque el string del modelo cambió o no coincide con la doc. Verifica el string exacto en la página del modelo específico (`model=` del snippet, no lo que dice el nombre del listado) antes de hardcodearlo.
6. **`reasoning_content` es un campo no estándar** (extensión de NIM sobre el chat completion de OpenAI) — si usas un SDK genérico OpenAI-compatible que no lo espera, puede que lo ignore silenciosamente o rompa el parseo si tu código asume el schema estricto de OpenAI. Usa `getattr(..., None)` como en el snippet, no acceso directo por atributo.