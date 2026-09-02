# ADR-003: El modelo de lenguaje no escribe en la base de datos

**Estado:** Aceptada
**Fecha:** 2026-08
**Atributos:** AC-01 (principal), AC-02, AC-03

## Contexto

La capa institucional se puebla extrayendo hechos de sílabos en PDF con un modelo de lenguaje. La salida de un modelo de lenguaje no es determinista, puede alucinar entidades y puede proponer relaciones que la ontología no admite.

Existe la opción de darle al modelo la capacidad de generar y ejecutar Cypher directamente, o de operar como agente con acceso a la base.

## Decisión

El modelo de lenguaje produce **exclusivamente** hechos candidatos en salida estructurada, contra un esquema Pydantic. No genera Cypher, no accede a la base, no decide escrituras.

El pipeline es:

```
PDF → parseo (Docling)
    → recuperación del subgrafo relevante (anclaje)
    → extracción con modelo de lenguaje, salida estructurada
    → validación contra el esquema Pydantic
    → enlace de entidades contra nodos existentes
    → generación determinista de Cypher idempotente (MERGE)
    → consultas de integridad posteriores
```

Todo lo que sigue a la extracción es código determinista. Los fallos (JSON inválido, incoherencia de esquema, duplicación) van a cola de revisión; no se reintenta a ciegas.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| El modelo genera Cypher | Ninguna garantía de conformidad con la ontología; imposible acotar qué puede escribir (AC-01). |
| Agente con acceso a la base | Mismo problema, con efectos no reproducibles: la misma entrada puede producir grafos distintos (AC-02). |
| Reintento automático ante fallo de validación | Convierte el fallo en ruido y oculta los casos que el esquema no cubre. |

## Consecuencias

- La conformidad del grafo con la ontología es alta por construcción: lo que no pasa la validación no llega a la base.
- Por lo mismo, la auditoría posterior rara vez encontrará violaciones. La medida operativa complementaria es el conteo de hechos candidatos descartados en validación, por motivo (ver AC-01).
- La escritura idempotente permite reprocesar un documento modificado sin duplicar (AC-03).
- El costo del ciclo se concentra en la etapa de extracción, que es la que AC-04 busca no re-ejecutar innecesariamente.
