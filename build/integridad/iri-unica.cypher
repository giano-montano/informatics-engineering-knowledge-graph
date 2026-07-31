// regla: iri-unica  (clave_unica)
// origen: identidad de owl:NamedIndividual; el IRI identifica la entidad
MATCH (n:KnowledgeElement)
WITH n.iri AS clave, count(*) AS repeticiones
WHERE clave IS NULL OR repeticiones > 1
RETURN 'iri-unica' AS regla, coalesce(toString(clave), '<null>') AS entidad, ':KnowledgeElement con iri nulo o repetido ' + toString(repeticiones) AS detalle
UNION
MATCH (n:LearningResource)
WITH n.iri AS clave, count(*) AS repeticiones
WHERE clave IS NULL OR repeticiones > 1
RETURN 'iri-unica' AS regla, coalesce(toString(clave), '<null>') AS entidad, ':LearningResource con iri nulo o repetido ' + toString(repeticiones) AS detalle
UNION
MATCH (n:Course)
WITH n.iri AS clave, count(*) AS repeticiones
WHERE clave IS NULL OR repeticiones > 1
RETURN 'iri-unica' AS regla, coalesce(toString(clave), '<null>') AS entidad, ':Course con iri nulo o repetido ' + toString(repeticiones) AS detalle
UNION
MATCH (n:ResourceType)
WITH n.iri AS clave, count(*) AS repeticiones
WHERE clave IS NULL OR repeticiones > 1
RETURN 'iri-unica' AS regla, coalesce(toString(clave), '<null>') AS entidad, ':ResourceType con iri nulo o repetido ' + toString(repeticiones) AS detalle;
