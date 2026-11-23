# Verificación de AC-04 sobre el grafo de la medición de R4

**Fecha:** 2026-11-22 (19:30 a 19:31, hora de Lima) · **Grafo:** el de la corrida de
medición del 2026-11-16, reconstruido en el despliegue local (818 nodos, 2 898 aristas)
· **Código:** rama `dev`, núcleo sin cambios desde el tag `codigo-congelado-2026-11-16`.

## Escenario (tesis, Tabla 23)

Se corrige una etiqueta de la capa de referencia, se carga y se reaplica. Se espera:
ninguna llamada al modelo de lenguaje, la capa institucional igual (mismos nodos y
aristas) y la auditoría sin violaciones.

## Procedimiento

1. Se copiaron los almacenes del despliegue local (operacional, hechos y documentos) a
   una carpeta temporal, para no agregar reportes al almacén en servicio ni tocar
   `var/medicion-r4/`.
2. Se volcó la capa institucional con `ac04_volcado.py`: cada nodo con su clave,
   etiquetas y propiedades, y cada arista que sale de un nodo institucional con su
   tipo, sus extremos y sus propiedades.
3. Se detuvo la API, único escritor mientras el sistema está en servicio (ADR-007).
4. En una copia de `ontology/backbone_cs2023.ttl` se cambió una sola línea: la
   etiqueta en español de KU-OS-Purpose, de «Rol y Propósito de los Sistemas
   Operativos» a «Rol y propósito de los sistemas operativos». El archivo versionado
   no se tocó.
5. Se ejecutaron `iekg-build load` (con `IEKG_BACKBONE` apuntando a la copia) e
   `iekg-build reapply`, con las variables del proveedor vacías y la URL del
   proveedor apuntando a un puerto cerrado.
6. Se volvió a volcar la capa institucional y se comparó con el primer volcado.
7. Se restauró el grafo con el backbone original (`load` y `reapply`), se comprobó
   que el volcado coincidía con el primero y se volvió a levantar la API.

## Resultado

| Comprobación | Resultado |
|---|---|
| Llamadas al modelo de lenguaje | Ninguna. El almacén operacional tenía 14 corridas y 237 457 tokens de entrada y 70 068 de salida antes, y los mismos después. Los procesos de construcción no leen la configuración del proveedor. |
| Capa institucional | Idéntica: 638 nodos y 2 557 aristas, con sus propiedades. |
| Etiqueta corregida | KU-OS-Purpose quedó con «Rol y propósito de los sistemas operativos». |
| Auditorías | Carga (reporte 17) y reaplicación (reporte 18): 0 violaciones en las 15 reglas. |
| Duración | 12 s, de la carga al fin de la reaplicación. |
| Restauración | El grafo restaurado coincide con el volcado inicial; auditorías 19 y 20, limpias. |

AC-04 se cumple.
