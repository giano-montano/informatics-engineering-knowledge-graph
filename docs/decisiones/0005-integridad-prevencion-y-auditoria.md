# ADR-005: Integridad del grafo por prevención al escribir y auditoría posterior

**Estado:** Aceptada (enmendada 2026-10)
**Fecha:** 2026-09
**Atributos:** AC-01 (principal), AC-02

## Contexto

Neo4j no ejecuta un razonador: los axiomas que HermiT comprobaba sobre la ontología no se hacen cumplir solos en el grafo, y la extracción con modelo de lenguaje produce hechos no deterministas. Neo4j Community solo ofrece restricciones de unicidad. Las condiciones que el grafo debe cumplir están enunciadas como reglas de integridad en el anexo de transición al grafo de propiedades y en el capítulo de arquitectura.

## Decisión

Cada regla de integridad se garantiza dos veces:

1. **Se impide al escribir.** Lo que la viola se rechaza antes de escribir, o la forma misma de la escritura no puede expresarlo. La escritura sigue el orden validar → escribir → hacer commit.
2. **Se comprueba después.** Al cierre de cada carga del backbone, ingesta y reproyección, la auditoría ejecuta una consulta Cypher por regla sobre el grafo completo y emite un reporte por regla.

Una violación que la auditoría encuentra tras una ingesta se trata como error de código: se emite el reporte, se detiene la ingesta y decide el operador.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Restricciones de existencia, tipo y clave; graph types de GQL | Exclusivas de Neo4j Enterprise o no disponibles en Community con Cypher 5. |
| Disparadores de APOC | Desactivados por defecto, se instalan desde la base system, se propagan con un refresco de 60 s y no están en Aura. Solo frenarían escrituras hechas por fuera del sistema, que el escritor único ya excluye. |
| Comprobación dentro de la transacción antes de hacer commit | Redundante con la prevención al escribir; la auditoría ya cubre los errores de implementación. |
| Reproyección automática ante una violación | Desproporcionada para el fallo de un documento; la reproyección es un remedio que decide el operador. |

## Consecuencias

- Hay un único escritor a la vez: impedir algunas reglas exige consultar nodos existentes, y eso solo es fiable si nadie más escribe entre la lectura y el commit.
- Toda regla debe poder comprobarse con una consulta Cypher; una condición que no pueda comprobarse así no es regla de integridad.
- El diseño del pipeline documenta, regla por regla, qué mecanismo la impide.
- El reporte de integridad (RF-09) es uno solo y cubre todas las reglas.
- Nada protege frente a escrituras hechas por fuera del sistema.

## Enmienda (2026-10)

- **Cuándo corre la auditoría.** Al cierre de la carga, de cada ingesta y de la reaplicación (ADR-004).
- **Ante una violación tras una ingesta.** Se emite el reporte, la corrida queda *detenida por auditoría* y la compuerta de ADR-007 suspende las ingestas pendientes hasta que una reconstrucción la reabra. El operador dispone del reporte como evidencia, no del remedio: el remedio es un procedimiento de construcción que ejecuta el desarrollador, con el sistema detenido (ADR-004).
- **Escritor único.** El intervalo que protege va desde la lectura de la instantánea hasta el commit (ADR-007, ADR-011).
- **Mecanismo por regla.** El validador impide RI-05, RI-08, RI-10, RM-02, RM-04 y RM-05; la forma de la escritura, RI-02, RI-03, RI-04, RI-06, RI-09, RM-01 y RM-03; la restricción de unicidad, junto con el MERGE por clave, RI-01. RI-07 no aplica en la ingesta.
- **Relación con ADR-002.** Este régimen reemplaza los cuatro mecanismos de ADR-002. La existencia de propiedad queda descartada por ser exclusiva de Enterprise (ver Alternativas).
