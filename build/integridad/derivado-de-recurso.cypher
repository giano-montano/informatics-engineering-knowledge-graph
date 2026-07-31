// regla: derivado-de-recurso  (dominio_rango)
// origen: :wasDerivedFrom rdfs:domain (Course u KnowledgeElement); rdfs:range :LearningResource
MATCH (a)-[:WAS_DERIVED_FROM]->(b)
WHERE NOT (a:Course OR a:KnowledgeElement) OR NOT (b:LearningResource)
RETURN 'derivado-de-recurso' AS regla, coalesce(a.iri, '<sin iri>') + ' -> ' + coalesce(b.iri, '<sin iri>') AS entidad, 'WAS_DERIVED_FROM entre (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') y (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detalle;
