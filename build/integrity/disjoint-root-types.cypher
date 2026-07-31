// rule: disjoint-root-types  (disjoint_labels)
// source: AllDisjointClasses(Course, KnowledgeElement, LearningResource, ResourceType)
MATCH (n)
WITH n, [l IN labels(n) WHERE l IN ['Course', 'KnowledgeElement', 'LearningResource', 'ResourceType']] AS found
WHERE size(found) > 1
RETURN 'disjoint-root-types' AS rule, coalesce(n.iri, '<no iri>') AS entity, 'must have at most one of (Course, KnowledgeElement, LearningResource, ResourceType), has: ' + reduce(acc = '', x IN found | acc + CASE WHEN acc = '' THEN '' ELSE ', ' END + x) AS detail;
