# ADR-011: Instantánea del grafo por corrida

**Estado:** Aceptada
**Fecha:** 2026-10
**Atributos:** AC-01 (principal), AC-03

## Contexto

El extractor necesita ver los nodos existentes para anclar los temas a unidades reales y enlazar menciones sin duplicar. El validador necesita las etiquetas de los extremos existentes, el anclaje, la capa y las aristas de prerrequisito y especialización para impedir ciclos. Hay que decidir cómo obtienen esa información, y si la regla de ciclos se impide al escribir o solo se audita.

Esta decisión reemplaza la «recuperación del subgrafo relevante» del pipeline de ADR-003 y la validación «en el modelo Pydantic» de ADR-002.

## Decisión

- Al empezar cada corrida, el repositorio lee una **instantánea del grafo**: todos los nodos, con su clave, etiqueta, clase, área y capa, y las aristas de prerrequisito y especialización.
- El extractor recibe **el vocabulario completo**, sin recuperación selectiva. Devuelve cada mención con la clave de un nodo existente o marcada como nueva. El enlace compara las menciones nuevas, por etiqueta normalizada, con los nodos de la misma clase.
- **El validador trabaja en memoria** sobre la instantánea y el lote, sin consultar la base. Se ejecuta después del enlace, en un solo paso. El modelo Pydantic solo tipa la salida del extractor; no comprueba reglas.
- **La regla de ciclos (RM-04) se impide al escribir**, sobre las aristas de la instantánea más las del lote.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Recuperación selectiva de candidatos | Un componente más, cuyo criterio de selección hay que diseñar y medir; a escala piloto el vocabulario completo cabe en el contexto del modelo. |
| Validación en dos partes, con lecturas por clave alrededor del enlace | Con la salida tipada y la instantánea en memoria, separarla no ahorra lecturas. |
| Ciclos solo detectados en la auditoría | La reaplicación reescribiría el ciclo desde el almacén de hechos, y una violación auditada dejaría de significar un error de código (ADR-005). |
| Similitud por embeddings | Exigiría calcular y quizá persistir vectores; el MVP no los usa. |

## Consecuencias

- La vigencia de la instantánea descansa en el escritor único (ADR-007).
- El validador es una función pura y se prueba sin Neo4j.
- **Límite de generalización:** el diseño vale a escala piloto. Con muchos más documentos, el vocabulario dejaría de caber o de elegirse bien, y haría falta una recuperación selectiva.
- El enlace depende del orden de ingesta, así que el orden del piloto se fija y se declara.
