# ADR-008: Esquema del grafo como declaración única

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-01 (principal), AC-02

## Contexto

Lo que el grafo admite —etiquetas, tipos de arista con sus pares, propiedades y valores de capa— lo usan cuatro partes del sistema: el esquema de salida del extractor, el validador, las plantillas de escritura y las consultas de auditoría. Si cada una lo declara por su cuenta, pueden desalinearse sin que nada lo detecte. Hay que decidir dónde se declara y de dónde sale.

## Decisión

- Una sola declaración, el **esquema del grafo**: un módulo de Python con constantes, que leen los cuatro consumidores. Contiene datos, no lógica.
- **Se escribe a mano** a partir de las Tablas 1 y 2 del anexo de transición; no se genera desde el TTL.
- Una prueba que contraste la declaración con el TTL se construye **después de que el núcleo de R4 funcione**. Si no llega a hacerse, se declara como limitación. Si se hace, lleva pruebas negativas sobre copias alteradas del TTL que demuestren que puede fallar.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Generar la declaración desde el TTL con rdflib | Exige analizar uniones anónimas, inversas y subpropiedades de `owl:topObjectProperty` para una T-Box cerrada. Además, la dirección afirmada de cada par inverso no se deduce del TTL, así que igual hace falta una lista escrita a mano. |
| Archivo de configuración (YAML) | Solo lo lee Python; un formato más no aporta nada. |
| Que cada consumidor declare lo suyo | Los cuatro podrían desalinearse en silencio. |

## Consecuencias

- La declaración no es configuración: no cambia entre despliegues. Solo cambiaría con la T-Box, y ese cambio ya exige migración (ADR-004).
- Sin la prueba contra el TTL, la correspondencia entre la ontología y la declaración descansa en la revisión manual del anexo.
- La lógica que no es dato (clave única, procedencia, anclaje, ciclos) vive en el código del núcleo, no en la declaración.
