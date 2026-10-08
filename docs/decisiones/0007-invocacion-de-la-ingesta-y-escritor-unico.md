# ADR-007: Invocación de la ingesta y escritor único del grafo

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-01 (principal), AC-02, AC-04

## Contexto

Impedir al escribir las reglas que dependen de nodos existentes exige que nadie más escriba en el grafo entre la lectura y el commit (ADR-005). Escriben en él tres caminos: la ingesta, que se dispara cuando el operador sube un documento, y la carga y la reaplicación, que ejecuta el desarrollador. Hay que decidir cómo se lanza la ingesta, cómo se serializa, cómo se suspende tras una auditoría con violaciones y dónde viven los procesos de construcción.

## Decisión

- La API no escribe en el grafo. Al recibir un documento registra la corrida como pendiente en el almacén operacional y **lanza el worker como proceso hijo** si no hay uno activo. El worker procesa las corridas pendientes en orden de llegada y termina.
- **Compuerta de auditoría.** Antes de tomar cada corrida, el worker lee el último reporte de auditoría registrado. Si tiene violaciones, termina y deja las corridas pendientes. La compuerta se reabre con el siguiente reporte limpio, que solo pueden producir los procesos de construcción: una carga o una reaplicación.
- Los **procesos de construcción son un contenedor dentro de la frontera del sistema**: son código propio, bajo control propio. Se ejecutan desde la línea de comandos, **con el sistema detenido**.
- API, worker y procesos de construcción salen de **una sola imagen con tres puntos de entrada**.
- La aplicación web se sirve **aparte**, con nginx, que reenvía `/api` y `/resources` a la API bajo un mismo dominio.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Webhook HTTP hacia un segundo servicio | Un servicio más que desplegar para serializar algo que un proceso hijo ya serializa. |
| Daemon residente que sondea el almacén operacional | Un proceso permanente para una carga de trabajo esporádica. |
| Worker en un contenedor propio | El proceso hijo no cruza contenedores; habría que agregar una cola o un candado. |
| Bandera de suspensión que el desarrollador apaga a mano | Depende de que alguien la recuerde, y se puede apagar sin haber reconstruido. |
| Procesos de construcción como sistema externo | Un sistema externo está fuera del control propio; estos procesos no lo están. |
| La API sirve la aplicación web | Redesplegar la interfaz reiniciaría la API y mataría una ingesta en curso. Además, R6 consume R4 como caja negra, y esta opción despliega R6 dentro del artefacto de R4. |

## Consecuencias

- El escritor único es una **condición de operación**, no un mecanismo. Supone que la API corre en un solo proceso y que el operador sube un documento a la vez: nada impide técnicamente que coincidan dos workers, ni un proceso de construcción con un worker en curso. Una corrida que llega mientras el worker termina queda pendiente hasta la siguiente subida. Se declara como limitación.
- Reiniciar la API interrumpe al worker. La corrida queda *en curso* o *escrita sin persistir* (ADR-010), sin recuperación automática; se declara como limitación.
- Mientras la compuerta está cerrada, la API sigue registrando corridas: quedan pendientes hasta que una reconstrucción con auditoría limpia la reabra.
- Una carga limpia también reabre la compuerta. Reaplicar antes de volver a ingestar es parte del procedimiento, no algo que el sistema imponga: una ingesta sobre una carga sin reaplicar no vería la capa institucional y podría duplicar sus nodos.
- Con una sola imagen, la ingesta y la reaplicación ejecutan por construcción la misma versión del núcleo, lo que sostiene AC-04.
- El desarrollador no es actor del sistema: los procesos de construcción no tienen flecha entrante en el diagrama de contenedores.
