// rule: prerequisites-dag  (acyclicity)
// source: :hasPrerequisite rdf:type owl:TransitiveProperty; a prerequisite cycle is unsatisfiable
MATCH cycle = (n)-[:HAS_PREREQUISITE*1..15]->(n)
RETURN 'prerequisites-dag' AS rule, coalesce(n.iri, '<no iri>') AS entity, 'HAS_PREREQUISITE cycle of length ' + toString(length(cycle)) AS detail
LIMIT 25;
