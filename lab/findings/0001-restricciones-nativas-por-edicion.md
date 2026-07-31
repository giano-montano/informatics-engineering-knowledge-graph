# 0001 — Qué restricciones soporta Neo4j según la edición

- **Fecha:** 2026-07-31
- **Sustentabilidad:** alta. Medición propia reproducible sobre imágenes oficiales, concordante con la documentación oficial de Neo4j. Citable en la tesis.
- **Afecta a:** R4 (pipeline de ingesta), diseño del archivo declarativo de reglas de esquema.

## Pregunta

Las reglas de esquema pueden resolverse como restricción nativa, validación previa a la escritura, o consulta de integridad. ¿Cuáles de mis cinco tipos de regla admiten realmente una restricción nativa, y qué pasa con ellas cuando el despliegue final pase de Enterprise a Community?

## Método

Script `lab/scripts/probe_constraints.sh`: intenta crear cada tipo de restricción con `CREATE CONSTRAINT`, reporta éxito o el mensaje de error, y limpia lo que creó. Ejecutado sobre las imágenes oficiales `neo4j:5.26.28-enterprise` y `neo4j:5.26.28`, misma versión de kernel en ambas para que la única variable sea la edición.

```
docker compose exec -T neo4j bash -s < lab/scripts/probe_constraints.sh
```

## Resultado

| Restricción | Enterprise | Community |
|---|---|---|
| Unicidad, nodo (`IS UNIQUE`) | sí | **sí** |
| Unicidad, relación | sí | **sí** |
| Clave compuesta (`IS NODE KEY` / `IS RELATIONSHIP KEY`) | sí | no |
| Existencia (`IS NOT NULL`) | sí | no |
| Tipo de propiedad (`IS :: STRING`) | sí | no |

Community rechaza las tres últimas con el mensaje `requires Neo4j Enterprise Edition`.

## Lo que no existe en ninguna edición

Ni Enterprise ni Community tienen restricción nativa para:

- etiquetas disjuntas,
- cardinalidad de relaciones (relación funcional),
- dominio y rango de relaciones,
- aciclicidad.

Neo4j es *schema-optional* por diseño: el motor no conoce la noción de tipo de nodo más allá de las etiquetas, y no valida la forma del grafo.

## Consecuencia de diseño

De los cinco tipos de regla del archivo declarativo, **solo la clave única se resuelve como restricción nativa**, y es justamente la única portable a Community. Los otros cuatro viven forzosamente en validación previa a la escritura y consultas de integridad.

Dos lecturas:

1. El intérprete de reglas es más pequeño de lo previsto: la rama "restricción nativa" atiende un caso de cinco.
2. **La alarma Enterprise→Community queda descartada para el esquema.** Existencia y clave compuesta sí se pierden al migrar, pero ninguna de las cinco reglas depende de ellas. El riesgo real de esa migración es cero en este frente.

Sigue en pie una restricción distinta y no relacionada: Community solo admite una base de datos de usuario, así que el diseño no puede depender de multi-base. El backbone y el slice viven en la base `neo4j`.

## Contradicción registrada

Durante esta misma sesión advertí que la elección "Enterprise ahora, Community al desplegar" ponía en riesgo las reglas resueltas como restricción nativa. La medición muestra que la advertencia no aplica a este conjunto de reglas. Queda anotada porque volvería a aplicar si en el futuro se añade una regla de existencia o de clave compuesta.
