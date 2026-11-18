# ADR-004: Reproyección destructiva en lugar de reconciliación incremental

**Estado:** Aceptada, en parte reemplazada por ADR-012 (enmendada 2026-09-29 y 2026-10)
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

## Enmienda (2026-09-29)

- **Alcance.** La reconstrucción aplica ante correcciones del backbone que no cambian claves (etiquetas, descripciones), cambios en el código de proyección y constructos que solo existen en el grafo. No aplica ante cambios de clave, fusión o eliminación de unidades ni cambios de la T-Box: esos exigen transformar los hechos guardados con un script escrito para cada cambio.
- **Documentos reprocesados.** Reingestar un documento no dispara la reconstrucción; es una ingesta más (ADR-006).
- **Reaplicación.** Copia los hechos que cada corrida escribió, con claves resueltas y procedencia ya fijada, en el orden original de las corridas. No revalida; la auditoría corre al cierre (ADR-005).

## Enmienda (2026-10)

- **Dos modos, no tres.** La **carga** vacía la base, la inicializa y escribe la capa de referencia. La **reaplicación** se activa por separado, solo después de una carga. «Reproyección» es el nombre del procedimiento de ejecutar ambas, no un modo propio.
