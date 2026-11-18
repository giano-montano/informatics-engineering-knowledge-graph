# Panel del operador (RF-23) · común a P1, P2 y P3

## 1. Qué hace y cómo abrirlo

Es una pantalla de consola de administración para el único operador. Se teclea el token, se ve el estado de la compuerta de auditoría, se sube un sílabo, se siguen las corridas y, para cada una, se ven su detalle, su reporte de auditoría de cierre y sus descartes. Al pie están las 15 reglas del último reporte.

- **Abrir:** doble clic en `index.html` (`file://`). Carga `../datos/datos.js` y lee `window.IEKG_OPERACION`, que tiene las respuestas reales capturadas de la API.
- **Entrar:** cualquier token no vacío. Para ver el rechazo, pulsa «Probar token inválido» en el acceso o, ya dentro, «Sesión ▾ → Simular token rechazado».
- **Sin librerías ni framework:** HTML, CSS y JS sin compilación (`panel.css` y `panel.js`). Como no hay nada que traer de un CDN, no hubo versiones que verificar.
- **Para integrarlo en P1, P2 o P3:** todos los colores salen de variables CSS en `:root`, con tema claro y oscuro (`prefers-color-scheme` o `data-theme`). Cada propuesta las redefine y el panel toma su estética sin tocar el resto.
- **PDF:** el enlace «Abrir el documento» apunta a `http://localhost:8000/resources/{resource_key}`. Abre solo con la API corriendo (`uv run iekg-api`). Es la misma URL que el `locator` del nodo en el grafo: lo comprobé con las 4 corridas.

## 2. Flujo

El panel resuelve un caso de uso del catálogo común (`../casos-de-uso.md`).

**Flujo CU-11 · Cargar un documento y revisar su ingesta**
1. En el acceso, el operador teclea su token y entra. Con un token rechazado, el panel muestra el error y no deja pasar.
2. Arriba ve el estado de la compuerta de auditoría: si está abierta, se pueden registrar corridas.
3. En «Cargar un documento» elige el PDF, el tipo de recurso («Sílabo»), el código y el nombre del curso, y lo envía. La corrida nueva aparece en la lista como pendiente.
4. En «Corridas de ingesta» sigue el estado de cada corrida, con su duración.
5. Abre una corrida: en «Resumen» ve sus fechas, el documento y el modelo; en «Auditoría de cierre», el reporte regla por regla; en «Descartes», lo que se rechazó, si hubo algo.
6. Al pie consulta el último reporte de auditoría, con las 15 reglas.

### Qué parte de RF-23 cubre cada zona

RF-23 pide: *cargar un documento, seguir el estado de su ingesta, revisar los descartes de esa ejecución y consultar su reporte de auditoría.*

| Zona de la pantalla | Capacidad de RF-23 | Detalle |
|---|---|---|
| Acceso del operador | (condición previa, ADR-013) | El token se teclea y vive en `sessionStorage`, con respaldo en memoria. Muestra la respuesta 401 real. |
| Cargar un documento | **Cargar un documento** | Los campos son los reales de `POST /api/runs`. Antes de enviar valida lo mismo que da 422 en la API: extensión `.pdf`, cabecera `%PDF-`, código y nombre del curso. |
| Corridas de ingesta (lista) | **Seguir el estado** | Muestra los 7 estados de ADR-010 con ícono, texto en español y el código de la API, nunca solo con color. La leyenda es plegable. Cada fila lleva la duración. |
| Detalle → Resumen | **Seguir el estado** | Fechas, documento con enlace al PDF, modelo, versión del prompt, reintentos de contenido (de 1 permitido), ajustes del modelo y error. Cubre RF-25. |
| Detalle → Auditoría de cierre | **Consultar su reporte** | El reporte que cerró esa corrida, regla por regla. |
| Detalle → Descartes | **Revisar los descartes** | Tiene un estado vacío según el estado de la corrida. Un botón muestra un ejemplo con descartes. |
| Compuerta de auditoría (arriba) | **Consultar el reporte** | Estado de la compuerta (`gate.state` y `reason`) y resumen del último reporte. |
| Último reporte de auditoría (abajo) | **Consultar el reporte** | Las 15 reglas, agrupadas en RI y RM, con su enunciado, sus violaciones y la muestra. |

## 3. Rutas que usa

Todas existen en R4 y llevan `Authorization: Bearer <token>`, salvo `/resources`, que es pública.

| Ruta | Zona |
|---|---|
| `GET /api/runs` | Lista de corridas (y validar el token al entrar) |
| `GET /api/runs/{id}` | Detalle: resumen y auditoría de cierre |
| `GET /api/runs/{id}/discards` | Detalle: descartes |
| `GET /api/audit-reports/latest` | Compuerta y último reporte |
| `POST /api/runs` (multipart: `file`, `resource_type`, `course_code`, `course_name`) | Cargar un documento; responde `202 {"run_id", "worker_launched"}` |
| `GET /resources/{resource_key}` | Enlace al PDF desde el detalle |

**No hace falta ninguna ruta nueva.** Hay dos mejoras opcionales (ver §6, decisiones 1 y 2):
- `GET /api/resource-types` → `["Sílabo"]`. Hoy la lista está fija en el panel, copiada de `RESOURCE_TYPES`.
- Un campo `statement` en cada regla de `RuleResultView` → `{"rule": "RI-01", "statement": "…", "violations": 0, "sample": []}`. Hoy el panel trae los enunciados de las Tablas 18 y 19 de la tesis.

Todo el acceso pasa por una sola función, `api(metodo, ruta, cuerpo)`, en `panel.js`. En R6 su cuerpo se reemplaza por un `fetch` y el comentario que la acompaña muestra cómo.

## 4. Lo simulado

Todo lo simulado lleva en pantalla la etiqueta `SIMULADO` o `EJEMPLO · NO REAL`, con borde discontinuo.

- **La validación del token.** La maqueta acepta cualquier token. El 401 que muestra es la respuesta real capturada (`IEKG_OPERACION["GET /api/runs (sin token)"]`).
- **El envío.** No se envía nada. Se muestran la petición que saldría y la respuesta `202 {"run_id": 5, "worker_launched": true}`, y se agrega una corrida 5 `pending` que dura lo que dure la página. Su detalle es el de una corrida recién registrada: campos nulos y sin reporte. No se inventa una `resource_key`.
- **El seguimiento automático.** Con datos estáticos no avanza nada. El botón «Actualizar» vuelve a pedir las rutas, y una nota en las corridas no terminadas explica el sondeo de R6.
- **Una corrida con descartes.** Las 4 reales están vacías. El ejemplo es literalmente el de la documentación de la API (`RunDiscards` en `models.py`: `RI-05`, `(a)-[:PART_OF]->(b)`, `Concept PART_OF Course`).
- **La compuerta cerrada.** Las 4 corridas reales la dejan abierta. El ejemplo es el de `LatestAuditReport` en `models.py`, que trae una sola regla (RI-08 con 1 violación).
- **Lo que sale del código o de la tesis y no de la API:** las etiquetas en español de los estados y sus significados (tesis, l. 1217), las traducciones de los motivos de la compuerta (`orchestrator.py`), los enunciados de las reglas (Tablas 18 y 19; EX-01 a EX-03 de la enmienda de ADR-010) y el máximo de 1 reintento de contenido (ADR-010).

## 5. Componentes (esbozo del nivel 3 de C4)

| Componente | Responsabilidad | Rutas que consume |
|---|---|---|
| Acceso del operador | Pide el token, lo guarda en la pestaña y vuelve aquí ante un 401. | — (a través del cliente) |
| Cliente de operación | Una función por ruta. Añade `Bearer`, traduce 401, 404 y 422 y es el único que habla con la API. | Las cinco de operación |
| Compuerta y último reporte | Estado de la compuerta y resumen del último reporte. | `GET /api/audit-reports/latest` |
| Formulario de carga | Valida igual que la API y envía el multipart. | `POST /api/runs` |
| Lista de corridas | Lista y estado. Hace sondeo mientras haya alguna `pending` o `running`. | `GET /api/runs` |
| Detalle de corrida | Fechas, documento, modelo y reporte de cierre. Enlaza el PDF. | `GET /api/runs/{id}`, `GET /resources/{key}` |
| Descartes | Violaciones, lote candidato y salida cruda, con su estado vacío. | `GET /api/runs/{id}/discards` |
| Tabla de reglas | Muestra un reporte regla por regla. La comparten el detalle y el último reporte. | — |

```likec4
// Borrador: componentes del panel dentro del contenedor existente kms.web.
// Prefijo «op» para no chocar con los componentes de navegación de la propuesta elegida.
model {
  extend kms.web {
    opAccess = component 'Acceso del operador' {
      technology 'JS, sessionStorage'
      summary 'Pide el token y lo guarda solo en la pestaña (ADR-013).'
    }
    opClient = component 'Cliente de operación' {
      technology 'fetch'
      summary 'Una función por ruta de operación; añade el token y traduce 401, 404 y 422.'
    }
    opGate = component 'Compuerta y último reporte' {
      summary 'Estado de la compuerta de auditoría y las 15 reglas del último reporte.'
    }
    opUpload = component 'Formulario de carga' {
      summary 'Documento, tipo de recurso, código y nombre del curso.'
    }
    opRuns = component 'Lista de corridas' {
      summary 'Estado de cada corrida; sondeo mientras haya pendientes o en curso.'
    }
    opRunDetail = component 'Detalle de corrida' {
      summary 'Fechas, modelo, versión del prompt, reintentos y reporte de cierre.'
    }
    opDiscards = component 'Descartes' {
      summary 'Violaciones, lote candidato y salida cruda de una corrida rechazada.'
    }
    opRules = component 'Tabla de reglas' {
      summary 'Un reporte de auditoría, regla por regla.'
    }
  }

  operator -> kms.web.opAccess 'Teclea el token'
  operator -> kms.web.opUpload 'Sube un sílabo'

  kms.web.opAccess -> kms.web.opClient 'Entrega el token'
  kms.web.opGate -> kms.web.opClient 'Pide el último reporte'
  kms.web.opUpload -> kms.web.opClient 'Registra la corrida'
  kms.web.opRuns -> kms.web.opClient 'Pide la lista'
  kms.web.opRunDetail -> kms.web.opClient 'Pide la corrida'
  kms.web.opDiscards -> kms.web.opClient 'Pide los descartes'
  kms.web.opGate -> kms.web.opRules 'Muestra con'
  kms.web.opRunDetail -> kms.web.opRules 'Muestra con'

  kms.web.opClient -> kms.api.opsRoutes 'Alta de corrida, estado, descartes y reporte' {
    technology 'HTTP/JSON, Bearer'
  }
  kms.web.opRunDetail -> kms.api.navRoutes 'Abre el documento de la corrida' {
    technology 'HTTP, /resources/{key}'
  }
}
```

## 6. Decisiones del panel

1. **Tipos de recurso.** El MVP admite solo «Sílabo», y el panel lo tiene fijo. Cuando haya un segundo tipo, la API expone la lista (`GET /api/resource-types`) y el panel deja de repetir el dominio.
2. **Enunciados de las reglas.** La API devuelve solo el código de cada regla; el panel copia el enunciado de la tesis. La alternativa es agregar `statement` a la respuesta en R4, que deja una sola fuente pero obliga a decidir en qué idioma vive el enunciado: en `rules.py` está en inglés y en la tesis, en español.
3. **Seguir el estado.** Sondeo cada 5 s, solo mientras haya una corrida `pending` o `running`. Una ingesta dura de 30 a 75 s (las 4 reales), así que no justifica WebSocket ni SSE.
