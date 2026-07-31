// regla: ke-subtipos-disjuntos  (etiquetas_disjuntas)
// origen: :KnowledgeElement owl:disjointUnionOf (Concept KnowledgeArea KnowledgeUnit Topic)
MATCH (n:KnowledgeElement)
WITH n, [l IN labels(n) WHERE l IN ['Concept', 'KnowledgeArea', 'KnowledgeUnit', 'Topic']] AS halladas
WHERE size(halladas) <> 1
RETURN 'ke-subtipos-disjuntos' AS regla, coalesce(n.iri, '<sin iri>') AS entidad, 'debe tener exactamente una de (Concept, KnowledgeArea, KnowledgeUnit, Topic), tiene: ' + reduce(acc = '', x IN halladas | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) AS detalle;
