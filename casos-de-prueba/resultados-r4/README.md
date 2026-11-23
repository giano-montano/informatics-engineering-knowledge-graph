# Resultados de la medición de R4

Copia estática de la evidencia de R4. Los originales viven en `var/`, que git ignora;
aquí se versionan tal como salieron, sin editar.

| Archivo | Qué es | Origen |
|---|---|---|
| `extraccion-cp01-cp14-20261116.json` | CP-01 a CP-14 sobre la corrida de medición: por caso y en total (los 13, los 11 del ajuste y los 2 retenidos), intentos, fusión y el diagnóstico con la definición anterior de ítem | `scripts/evaluate_ingestion.py cases --from-run 1`, almacenes de `var/medicion-r4/` |
| `contraste-participante-1-20261116.json` | Extracción del primer participante contra la anotación congelada y contra el pipeline | `evaluate_ingestion.py review`, `revision/revisor-1/` |
| `contraste-participante-2-20261116.json` | Lo mismo para el segundo participante, con su adjudicación | `revision/revisor-2/` |
| `acuerdo-entre-participantes-20261115.json` | Nombres que comparten las dos extracciones | `evaluate_ingestion.py` |
| `reporte-cp15.md`, `reporte-cp16.md` | Juicio de las relaciones, con la forma de `formato-de-reporte-de-prueba.md` | `relaciones/juicio-de-relaciones-semilla-20261116.xlsx` |
| `ac04-registro.md`, `ac04_volcado.py` | Verificación de AC-04: corrección de una etiqueta, carga y reaplicación | Despliegue local, 2026-11-22 |
| `ac05-20261122.json` | Verificación de AC-05: los cinco patrones sobre el grafo final | `scripts/measure_navigation.py` |
| `openapi.json` | La especificación OpenAPI que genera la API (rutas, parámetros y esquemas) | `GET /openapi.json` de la API en servicio |

La corrida de medición se hizo el 2026-11-16 con el código del tag
`codigo-congelado-2026-11-16` y la anotación del tag `anotacion-corregida-2026-11-16`.
Cómo calcula el evaluador cada medida:
[`calculo-de-las-medidas-del-evaluador.md`](../calculo-de-las-medidas-del-evaluador.md).
