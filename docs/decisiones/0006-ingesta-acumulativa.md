# ADR-006: Ingesta acumulativa con procedencia fijada al crear

**Estado:** Aceptada
**Fecha:** 2026-09
**Atributos:** AC-03 (principal), AC-01

## Contexto

Un documento institucional puede ingestarse más de una vez, y documentos distintos pueden afirmar el mismo hecho. Hay que decidir qué hace la ingesta con lo que ya existe en el grafo y qué procedencia conserva un hecho que afirman varios documentos.

## Decisión

- La ingesta no borra nodos, aristas ni propiedades. Reingestar un documento, haya cambiado o no, es una ingesta más: lo nuevo se crea y lo existente se fusiona.
- La procedencia de un nodo y la de una arista se fijan al crearlos y no cambian después.
- Si un hecho del lote de ingesta se rechaza, no se escribe ninguno del lote.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Retirar lo que la versión nueva de un documento ya no afirma | Exige comparar versiones de cada documento: es la reconciliación incremental que ADR-004 descarta. |
| Acumular todas las procedencias de un hecho | Un documento que repite un hecho no agrega nada al grafo; complica la escritura sin beneficio en el piloto. |
| Registrar en cada arista las corridas que la afirmaron | Solo detecta afirmaciones desactualizadas, no las corrige. |

## Consecuencias

- La procedencia indica el primer documento que afirmó el hecho, no todos los que lo respaldan. Como depende del orden de ingesta, el orden del piloto se fija y se declara.
- Si un documento cambia y se vuelve a ingestar, lo que la versión nueva ya no afirma permanece con su procedencia anterior. Es una limitación del MVP; retirarlo queda como trabajo futuro.
- Un nodo ya anclado no pierde su arista de partonomía, así que la regla de anclaje solo se valida sobre los nodos nuevos.
- El tamaño del lote de ingesta queda para el diseño del pipeline.
