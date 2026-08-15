Este es un informe actualizado (agosto 2026) sobre los modelos disponibles en la capa gratuita de **Google AI Studio** para uso con API Key, enfocándonos en su capacidad de razonamiento.

---

# Informe: Modelos Gemini en Capa Gratuita (Free Tier)

### 1. Modelos de Razonamiento Avanzado (Pro Series)
Estos modelos son los "cerebros" de la familia. Utilizan una arquitectura diseñada para resolver problemas lógicos, matemáticos y de programación complejos.

| Modelo | ID para la API (Model ID) | Característica Principal |
| :--- | :--- | :--- |
| **Gemini 3.1 Pro** | `gemini-3.1-pro` | Máxima inteligencia y razonamiento profundo. Ventana de contexto de hasta 2M de tokens. |
| **Gemini 2.5 Pro** | `gemini-2.5-pro` | Excelente para análisis de documentos masivos y razonamiento de largo alcance. |

### 2. Modelos de Rendimiento y Lógica (Flash Series)
Modelos optimizados para velocidad, pero las versiones más recientes (3.x) han incorporado capacidades de "Pensamiento" (Thinking) antes de responder.

| Modelo | ID para la API (Model ID) | Característica Principal |
| :--- | :--- | :--- |
| **Gemini 3.7 Flash** | `gemini-3.7-flash` | El mejor equilibrio: rapidez extrema con razonamiento lógico para agentes autónomos. |
| **Gemini 3.1 Flash** | `gemini-3.1-flash` | Optimizado para latencia ultra baja y tareas repetitivas de chat. |

---

## Comparativa y Trade-offs

| Factor | **Pro Series** (3.1 Pro) | **Flash Series** (3.7 Flash) |
| :--- | :--- | :--- |
| **Razonamiento** | **Superior.** Resuelve lógica compleja en un solo paso. | **Bueno.** Utiliza "Thinking blocks" para pensar antes de hablar. |
| **Velocidad** | Lenta (latencia alta). | Muy rápida (latencia casi instantánea). |
| **Límites (Free)** | Muy estrictos (ej. 2 RPM / 50 RPD). | Generosos (ej. 15 RPM / 1500 RPD). |
| **Uso Ideal** | Investigación, código complejo, análisis legal. | Chatbots, resúmenes rápidos, clasificación. |

---

## Cómo invocarlos en Código (Python SDK)

Para usar las capacidades de razonamiento (especialmente en modelos que soportan `thinking`), se recomienda usar la librería `google-genai`.

### 1. Instalación
```bash
pip install -U google-generativeai
```

### 2. Ejemplo de Invocación con Razonamiento
Aquí llamamos al modelo **Gemini 3.7 Flash**, activando su configuración de pensamiento para que resuelva un problema lógico.

```python
import google.generativeai as genai
import os

# Configura tu API Key
genai.configure(api_key="TU_API_KEY_ACA")

# Selección del modelo (usa el ID de la tabla anterior)
model_id = "gemini-3.7-flash"

model = genai.GenerativeModel(
    model_name=model_id,
    # Opcional: Configuración para forzar razonamiento paso a paso
    generation_config={
        "thinking_level": "HIGH", # Disponible en modelos 3.x
        "temperature": 0.1
    }
)

response = model.generate_content(
    "Si tengo 3 camisas y tardan 3 horas en secarse al sol, ¿cuánto tardan 30 camisas?"
)

print(f"Respuesta: {response.text}")

# Si quieres ver el proceso de pensamiento (si el modelo lo soporta):
if hasattr(response, 'candidates') and response.candidates[0].grounding_metadata:
    print("Pensamiento interno detectado.")
```

### 3. Invocación Simple (Gemini 3.1 Pro)
```python
model_pro = genai.GenerativeModel("gemini-3.1-pro")
chat = model_pro.start_chat()
res = chat.send_message("Explica la teoría de cuerdas a un niño de 5 años.")
print(res.text)
```

---

### Notas Importantes sobre la Capa Gratuita:
1. **Privacidad:** Los datos enviados en la capa gratuita pueden ser utilizados por Google para entrenar y mejorar sus modelos. No envíes información sensible.
2. **Rate Limits:** Si ves el error `429 Resource Exhausted`, has superado las solicitudes por minuto (RPM). Los modelos Flash aguantan mucho más que los Pro.
3. **Regiones:** Algunos modelos nuevos pueden estar limitados por región geográfica (especialmente en la UE), verifica siempre el panel de [Google AI Studio](https://aistudio.google.com/).