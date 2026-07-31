// regla: prerrequisitos-dag  (aciclicidad)
// origen: :hasPrerequisite rdf:type owl:TransitiveProperty; un ciclo de prerrequisitos es insatisfacible
MATCH ciclo = (n)-[:HAS_PREREQUISITE*1..15]->(n)
RETURN 'prerrequisitos-dag' AS regla, coalesce(n.iri, '<sin iri>') AS entidad, 'ciclo de HAS_PREREQUISITE de longitud ' + toString(length(ciclo)) AS detalle
LIMIT 25;
