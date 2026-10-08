# ADR-010: Rechazo por documento, reintentos y registro de descartes

**Estado:** Aceptada (enmendada 2026-10)
**Fecha:** 2026-10
**Atributos:** AC-01 (principal), AC-02

## Contexto

Un lote rechazado no se escribe (ADR-006). Falta decidir qué unidad forma el lote, qué hacer ante los errores del proveedor del modelo de lenguaje, qué se guarda de lo rechazado y qué estados distinguen esos casos. De esto depende la medida de AC-01: las afirmaciones rechazadas por documento y por tipo de regla.

ADR-003 enviaba los fallos a una cola de revisión y descartaba todo reintento. Esta decisión reemplaza ambas cosas.

## Decisión

- **El lote es el documento completo.** El validador acumula todas las violaciones, no solo la primera.
- **Errores transitorios del proveedor** (tiempo agotado, límite de peticiones, caída): reintentos acotados dentro del extractor. Si se agotan, la corrida queda *fallida*.
- **Salida no conforme al esquema:** como máximo un reintento que le devuelve al modelo el error. Si también falla, la corrida queda *rechazada* con el código EX-01, que no es una regla de integridad ni tiene consulta de auditoría.
- **Escritura que no produce lo esperado:** el repositorio revierte la transacción y la corrida queda *fallida*. El worker sigue con la siguiente.
- **Registro de descartes:** por cada corrida rechazada, una fila por violación (regla, hecho, mensaje) y el lote candidato completo. Una corrida *fallida* no genera descarte.
- **Estados de una corrida:** pendiente, en curso, terminada, rechazada, fallida, escrita sin persistir y detenida por auditoría.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Lote por subárbol de tema o hecho a hecho | Menos destructivo, pero exige ordenar dependencias y decidir qué hacer con las aristas que cruzan lotes. Queda como evolución. |
| Sin reintento ante salida no conforme | Mediría al modelo por separado; se mide el pipeline como sistema. |
| Reintento ilimitado, o sin informar el error | Es el reintento ciego que ADR-003 excluye: oculta los casos que el esquema no cubre. |
| Guardar solo las violaciones | Se pierde lo que arrastró el todo o nada y la posibilidad de medir la precisión de un documento rechazado. |

## Consecuencias

- El todo o nada por documento castiga más a los sílabos largos. Se declara como limitación.
- Cada corrida reporta cuántos reintentos de contenido usó. Las medidas se declaran tomadas después de ese reintento.
- La distinción entre *rechazada* y *fallida* separa el descarte por contenido de las fallas de ejecución, del proveedor o de la escritura.

## Enmienda (2026-10)

- **Qué es una salida no conforme.** Son tres casos, con un código cada uno, que comparten el único reintento de contenido:
  - **EX-01:** la salida no se ajusta al esquema de salida.
  - **EX-02:** una mención enlazada trae una clave que no está en la instantánea.
  - **EX-03:** una clave existente es, en la instantánea, de otra clase que la que exige su lugar en la salida.

  EX-01 lo detecta la validación tipada; EX-02 y EX-03, el extractor al enlazar, antes de armar el lote. Sin EX-03, un error de clase lo frenaría la escritura y la corrida quedaría *fallida* en lugar de *rechazada*. Ninguno es regla de integridad ni tiene consulta de auditoría. Las menciones repetidas y las aristas duplicadas no son salida no conforme: el código las fusiona antes de armar el lote.
