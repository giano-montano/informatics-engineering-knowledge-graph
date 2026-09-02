# ADR-004: Reproyección destructiva en lugar de reconciliación incremental

**Estado:** Aceptada
**Fecha:** 2026-08
**Atributos:** AC-04 (principal), AC-02

## Contexto

Durante el ciclo del proyecto la capa de referencia se corrige (recuración de CS2023) y los sílabos se reprocesan varias veces. Hay que decidir cómo se aplican esos cambios al grafo ya cargado.

La reconciliación incremental —comparar el estado actual con el deseado y aplicar solo las diferencias— exige lógica de diff, resolución de conflictos y pruebas propias. Es un subsistema, no una función.

## Decisión

Ante un cambio, el grafo se reconstruye desde los artefactos versionados en archivo. **Nada nace en el grafo:** todo elemento tiene su origen en un archivo bajo control de versiones y se recarga desde ahí.

El aislamiento que exige AC-04 no es de estado en la base, sino de **etapas del proceso**: una corrección de la capa de referencia se resuelve recargando el backbone desde archivo, sin volver a ejecutar la extracción con modelo de lenguaje, que es la etapa cara.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Reconciliación incremental | Complejidad desproporcionada para un prototipo de tesis; introduce estados intermedios difíciles de auditar (AC-02). |
| Escritura acumulativa sin reconstrucción | El grafo acumula elementos huérfanos de versiones anteriores; el estado deja de ser reproducible desde los archivos. |

## Consecuencias

- El estado del grafo es reproducible en cualquier momento desde los artefactos versionados.
- Cualquier dato que solo exista en la base se pierde en la siguiente reconstrucción. **Restricción de diseño:** si en el futuro se incorpora curación experta o cualquier estado editado en el grafo, debe persistirse en archivo o esta decisión debe revisarse.
- El costo de reconstruir es aceptable a la escala del piloto; a escala mayor habría que revisarla.
