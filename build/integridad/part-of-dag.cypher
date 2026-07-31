// regla: part-of-dag  (aciclicidad)
// origen: :isPartOf rdf:type owl:TransitiveProperty; una jerarquia transitiva con ciclo es incoherente
MATCH ciclo = (n)-[:PART_OF*1..6]->(n)
RETURN 'part-of-dag' AS regla, coalesce(n.iri, '<sin iri>') AS entidad, 'ciclo de PART_OF de longitud ' + toString(length(ciclo)) AS detalle
LIMIT 25;
