// rule: ke-disjoint-subtypes  (disjoint_labels)
// source: :KnowledgeElement owl:disjointUnionOf (Concept KnowledgeArea KnowledgeUnit Topic)
MATCH (n:KnowledgeElement)
WITH n, [l IN labels(n) WHERE l IN ['Concept', 'KnowledgeArea', 'KnowledgeUnit', 'Topic']] AS found
WHERE size(found) <> 1
RETURN 'ke-disjoint-subtypes' AS rule, coalesce(n.iri, '<no iri>') AS entity, 'must have exactly one of (Concept, KnowledgeArea, KnowledgeUnit, Topic), has: ' + reduce(acc = '', x IN found | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) AS detail;
