// rule: unique-iri  (unique_key)
// source: owl:NamedIndividual identity; the IRI identifies the entity
MATCH (n:KnowledgeElement)
WITH n.iri AS key, count(*) AS occurrences
WHERE key IS NULL OR occurrences > 1
RETURN 'unique-iri' AS rule, coalesce(toString(key), '<null>') AS entity, ':KnowledgeElement with null or repeated iri ' + toString(occurrences) AS detail
UNION
MATCH (n:LearningResource)
WITH n.iri AS key, count(*) AS occurrences
WHERE key IS NULL OR occurrences > 1
RETURN 'unique-iri' AS rule, coalesce(toString(key), '<null>') AS entity, ':LearningResource with null or repeated iri ' + toString(occurrences) AS detail
UNION
MATCH (n:Course)
WITH n.iri AS key, count(*) AS occurrences
WHERE key IS NULL OR occurrences > 1
RETURN 'unique-iri' AS rule, coalesce(toString(key), '<null>') AS entity, ':Course with null or repeated iri ' + toString(occurrences) AS detail
UNION
MATCH (n:ResourceType)
WITH n.iri AS key, count(*) AS occurrences
WHERE key IS NULL OR occurrences > 1
RETURN 'unique-iri' AS rule, coalesce(toString(key), '<null>') AS entity, ':ResourceType with null or repeated iri ' + toString(occurrences) AS detail;
