// regla: part-of-pares  (dominio_rango)
// origen: rdfs:domain/rdfs:range de conceptInTopic, topicInKnowledgeUnit y knowledgeUnitInKnowledgeArea
MATCH (a)-[:PART_OF]->(b)
WHERE NOT ((a:Concept AND b:Topic) OR (a:Topic AND b:KnowledgeUnit) OR (a:KnowledgeUnit AND b:KnowledgeArea))
RETURN 'part-of-pares' AS regla, coalesce(a.iri, '<sin iri>') + ' -> ' + coalesce(b.iri, '<sin iri>') AS entidad, 'PART_OF entre (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') y (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detalle;
