// rule: derived-from-resource  (domain_range)
// source: :wasDerivedFrom rdfs:domain (Course u KnowledgeElement); rdfs:range :LearningResource
MATCH (a)-[:WAS_DERIVED_FROM]->(b)
WHERE NOT (a:Course OR a:KnowledgeElement) OR NOT (b:LearningResource)
RETURN 'derived-from-resource' AS rule, coalesce(a.iri, '<no iri>') + ' -> ' + coalesce(b.iri, '<no iri>') AS entity, 'WAS_DERIVED_FROM between (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') and (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detail;
