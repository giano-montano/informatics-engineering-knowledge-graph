# ADR-012: Almacén de hechos: un archivo por corrida, sin control de versiones

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-04 (principal), AC-02

## Contexto

La reaplicación reconstruye la capa institucional desde los hechos que cada corrida escribió (ADR-004). ADR-004 suponía que esos hechos vivían bajo control de versiones, pero el almacén está en la máquina virtual del despliegue, lejos del repositorio de código. Hay que decidir qué se guarda, en qué forma y si se versiona.

Esta decisión reemplaza lo que ADR-004 dice sobre «artefactos versionados» en cuanto a los hechos institucionales. El TTL del backbone sigue versionado con el código.

## Decisión

- **Un archivo por corrida** que escribió, nombrado con el identificador de la corrida y escrito una sola vez, después de confirmar la transacción. La carpeta es su propio historial; se respalda copiándola en hitos, como la corrida de medición.
- **Cada archivo guarda exactamente el lote que recibió el escritor**, con las claves resueltas y la procedencia fijada, incluidos los hechos que ya existían. Así la reaplicación repite las mismas escrituras que la ingesta.
- **La reaplicación salta las corridas detenidas por auditoría.** Nada escrito después de una detención pudo leer lo que escribió la corrida detenida: la compuerta de ADR-007 impide ingestar hasta reconstruir, y la reconstrucción empieza con una carga que lo borra. Excluirla, por tanto, no rompe dependencias. Remedio ante un error de código: corregir, cargar, reaplicar y volver a subir ese documento.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Versionado manual en git, como suponía ADR-004 | El almacén vive en la máquina virtual y el repositorio en la del desarrollador. Archivos escritos una sola vez ya forman su propio historial; git solo agregaría un paso manual que se puede olvidar. Además, los archivos no sirven en otro host (ADR-009). |
| Un solo archivo acumulado | Una escritura a medias dañaría el historial completo; con un archivo por corrida, ninguna corrida puede dañar las anteriores. |
| Guardar solo lo que la corrida creó | Exige distinguir al escribir lo creado de lo fusionado, y la reaplicación ya no repetiría las mismas escrituras que la ingesta. |

## Consecuencias

- Sin respaldo, perder la carpeta es perder la capa institucional: habría que volver a ingestar todos los documentos.
- Los archivos llevan el host en los localizadores, así que no se reutilizan en otro host (ADR-009).
- Si el worker se interrumpe entre confirmar y persistir, la corrida queda *escrita sin persistir* y la reaplicación no la reproduce (ADR-010).
