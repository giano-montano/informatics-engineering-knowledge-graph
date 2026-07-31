// rule: part-of-pairs  (domain_range)
// source: rdfs:domain/rdfs:range of conceptInTopic, topicInKnowledgeUnit and knowledgeUnitInKnowledgeArea
MATCH (a)-[:PART_OF]->(b)
WHERE NOT ((a:Concept AND b:Topic) OR (a:Topic AND b:KnowledgeUnit) OR (a:KnowledgeUnit AND b:KnowledgeArea))
RETURN 'part-of-pairs' AS rule, coalesce(a.iri, '<no iri>') + ' -> ' + coalesce(b.iri, '<no iri>') AS entity, 'PART_OF between (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') and (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detail;
