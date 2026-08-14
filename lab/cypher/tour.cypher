// =========================================================================
//  Recorrido guiado del grafo, para pegar en el Neo4j Browser
//  (http://localhost:7474) o en Neo4j Desktop conectado a bolt://localhost:7687
//
//  Cada bloque es una consulta independiente, terminada en punto y coma.
//  Pega un bloque a la vez en el Browser y dale Ctrl+Enter. El archivo
//  entero también corre de un tirón con cypher-shell.
//
//  Comentarios en español a propósito: esto es material de aprendizaje del
//  laboratorio, no código del paquete. Ver docs/estandares-de-codigo.md.
// =========================================================================


// -------------------------------------------------------------------------
// 0. ¿Qué hay aquí? Censo por etiqueta.
//    Un nodo puede llevar VARIAS etiquetas, así que la suma da más que el
//    total de nodos: cada KnowledgeUnit cuenta también como KnowledgeElement.
// -------------------------------------------------------------------------
MATCH (n)
UNWIND labels(n) AS etiqueta
RETURN etiqueta, count(*) AS nodos
ORDER BY nodos DESC;


// -------------------------------------------------------------------------
// 1. Censo por tipo de arista.
// -------------------------------------------------------------------------
MATCH ()-[r]->()
RETURN type(r) AS tipo, count(*) AS aristas
ORDER BY aristas DESC;


// -------------------------------------------------------------------------
// 2. LA FOTO. El backbone entero: las 162 unidades colgando de sus 17 áreas.
//    `p=` captura el camino completo, y el Browser dibuja un camino como
//    nodos + arista. Si devolvieras sólo `ku, ka` verías nodos sueltos.
// -------------------------------------------------------------------------
MATCH p = (ku:KnowledgeUnit)-[:PART_OF]->(ka:KnowledgeArea)
RETURN p;


// -------------------------------------------------------------------------
// 3. El esquema que Neo4j INFIERE de los datos.
//    Ojo: no es tu T-box. Es el resumen de lo que hay cargado. No muestra
//    Concept, Topic ni Course porque todavía no existe ningún individuo de
//    esas clases, ni muestra disyunciones ni cardinalidades. La T-box
//    completa está en build/tbox.md.
// -------------------------------------------------------------------------
CALL db.schema.visualization();


// -------------------------------------------------------------------------
// 4. Las restricciones nativas que hay puestas.
//    Sólo unicidad sobre `iri`: es la única que sobrevive al pasar a
//    Community Edition (lab/findings/0001). Cada una crea un índice detrás.
// -------------------------------------------------------------------------
SHOW CONSTRAINTS;


// -------------------------------------------------------------------------
// 5. Una sola área con sus unidades. Cambia el prefLabel para explorar otras.
//    La flecha va de la unidad al área, y aquí se lee al revés (`<-`) sin
//    costo adicional. Eso es exactamente por qué no se guardan las inversas.
// -------------------------------------------------------------------------
MATCH p = (ka:KnowledgeArea {prefLabel: 'Artificial Intelligence'})<-[:PART_OF]-(ku:KnowledgeUnit)
RETURN p;


// -------------------------------------------------------------------------
// 6. Las áreas más grandes de CS2023, por número de unidades.
//    Primer agregado: `count` sobre el patrón, no sobre una tabla.
// -------------------------------------------------------------------------
MATCH (ka:KnowledgeArea)<-[:PART_OF]-(ku:KnowledgeUnit)
RETURN ka.prefLabel AS area, count(ku) AS unidades
ORDER BY unidades DESC, area;


// -------------------------------------------------------------------------
// 7. Lo mismo, pero incluyendo un área que no tuviera ninguna unidad.
//    `OPTIONAL MATCH` conserva la fila con cero. Con MATCH normal, un área
//    vacía DESAPARECE del resultado: la misma trampa que obligó a usarlo en
//    la regla de cardinalidad (ver el handoff, sección 8).
// -------------------------------------------------------------------------
MATCH (ka:KnowledgeArea)
OPTIONAL MATCH (ka)<-[:PART_OF]-(ku:KnowledgeUnit)
RETURN ka.prefLabel AS area, count(ku) AS unidades
ORDER BY unidades ASC, area
LIMIT 5;


// -------------------------------------------------------------------------
// 8. Buscar por texto. Devuelve las unidades cuya etiqueta menciona el término.
//    Sin índice de texto: con 162 nodos es irrelevante, con 100k no lo sería.
// -------------------------------------------------------------------------
MATCH (ku:KnowledgeUnit)
WHERE toLower(ku.prefLabel) CONTAINS 'machine'
MATCH (ku)-[:PART_OF]->(ka:KnowledgeArea)
RETURN ku.prefLabel AS unidad, ka.prefLabel AS area
ORDER BY area, unidad;


// -------------------------------------------------------------------------
// 9. Transitividad: se recorre, no se guarda.
//    El `*1..3` sube por PART_OF hasta 3 saltos. Hoy siempre encuentra el
//    área en 1 salto porque sólo hay dos niveles cargados. Cuando el pipeline
//    acuñe Topic y Concept, la MISMA consulta subirá 3 niveles sin cambiar.
//    Ese es el motivo de no materializar la clausura transitiva.
// -------------------------------------------------------------------------
MATCH (n:KnowledgeElement)-[:PART_OF*1..3]->(ka:KnowledgeArea)
RETURN labels(n) AS etiquetas, n.prefLabel AS elemento, ka.prefLabel AS area
ORDER BY area, elemento
LIMIT 20;


// -------------------------------------------------------------------------
// 10. Procedencia: de dónde salió cada cosa.
//     Los 179 elementos apuntan al documento CS2023. Esta arista es la que
//     hará auditable lo que el pipeline extraiga de cada sílabo.
// -------------------------------------------------------------------------
MATCH (n)-[:WAS_DERIVED_FROM]->(fuente:LearningResource)
RETURN fuente.prefLabel AS fuente, fuente.description AS referencia,
       count(n) AS elementos_derivados;


// -------------------------------------------------------------------------
// 11. Un nodo y todo su vecindario, en las dos direcciones.
//     La arista sin flecha `-[r]-` ignora el sentido: recorre para ambos
//     lados. Útil para inspeccionar. Caro si lo dejas suelto en un grafo
//     grande sin etiqueta.
// -------------------------------------------------------------------------
MATCH p = (ku:KnowledgeUnit {prefLabel: 'Machine Learning'})-[r]-(vecino)
RETURN p;


// -------------------------------------------------------------------------
// 12. Verificación visible del invariante: ninguna unidad puede quedar
//     huérfana ni colgar de dos áreas. Debe devolver CERO filas.
//     Es la versión legible de build/integrity/ku-in-single-ka.cypher.
// -------------------------------------------------------------------------
MATCH (ku:KnowledgeUnit)
OPTIONAL MATCH (ku)-[:PART_OF]->(ka:KnowledgeArea)
WITH ku, count(DISTINCT ka) AS areas
WHERE areas <> 1
RETURN ku.iri AS unidad, areas;


// -------------------------------------------------------------------------
// 13. Las etiquetas múltiples en acción: la subclase OWL se volvió una
//     etiqueta extra, no una tabla aparte ni una arista de tipo.
// -------------------------------------------------------------------------
MATCH (n:KnowledgeElement)
RETURN labels(n) AS juego_de_etiquetas, count(*) AS nodos
ORDER BY nodos DESC;


// -------------------------------------------------------------------------
// 14. Cómo se ve un nodo por dentro: propiedades crudas.
// -------------------------------------------------------------------------
MATCH (ka:KnowledgeArea {prefLabel: 'Data Management'})
RETURN ka.iri AS iri, ka.prefLabel AS etiqueta, ka.layer AS capa,
       properties(ka) AS todas_las_propiedades;
