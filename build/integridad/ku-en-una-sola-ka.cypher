// regla: ku-en-una-sola-ka  (relacion_funcional)
// origen: :knowledgeUnitInKnowledgeArea rdf:type owl:FunctionalProperty
MATCH (a:KnowledgeUnit)
OPTIONAL MATCH (a)-[:PART_OF]->(b:KnowledgeArea)
WITH a, count(DISTINCT b) AS destinos
WHERE destinos <> 1
RETURN 'ku-en-una-sola-ka' AS regla, coalesce(a.iri, '<sin iri>') AS entidad, 'apunta a ' + toString(destinos) + ' :KnowledgeArea via PART_OF' AS detalle;
