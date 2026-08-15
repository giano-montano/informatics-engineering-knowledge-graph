// rule: concept-in-topic  (existential_relationship)
// source: :Concept rdfs:subClassOf [ owl:onProperty :conceptInTopic ; owl:someValuesFrom :Topic ]
MATCH (a:Concept)
WHERE NOT (a)-[:PART_OF]->(:Topic)
RETURN 'concept-in-topic' AS rule, coalesce(a.iri, '<no iri>') AS entity, 'is not part of any :Topic via PART_OF' AS detail;
