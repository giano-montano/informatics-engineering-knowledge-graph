// rule: prerequisite-between-concepts  (domain_range)
// source: :hasPrerequisite rdfs:domain :Concept; rdfs:range :Concept
MATCH (a)-[:HAS_PREREQUISITE]->(b)
WHERE NOT (a:Concept) OR NOT (b:Concept)
RETURN 'prerequisite-between-concepts' AS rule, coalesce(a.iri, '<no iri>') + ' -> ' + coalesce(b.iri, '<no iri>') AS entity, 'HAS_PREREQUISITE between (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') and (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detail;
