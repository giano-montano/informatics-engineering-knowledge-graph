// Restricciones nativas. Unicidad es la unica portable a
// Community Edition; ver lab/findings/0001.

CREATE CONSTRAINT iri_unica_KnowledgeElement IF NOT EXISTS
FOR (n:KnowledgeElement) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT iri_unica_LearningResource IF NOT EXISTS
FOR (n:LearningResource) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT iri_unica_Course IF NOT EXISTS
FOR (n:Course) REQUIRE n.iri IS UNIQUE;
CREATE CONSTRAINT iri_unica_ResourceType IF NOT EXISTS
FOR (n:ResourceType) REQUIRE n.iri IS UNIQUE;
