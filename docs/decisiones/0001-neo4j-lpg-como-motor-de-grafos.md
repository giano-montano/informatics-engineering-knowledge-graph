# ADR-001: Neo4j (grafo de propiedades) como motor de ejecución

**Estado:** Aceptada
**Fecha:** 2026-08
**Atributos:** AC-05 (principal), AC-01, AC-03

## Contexto

El modelo del dominio se expresó en OWL 2 y se validó con HermiT (R1). Para la ejecución hay que elegir entre mantener la representación en RDF sobre un triplestore, o proyectarla a un grafo de propiedades.

El sistema no necesita inferencia en ejecución: el razonamiento ocurre en tiempo de diseño sobre la T-Box. Lo que sí necesita son recorridos: cierre transitivo de prerrequisitos entre conceptos, agregación de recursos sobre cuatro niveles de partonomía, y consultas de navegación desde la interfaz.

## Decisión

Neo4j Community, Cypher 5 LTS, base de datos única. El grafo de propiedades es el modelo físico; OWL queda como modelo conceptual y fuente de la especificación.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Triplestore RDF con razonamiento en ejecución | Inferencia innecesaria: el razonamiento se resuelve en diseño. Costo operativo sin beneficio. |
| Triplestore RDF sin razonamiento | Recorridos de longitud variable menos directos que en Cypher; las propiedades de arista requieren reificación. |
| Base de datos relacional | Los cierres transitivos exigen recursión sobre joins; el modelo de navegación no se expresa con naturalidad. |

## Consecuencias

- Los recorridos de longitud variable y la agregación multinivel se expresan directamente en Cypher (AC-05).
- Las aristas admiten propiedades sin reificación, lo que permite registrar procedencia por arista (AC-03).
- **Se pierde la garantía semántica de OWL en ejecución.** El grafo de propiedades no valida dominio, rango ni disyunción. Esa pérdida se compensa en el módulo, y su régimen se define en ADR-002 y en la tabla de mapeo.
- La edición Community limita opciones de esquema declarativo (ver ADR-002).
