## Groq — modelo más inteligente disponible gratis (ago 2026)

**El hueco antes de responder:** si ibas a asumir que el modelo "flagship" de Groq (GPT-OSS 120B) es automáticamente el más inteligente, los datos actuales no lo confirman. En el índice de inteligencia de Artificial Analysis (v4.1.1, el que se usa hoy), **Qwen3.6-27B saca 38 puntos vs. 24 de GPT-OSS-120B (high)**. Es decir, el modelo "preview" y más chico le gana en razonamiento al modelo "production" y más grande. Esto contradice la intuición de "más parámetros = más inteligente" y la etiqueta de featured/flagship de Groq.

### Recomendación concreta

| Criterio | **Qwen3.6-27B** (mejor razonamiento) | GPT-OSS-120B (alternativa estable) |
|---|---|---|
| Intelligence Index (Artificial Analysis) | **38** | 24 (modo "high") |
| Estado en Groq | Preview — puede discontinuarse sin aviso | Production |
| Velocidad | ~55 tok/s (lenta) | ~500 tok/s (rápida) |
| Verbosidad | Alta (gasta muchos más tokens pensando) | Moderada |
| Rate limit free tier | 30 RPM / 1K RPD / 8K TPM / 200K TPD | 30 RPM / 1K RPD / 8K TPM / 200K TPD |
| Contexto | 131,072 tok (en Groq; nativo 262K) | 131,072 tok |

Ambos están dentro del free tier con **los mismos límites numéricos** (Groq no diferencia mucho el free plan por modelo, solo el modelo define el techo). El costo por token no importa en la free tier salvo que te pase de cuota.

### Limitaciones reales que importan para tu caso

1. **Qwen3.6-27B es preview**: Groq lo puede sacar de catálogo en cualquier momento sin aviso previo (política explícita de "evaluation purposes only, not for production"). Si construyes algo que dependa de él, te puedes quedar sin modelo de un día a otro.
2. **1,000 requests/día** es la limitación dura para ambos en free tier — si tu caso de uso implica iterar mucho (agentic, testing en loop), lo vas a agotar rápido.
3. **8K TPM** es bajito: con prompts largos o razonamiento verboso (que es justo el punto fuerte de Qwen3.6), te vas a topar con el límite de tokens por minuto antes que con el de requests.
4. El benchmark de Qwen3.6 en SWE-bench/agentic viene de su **propio scaffold interno** (no verificación independiente completa aún) — su ventaja en Intelligence Index sí es de terceros (Artificial Analysis), pero para coding agentic hay que tomar sus propios números con cautela.

### Conclusión sin adornos

Si el criterio es **puramente razonamiento/inteligencia** y no te importa la inestabilidad de un modelo preview: **Qwen3.6-27B**. Si necesitas algo que no desaparezca de la API mañana: **GPT-OSS-120B**, aceptando que es menos inteligente según el índice actual, aunque bastante más rápido y con soporte de razonamiento nativo (browser search, code execution incorporados).