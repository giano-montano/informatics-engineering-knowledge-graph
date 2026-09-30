# **Transición del modelo ontológico al grafo de propiedades**

Neo4j no ejecuta un razonador, así que cada constructo de la ontología llega al grafo de propiedades como una estructura del grafo o como una regla que el sistema impide violar y luego comprueba. La Tabla 1 y la Tabla 2 dicen qué pasa con cada constructo; la Tabla 3 enuncia las diez reglas de integridad y el mecanismo que impide violar cada una.

El anexo cubre solo lo que exige traducir entre OWL y el grafo de propiedades. Las condiciones que nacen de decisiones propias del módulo van al capítulo de arquitectura.

## **Términos**

Cada término conserva en todo el anexo el significado que le da esta tabla.

| Término | Significado |
| ----- | ----- |
| Constructo del modelo ontológico | Cada pieza del lenguaje OWL que el TTL usa para describir el dominio. Unas declaran un nombre: una clase, una propiedad o un individuo. Otras, los axiomas, afirman algo sobre esos nombres: que una clase es subclase de otra, que dos clases son disjuntas, que una propiedad es transitiva. |
| Base de datos de grafos | La instancia de Neo4j Community del sistema: una sola base de datos, consultada con Cypher 5\. |
| Clave | La única propiedad de identidad de un nodo. Vale el IRI en la capa de referencia y un uuid, acuñado al crear el nodo, en la capa institucional. |
| Carga del backbone | La corrida que lee el TTL del backbone y escribe la capa de referencia sobre una base de datos de grafos vacía. Es destructiva y precede a toda ingesta. |
| Ingesta | El procesamiento de un documento institucional que termina escribiendo en la base de datos de grafos. |
| Lote de ingesta | Los hechos candidatos que se validan y se escriben juntos: si uno falla, no se escribe ninguno. |
| Validación previa a la escritura | Las comprobaciones sobre lo que se va a escribir, antes de escribirlo. Puede leer la base de datos de grafos; no escribe en ella. |
| Hacer commit | Dejar firme la transacción de escritura. |
| Auditoría | La corrida de las consultas Cypher de integridad sobre el grafo completo. Cada consulta lleva el código de la regla que comprueba. |
| Reproyección | Vaciar la base de datos de grafos, repetir la carga del backbone desde el TTL versionado y reaplicar los hechos institucionales del almacén versionado, sin invocar al modelo de lenguaje. |
| Reaplicación | El paso de la reproyección que copia a la base de datos de grafos los hechos institucionales guardados. |
| Tipo de arista | Uno de los ocho tipos de relación del grafo, listados en la Tabla 2\. |

Las etiquetas de Neo4j conservan el nombre en inglés de cada clase: elemento de conocimiento (KnowledgeElement), área de conocimiento (KnowledgeArea), unidad de conocimiento (KnowledgeUnit), tema (Topic), concepto (Concept), curso (Course), recurso de aprendizaje (LearningResource) y tipo de recurso (ResourceType).

## **Correspondencia de constructos**

Todo constructo que aparece en el TTL de la T-Box o en el del backbone tiene una fila. La columna «En Neo4j» nombra un elemento solo cuando existe en el grafo; un axioma no tiene representación propia y sobrevive como regla de la Tabla 3\.

**Tabla 1\.** Correspondencia entre los constructos del modelo ontológico y el grafo de propiedades

| Constructo | En la ontología | En Neo4j | Qué no se almacena y dónde queda | Reglas |
| ----- | ----- | ----- | ----- | ----- |
| Cabecera e importación | Cada TTL se declara ontología. La T-Box importa el backbone y comenta la advertencia de mundo abierto | Sin representación propia | Se consume en la carga del backbone; el comentario queda en el TTL versionado | — |
| Declaración de entidad | Cada clase, propiedad e individuo se declara con su tipo de entidad | Sin representación propia: ningún nodo representa una clase o una propiedad | Las declaraciones fijan qué etiquetas, tipos de arista y propiedades admite el grafo | RI-02, RI-04, RI-09 |
| Individuo nombrado | En el backbone, 180 individuos con IRI: 17 áreas, 162 unidades y el recurso de aprendizaje CS2023 | Un nodo con su clave | El IRI deja de ser la identidad del individuo y pasa a ser el valor de la clave | RI-01 |
| Individuos distintos | owl:AllDifferent sobre las 179 áreas y unidades, que anula el supuesto de nombres no únicos | Sin representación propia | No se proyecta: con la clave única, dos nodos con claves distintas son siempre nodos distintos | RI-01 |
| Clase | Ocho clases con nombre | Una etiqueta con el nombre de la clase | — | RI-02 |
| Subsunción | Área, unidad, tema y concepto son subclases de elemento de conocimiento | Una segunda etiqueta, la de la superclase | El razonador infería la superclase; el grafo la escribe | RI-02 |
| Unión disjunta y disyunción | Elemento de conocimiento es la unión disjunta de sus cuatro subclases. Dos axiomas más declaran disjuntas esas cuatro subclases, y también KnowledgeElement, Course, LearningResource y ResourceType | Sin representación propia | El axioma no viaja. HermiT lo comprobó sobre el backbone en R2 | RI-03 |
| Unión de clases | Curso ⊔ elemento de conocimiento, escrita sin nombre propio (clase anónima): dominio de wasDerivedFrom y hasResource, rango de isAbout | Sin representación propia | Se expande en cinco pares de etiquetas por cada tipo de arista afectado (Tabla 2\) | RI-05 |
| Propiedad de objeto afirmada | Once propiedades en la dirección que fija R1 | Un tipo de arista en esa dirección (Tabla 2\) | Nada se pierde | RI-04, RI-06 |
| Propiedad inversa | Seis propiedades, cada una inversa de una afirmada | Sin representación propia | No se materializa: se consulta recorriendo la arista afirmada en sentido contrario | RI-04 |
| Subpropiedad de partonomía | conceptInTopic, topicInKnowledgeUnit y knowledgeUnitInKnowledgeArea, bajo la superpropiedad isPartOf | Las cuatro propiedades se proyectan en un solo tipo de arista | La subpropiedad de cada arista no se guarda: se recupera del par de etiquetas, porque cada par admitido corresponde a una sola subpropiedad | RI-05 |
| Subpropiedad de owl:topObjectProperty | Siete propiedades figuran como subpropiedades de owl:topObjectProperty, la propiedad que relaciona todo individuo con todo otro. Protégé agrega ese axioma, que no dice nada del dominio | Sin representación propia | Se descarta sin proyectar. Solo la partonomía colapsa sus subpropiedades en un tipo de arista | — |
| Propiedad transitiva | isPartOf, hasPart, hasPrerequisite e isPrerequisiteFor | Sin representación propia | El cierre no se materializa (R1, DD-07): lo deriva un recorrido de longitud variable. Como un camino no repite aristas, el recorrido termina aun con ciclos y alcanza el mismo conjunto que el cierre de OWL. Enumera caminos, no nodos: la consulta pide nodos distintos, y su tiempo es lo que mide AC-05 | — |
| Propiedad funcional | knowledgeUnitInKnowledgeArea | Sin representación propia | El axioma no viaja. HermiT lo comprobó sobre el backbone en R2, junto con la declaración de individuos distintos | RI-07 |
| Dominio y rango | Declarados en dieciséis de las diecisiete propiedades de objeto; hasPart no los declara | Sin representación propia | En OWL infieren el tipo de los extremos; en el grafo, un extremo de otra etiqueta es violación y no inferencia | RI-05 |
| Restricción existencial | Tres axiomas de subclase, uno por cada nivel bajo el área: concepto, tema y unidad | Sin representación propia | Bajo mundo abierto HermiT la asumía verdadera sin comprobarla; el comentario de cabecera de la T-Box lo advierte | RI-08 |
| Propiedad de datos | resourceLocator, con rango xsd:anyURI | Una propiedad de cadena en el nodo del recurso de aprendizaje | El tipo de dato del literal no se conserva. El grafo exige la forma http o https, más estricta que un rango que admite casi cualquier cadena | RI-09, RI-10 |
| Propiedad de anotación | layer, la única que declara la T-Box | Una propiedad de cadena en el nodo | — | RI-09 |
| Anotaciones de otros vocabularios | skos:prefLabel (SKOS) y dcterms:description (Dublin Core), que el backbone usa sin que la T-Box las declare | Una propiedad de cadena en el nodo | Se declaran como decisión de proyección, sin modificar R1 | RI-09 |
| Etiqueta de idioma | La etiqueta preferida del backbone lleva un literal en español y otro en inglés | Una propiedad por idioma: etiqueta española y etiqueta inglesa | El idioma deja de ser metadato del literal y pasa al nombre de la propiedad | RI-09 |

**Notas de la Tabla 1**

* El grafo es más estricto que la ontología en tres puntos. La clave única vuelve redundante la declaración de individuos distintos. La partonomía solo admite los tres pares de etiquetas de la Tabla 2, mientras que OWL acepta afirmar isPartOf entre dos elementos de conocimiento cualesquiera, incluso en sentido inverso. Y el localizador exige una forma que su rango no exige.  
* Un constructo del TTL sin fila en la Tabla 1 no se proyecta en silencio: la carga del backbone lo rechaza.  
* Lo que el TTL no contiene se fija como decisión de proyección: la propiedad afirmada de cada par inverso y el nombre de su tipo de arista (Tabla 2), el colapso de la partonomía, una propiedad por idioma y las anotaciones de otros vocabularios.  
* El grafo añade una propiedad de arista sin constructo de origen: la procedencia por arista, que R1 (DD-09) ubica fuera de OWL.  
* Fuera de alcance: los constructos de OWL 2 que la ontología no usa, como cadenas de propiedades, nominales, negación, cardinalidades distintas de la existencial y equivalencia declarada con owl:equivalentClass.

  ## **Tipos de arista**

Las once propiedades afirmadas se proyectan en ocho tipos de arista, porque las cuatro de partonomía se colapsan en uno. Cada arista va en la dirección de la propiedad afirmada, que el TTL no registra y la Tabla 2 fija.

**Tabla 2\.** Tipos de arista, propiedad de origen y pares de etiquetas admitidos

| Tipo de arista | Propiedad afirmada | Inversa no materializada | Pares admitidos (origen → destino) | La escribe |
| ----- | ----- | ----- | ----- | ----- |
| PART\_OF | isPartOf, mediante conceptInTopic, topicInKnowledgeUnit y knowledgeUnitInKnowledgeArea | hasPart | Concept → Topic; Topic → KnowledgeUnit; KnowledgeUnit → KnowledgeArea | La ingesta, los dos primeros pares; la carga del backbone, el tercero |
| HAS\_PREREQUISITE | hasPrerequisite | isPrerequisiteFor | Concept → Concept | La ingesta |
| SPECIALIZES | specializes | hasSpecialization | Concept → Concept | La ingesta |
| TEACHES\_CONCEPT | teachesConcept | conceptTaughtBy | Course → Concept | La ingesta |
| REQUIRES\_CONCEPT | requiresConcept | conceptRequiredBy | Course → Concept | La ingesta |
| IS\_ABOUT | isAbout | hasResource | LearningResource → KnowledgeArea, KnowledgeUnit, Topic, Concept o Course | La ingesta |
| HAS\_RESOURCE\_TYPE | hasResourceType | — | LearningResource → ResourceType | La ingesta |
| WAS\_DERIVED\_FROM | wasDerivedFrom | — | KnowledgeArea, KnowledgeUnit, Topic, Concept o Course → LearningResource | La carga del backbone, hacia CS2023; la ingesta |

Toda arista que escribe la ingesta sale de un nodo institucional, y ninguna dirección afirmada obliga a salir de un nodo de referencia. Por eso la condición de frontera de capas no necesita excepciones.

## **Reglas de integridad**

Diez reglas describen condiciones sobre el contenido del grafo, y la auditoría comprueba cada una con una consulta que lleva el código de la regla. Las dos últimas columnas dicen cómo se garantiza cada regla en la carga del backbone y en la ingesta.

Valores de las columnas «Carga del backbone» e «Ingesta»: se impide al escribir, cuando la violación nunca llega a hacerse commit, porque se rechaza antes de escribir o porque la escritura misma la impide; validado en R2, cuando HermiT comprobó el TTL, lo que garantiza la fuente y no su proyección; se detecta en la auditoría, cuando nada lo impide; no aplica, con su motivo. El mecanismo concreto que impide cada regla lo decide el capítulo de arquitectura.

**Tabla 3\.** Reglas de integridad del grafo y mecanismos que las impiden

| Código | Regla | Origen | Carga del backbone | Ingesta |
| ----- | ----- | ----- | ----- | ----- |
| RI-01 | Todo nodo tiene clave no nula, y no hay dos nodos con la misma clave | Individuo nombrado; individuos distintos | Se impide al escribir | Se impide al escribir |
| RI-02 | Todo nodo lleva la etiqueta de su clase; los nodos KnowledgeArea, KnowledgeUnit, Topic y Concept llevan además la etiqueta KnowledgeElement | Clase; subsunción | Se impide al escribir | Se impide al escribir |
| RI-03 | Todo nodo lleva exactamente una de las etiquetas KnowledgeElement, Course, LearningResource y ResourceType, y todo nodo KnowledgeElement exactamente una de KnowledgeArea, KnowledgeUnit, Topic y Concept | Unión disjunta y disyunción | Validado en R2 que no haya dos. Se impide al escribir que no haya ninguna, algo que HermiT no detecta bajo mundo abierto | Se impide al escribir |
| RI-04 | Toda arista es de uno de los ocho tipos de la Tabla 2 | Propiedad afirmada; propiedad inversa | Se impide al escribir | Se impide al escribir |
| RI-05 | Cada arista une un par de etiquetas admitido para su tipo en la Tabla 2, en la dirección de la propiedad afirmada | Dominio y rango; subpropiedad de partonomía; unión de clases | Validado en R2. Se impide al escribir, porque R2 no cubre los errores de la proyección | Se impide al escribir |
| RI-06 | Entre dos nodos hay como máximo una arista de cada tipo en cada dirección | Propiedad afirmada: en RDF un triple está afirmado o no, y el grafo de propiedades admite aristas paralelas | Se impide al escribir | Se impide al escribir |
| RI-07 | Ninguna unidad tiene aristas de partonomía hacia más de un área | Propiedad funcional | Validado en R2 | No aplica: la condición de frontera de capas impide a la ingesta escribir aristas de unidad a área |
| RI-08 | Todo concepto tiene al menos una arista de partonomía hacia un tema; todo tema, hacia una unidad; toda unidad, hacia un área | Restricción existencial | Se detecta en la auditoría: HermiT no detecta ausencias bajo mundo abierto | Se impide al escribir |
| RI-09 | Todo nodo y toda arista tiene solo propiedades declaradas en la Tabla 1 o en sus notas | Propiedad de datos; propiedad de anotación; etiqueta de idioma | Se impide al escribir | Se impide al escribir |
| RI-10 | Si un recurso de aprendizaje tiene localizador, su valor es un URI absoluto con esquema http o https | Propiedad de datos | Se impide al escribir | Se impide al escribir |

**Notas de la Tabla 3**

* La partonomía no necesita regla de ciclos. Sus únicos pares admitidos son concepto → tema, tema → unidad y unidad → área, así que todo camino de partonomía avanza hacia el área y nunca vuelve a un nodo por el que ya pasó.  
* Impedir RI-05 y RI-08 en la ingesta exige consultar nodos que ya están en el grafo, y eso solo es fiable con un único escritor (condición 1).  
* RI-08 descansa en la escritura acumulativa: un nodo ya anclado no pierde su arista de partonomía, así que solo los nodos nuevos necesitan traer la suya.  
* La reaplicación no tiene columna propia: copia hechos que ya cumplieron las reglas al escribirse, y la auditoría corre al cierre de la reproyección.

  ## **Condiciones del proceso de escritura**

Las condiciones de esta sección no describen el contenido del grafo y no tienen consulta de auditoría, pero varias celdas de la Tabla 3 las suponen.

1. **Escritores.** Solo escriben en la base de datos de grafos la carga del backbone, la ingesta y la reaplicación, nunca dos a la vez. Ningún otro componente del sistema escribe en ella, y el anexo no cubre escrituras hechas por fuera del sistema.  
2. **Escrituras de forma fija.** Toda escritura tiene una forma fija, definida por el sistema, que solo recibe valores; ninguna se arma a partir de texto del modelo de lenguaje.  
3. **Escrituras comprobadas.** Una escritura que no produce lo esperado detiene la corrida en lugar de pasar en silencio. Por ejemplo, una arista cuyo extremo no existe no puede quedar sin escribir y sin aviso.  
4. **Escritura acumulativa.** La ingesta no borra nodos, aristas ni propiedades. Un documento que se vuelve a ingestar se trata como cualquier otro.  
5. **Procedencia única.** La procedencia de un nodo y la de una arista se fijan al crearlos. Si un documento posterior afirma algo que ya existe, se conserva la procedencia existente.  
6. **Frontera de capas.** La ingesta no crea ni modifica nodos ni aristas de la capa de referencia, y toda arista que escribe sale de un nodo institucional. RI-07 depende de esta condición.  
7. **Todo o nada por lote de ingesta.** Si una regla falla en la validación previa a la escritura, no se escribe nada del lote de ingesta.  
8. **Carga destructiva.** La carga del backbone parte de una base de datos de grafos vacía. Lo que no proviene del TTL y debe persistir se reaplica desde el almacén versionado, en un paso posterior y separado.  
9. **Alcance de la reproyección.** Cubre correcciones del backbone que no cambian claves, como etiquetas o descripciones, cambios en el código de proyección y constructos que solo existen en el grafo. No cubre cambios de clave, fusiones o eliminaciones de unidades ni cambios de la T-Box: después de ellos los hechos guardados ya no encajan en el modelo y deben transformarse con un script escrito para ese cambio. Criterio: si todo hecho guardado apunta a claves que existen y cumple las reglas de integridad, basta la reproyección.  
10. **Reaplicación.** El almacén versionado guarda los hechos que cada corrida escribió, con sus claves resueltas y su procedencia ya fijada. La reaplicación los copia sin recalcular nada, en el orden original de las corridas, porque cada corrida solo referencia nodos que existían antes de ella.  
11. **Auditoría y recuperación.** La auditoría corre al cierre de la carga del backbone, de cada corrida de ingesta y de la reproyección. En la ingesta todas las reglas se impiden al escribir, así que una violación que la auditoría encuentra tras una ingesta revela un error de código y no un dato malo. En la ingesta se hace commit, se persisten los hechos en el almacén versionado y luego corre la auditoría; si encuentra violaciones, emite su reporte, detiene la ingesta y deja la decisión al operador. La reproyección es el remedio disponible, no una reacción automática.

    ## **Alternativas descartadas**

Cada ausencia de un mecanismo o de un constructo en las tablas anteriores es una decisión registrada aquí, no un olvido.

**Tabla 4\.** Alternativas descartadas en la transición al grafo de propiedades

| Alternativa | Motivo |
| ----- | ----- |
| Restricciones de existencia, tipo y clave de Neo4j | Exclusivas de la edición Enterprise |
| Graph types de GQL | No disponibles en Neo4j Community con Cypher 5 |
| Disparadores de APOC | Vienen desactivados, se instalan desde la base de datos system, se propagan con un refresco de 60 s por defecto y Neo4j los excluye del subconjunto de APOC que ofrece en Aura. Su única ventaja propia, frenar escrituras hechas fuera del código, cubre un escritor que la condición de escritores ya excluye |
| Comprobación dentro de la transacción antes de hacer commit | Redundante: las reglas ya se impiden al escribir y la auditoría cubre los errores de implementación |
| Etiqueta común inventada para todos los nodos, con unicidad global | Ruido: con IRI en la capa de referencia y uuid acuñado al crear en la institucional, la colisión de clave entre etiquetas es imposible por construcción |
| Uuid también en la capa de referencia | Cada carga destructiva cambiaría esos uuid, y todo lo guardado fuera de la base de datos de grafos tendría que usar el IRI: dos formas de referirse a un mismo nodo |
| Materializar las aristas inversas o el cierre transitivo | Duplica información y se desactualiza al cambiar la estructura; R1 (DD-07) fija derivarlos en consulta |
| Deducir del TTL la dirección afirmada de cada par inverso | OWL no distingue una dirección afirmada, porque la inversa es simétrica, y el editor escribe el axioma bajo el nombre que va primero en orden alfabético. La Tabla 2 fija la dirección |
| Poblar en el piloto la relación asociativa de DD-08 | R1 la permite sin exigirla. Omitirla acota la extracción del modelo de lenguaje y deja cerrados los ocho tipos de arista |
| Varias procedencias por nodo o por arista | La procedencia registra el primer documento que afirmó el hecho; un documento posterior que lo repite no agrega un hecho nuevo al grafo |

## **Reglas que van al capítulo de arquitectura**

Cinco condiciones sobre el contenido del grafo no nacen de traducir OWL al grafo de propiedades, sino de decisiones del módulo. Se enuncian en el capítulo de arquitectura con su propio código. El reporte de integridad de RF-09 es uno solo y cubre las diez reglas de este anexo y las cinco condiciones de esta sección.

* Todo nodo tiene marca de capa, con valor reference o institutional (R1, DD-02).  
* Ninguna arista sale de un nodo de la capa de referencia hacia uno de la capa institucional (R1, DD-02). Es la forma consultable de la condición de frontera de capas.  
* Todo tema, concepto y curso institucional tiene al menos una arista de procedencia hacia un recurso de aprendizaje, y toda arista que escribe la ingesta lleva su procedencia (R1, DD-09).  
* No existen ciclos de prerrequisito ni de especialización. La transitividad no los prohíbe; los exige el orden topológico de la navegación (R5 y R6).  
* Todo recurso de aprendizaje tiene localizador (R1, DD-10).

AC-03 comprueba la procedencia y AC-04 la frontera de capas.