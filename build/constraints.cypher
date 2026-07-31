// Native constraints. Uniqueness is the only one portable to
// Community Edition; see lab/findings/0001.

CREATE CONSTRAINT unique_iri_KnowledgeElement IF NOT EXISTS
FOR (n:KnowledgeElement) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT unique_iri_LearningResource IF NOT EXISTS
FOR (n:LearningResource) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT unique_iri_Course IF NOT EXISTS
FOR (n:Course) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT unique_iri_ResourceType IF NOT EXISTS
FOR (n:ResourceType) REQUIRE n.iri IS UNIQUE;
