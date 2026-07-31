// rule: part-of-dag  (acyclicity)
// source: :isPartOf rdf:type owl:TransitiveProperty; a transitive hierarchy with a cycle is incoherent
MATCH cycle = (n)-[:PART_OF*1..6]->(n)
RETURN 'part-of-dag' AS rule, coalesce(n.iri, '<no iri>') AS entity, 'PART_OF cycle of length ' + toString(length(cycle)) AS detail
LIMIT 25;
