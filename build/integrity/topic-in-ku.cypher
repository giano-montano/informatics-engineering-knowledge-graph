// rule: topic-in-ku  (existential_relationship)
// source: :Topic rdfs:subClassOf [ owl:onProperty :topicInKnowledgeUnit ; owl:someValuesFrom :KnowledgeUnit ]
MATCH (a:Topic)
WHERE NOT (a)-[:PART_OF]->(:KnowledgeUnit)
RETURN 'topic-in-ku' AS rule, coalesce(a.iri, '<no iri>') AS entity, 'is not part of any :KnowledgeUnit via PART_OF' AS detail;
