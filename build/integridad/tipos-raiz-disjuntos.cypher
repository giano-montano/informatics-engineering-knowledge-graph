// regla: tipos-raiz-disjuntos  (etiquetas_disjuntas)
// origen: AllDisjointClasses(Course, KnowledgeElement, LearningResource, ResourceType)
MATCH (n)
WITH n, [l IN labels(n) WHERE l IN ['Course', 'KnowledgeElement', 'LearningResource', 'ResourceType']] AS halladas
WHERE size(halladas) > 1
RETURN 'tipos-raiz-disjuntos' AS regla, coalesce(n.iri, '<sin iri>') AS entidad, 'debe tener a lo sumo una de (Course, KnowledgeElement, LearningResource, ResourceType), tiene: ' + reduce(acc = '', x IN halladas | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) AS detalle;
