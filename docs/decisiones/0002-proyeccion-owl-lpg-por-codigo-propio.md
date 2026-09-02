# ADR-002: Proyección OWL → grafo de propiedades por código propio

**Estado:** Aceptada
**Fecha:** 2026-08
**Atributos:** AC-01 (principal), AC-02

## Contexto

Elegido Neo4j (ADR-001), hay que decidir cómo se lleva la ontología al grafo de propiedades y, sobre todo, quién sostiene en ejecución las restricciones que HermiT comprobaba en diseño: dominio y rango de cada propiedad de objeto, disyunción entre clases, funcionalidad de la pertenencia de unidad a área, y el invariante de cuatro niveles.

Nada de eso sobrevive automáticamente a la proyección. La decisión no es de conversión de formatos, sino de dónde vive cada garantía.

## Decisión

Proyección implementada como código propio, sustentada en una tabla de mapeo que declara, para cada constructo de la ontología, a qué patrón del grafo se proyecta y qué mecanismo lo sostiene en ejecución. Los mecanismos disponibles son cuatro:

1. Restricción nativa de Neo4j (unicidad, existencia de propiedad).
2. Validación previa a la escritura, en el modelo Pydantic del pipeline.
3. Consulta de auditoría posterior a la carga.
4. Pérdida aceptada, declarada explícitamente.

Todo axioma de la T-Box cae en uno de los cuatro. Ninguno queda sin asignar.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Neosemantics (n10s) | Proyección genérica y opaca sobre el mapeo; convierte tripletas pero no permite decidir por constructo dónde vive cada garantía, que es justamente el objeto de esta decisión. Añade dependencia de plugin. |
| Tipos de grafo GQL (ISO/IEC 39075, Neo4j 2026.02) | Permitiría esquema declarativo en el motor, pero está disponible solo en edición Enterprise. Descartado por edición y fecha, no por adecuación. Se registra como trabajo futuro. |
| Sin proyección explícita: escribir directo desde el pipeline | El pipeline quedaría como única especificación del esquema; imposible auditar la correspondencia con la ontología (AC-02). |

## Consecuencias

- La tabla de mapeo es la especificación del módulo, no documentación accesoria. Si diverge del código, el código está mal.
- Las pérdidas aceptadas quedan declaradas y son defendibles; las no declaradas son defectos.
- Los mecanismos de tipo 3 producen la lista de invariantes que da denominador a la medida de AC-02. **Pendiente:** numerarlos al cerrar la tabla.
- Mayor esfuerzo de implementación que usar el plugin, asumido a cambio del control sobre el régimen de validación.
