# ADR-014: Reglas de integridad como código sobre el esquema declarado

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-02 (principal), AC-01

## Contexto

La restricción del asesor pide una especificación declarativa y un intérprete pequeño, sin prescribir formato. ADR-008 fijó el formato del esquema del grafo y dejó en el código del núcleo la lógica que no es dato. Falta responder por qué las quince reglas (RI-01 a RI-10 y RM-01 a RM-05) no se expresan en un estándar ni en un formato propio, y qué parte del sistema es la especificación.

Se registra después de implementar la carga del backbone, y no cambia su código. El traspaso del laboratorio descartaba SHACL porque «no lee un LPG». Ese motivo no es exacto: el módulo de validación de neosemantics (n10s) valida un grafo de Neo4j contra formas SHACL. Los motivos reales van en la tabla.

## Decisión

- **La especificación es lo que es dato.** Por un lado, el esquema del grafo (ADR-008): etiquetas, tipos de arista con sus pares, propiedades y capas. Por otro, el catálogo de reglas de `core/rules.py`: el código y el enunciado de cada regla, y los parámetros que son dato, como el padre que requiere cada nivel y los tipos de arista sin ciclos.
- **El intérprete es el núcleo**: las plantillas de escritura, las comprobaciones del validador y las consultas del auditor, en Python y Cypher. Toman de la especificación los nombres que usan.
- Cada regla tiene una consulta de auditoría y, si el validador la impide, una comprobación. Ninguna regla se escribe en un tercer lenguaje.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| YAML u otro formato de configuración para las reglas | Cinco reglas tienen estructura propia: anclaje, ciclos, frontera, procedencia y funcionalidad. Expresarlas exige un minilenguaje con su intérprete, que también hay que probar y defender, o Cypher incrustado como texto, que es código con otra extensión. Además, sigue valiendo el argumento de ADR-008: solo lo lee Python. |
| SHACL sobre la base de grafos, con n10s | n10s es un proyecto de Neo4j Labs, sin soporte ni garantías de compatibilidad, y ADR-002 ya lo descartó. SHACL Core no tiene un componente que compare los valores de un camino con el propio nodo foco: los de pares de propiedades los comparan con los valores de una propiedad del nodo foco. La aciclicidad de RM-04 queda, por eso, del lado de las restricciones basadas en SPARQL, que la documentación de n10s no menciona. Y solo cubriría la auditoría: el validador trabaja en memoria sobre el lote y la instantánea (ADR-011), no sobre RDF. |
| SHACL sobre el TTL del backbone, antes de proyectar | Validaría la fuente en mundo cerrado y vería lo que HermiT no ve, como ausencias y conteos. Pero no cubre la ingesta, que es donde nacen los hechos no deterministas. Queda como trabajo futuro, como extensión de R2. |
| Graph types de GQL | Descartados en ADR-002 y ADR-005: exclusivos de Enterprise y de Cypher 25. |

## Consecuencias

- Regla por regla, lo que se defiende es una función o una consulta corta, no un intérprete genérico.
- Las reglas viven en dos lenguajes, y su catálogo es dato. Llevarlas a otro motor exige reescribir sus consultas.
- Ninguna prueba comprueba el reparto de mecanismos de la Tabla 3 del anexo y la Tabla 20 de la tesis. Ese reparto está en las tuplas de reglas del validador y en el docstring del repositorio.

## Fuentes

- W3C, *Shapes Constraint Language (SHACL)*, Recomendación del 20 de julio de 2017: §4.5, componentes de pares de propiedades; §5 y §6, SHACL-SPARQL. <https://www.w3.org/TR/shacl/>
- Neo4j, *Neo4j Labs*: los proyectos de Labs no tienen soporte ni garantías de compatibilidad. <https://neo4j.com/labs/>
- Neo4j Labs, *Validating Neo4j graphs against SHACL* (neosemantics 5.14). Es la documentación de un proyecto sin soporte: describe la herramienta. <https://neo4j.com/labs/neosemantics/5.14/validation/>
