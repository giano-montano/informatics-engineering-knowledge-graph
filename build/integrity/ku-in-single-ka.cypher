// rule: ku-in-single-ka  (functional_relationship)
// source: :knowledgeUnitInKnowledgeArea rdf:type owl:FunctionalProperty
MATCH (a:KnowledgeUnit)
OPTIONAL MATCH (a)-[:PART_OF]->(b:KnowledgeArea)
WITH a, count(DISTINCT b) AS targets
WHERE targets <> 1
RETURN 'ku-in-single-ka' AS rule, coalesce(a.iri, '<no iri>') AS entity, 'points to ' + toString(targets) + ' :KnowledgeArea via PART_OF' AS detail;
