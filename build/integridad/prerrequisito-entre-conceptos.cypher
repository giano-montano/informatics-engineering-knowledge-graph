// regla: prerrequisito-entre-conceptos  (dominio_rango)
// origen: :hasPrerequisite rdfs:domain :Concept; rdfs:range :Concept
MATCH (a)-[:HAS_PREREQUISITE]->(b)
WHERE NOT (a:Concept) OR NOT (b:Concept)
RETURN 'prerrequisito-entre-conceptos' AS regla, coalesce(a.iri, '<sin iri>') + ' -> ' + coalesce(b.iri, '<sin iri>') AS entidad, 'HAS_PREREQUISITE entre (' + reduce(acc = '', x IN labels(a) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ') y (' + reduce(acc = '', x IN labels(b) | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) + ')' AS detalle;
