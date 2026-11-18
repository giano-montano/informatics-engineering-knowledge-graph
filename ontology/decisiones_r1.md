# **Decisiones de diseño de ontología de Ingeniería Informática**

## **DD-01 — Frontera entre T-Box y A-Box en la representación del dominio**

**Estado:** Validada por el asesor especialista.

**Contexto.** El modelo ontológico (R1) debe representar el dominio de la Ingeniería Informática integrando tres estándares internacionales (CS2023, SWEBOK, CC2020) y el plan de estudios de la PUCP. Estos estándares organizan el conocimiento en taxonomías jerárquicas (Knowledge Areas, Knowledge Units, temas) cuyo contenido concreto es extenso y susceptible de evolucionar entre versiones. Se requiere decidir qué elementos del dominio se representan como clases (T-Box, esquema conceptual) y cuáles como instancias (A-Box, aserciones sobre individuos). Esta frontera condiciona la expresividad lógica de la ontología, la eficiencia de su posterior materialización como grafo de propiedades etiquetado en Neo4j (R3, R4) y la estrategia de mantenimiento del sistema.

**Decisión.** Se adopta una T-Box minimalista que define únicamente el metamodelo educativo del dominio —las categorías estructurales y las relaciones entre ellas— y se relega el contenido taxonómico concreto de los estándares (Knowledge Areas, Knowledge Units y temas específicos) y del plan de estudios (cursos, recursos) al nivel de A-Box, como instancias de las clases del metamodelo. En consecuencia, son clases del esquema las categorías del metamodelo (por ejemplo, KnowledgeArea, KnowledgeUnit, Concept, Course, LearningResource; la lista definitiva se fijará tras el análisis del contenido de los estándares), y son instancias las entidades concretas del dominio (por ejemplo, "Software Engineering" como instancia de KnowledgeArea, "Software Design" como instancia de KnowledgeUnit, "Design Patterns" como instancia de Concept o Topic).

**Alternativa considerada.** Modelar la taxonomía concreta de los estándares como jerarquía de clases (por ejemplo, "Ingeniería de Software" como subclase de KnowledgeArea), de modo análogo a ontologías clásicas de clasificación como la ontología de vinos referida en Ontology Development 101 (Noy & McGuinness, 2001). Esta alternativa es legítima y resulta apropiada en ontologías cuyo propósito central es la clasificación inferida —donde el razonador asigna automáticamente individuos a categorías a partir de condiciones necesarias y suficientes definidas a nivel de clase— o que requieren axiomas de clase ricos. No corresponde, sin embargo, al propósito de este sistema.

**Justificación.** El propósito del sistema es la navegación y el descubrimiento de relaciones entre entidades concretas del dominio, no la clasificación inferida de categorías. Tres razones sustentan la decisión:

1. *Expresividad de las relaciones.* En OWL 2, las propiedades de objeto (como hasPrerrequisite o isPartOf) vinculan individuos, no clases. Representar las áreas de conocimiento y los conceptos como instancias permite expresar directamente las relaciones del dominio —incluida la inferencia transitiva de prerrequisitos conceptuales, núcleo del primer problema causa— sin recurrir a mecanismos de mayor complejidad como el *punning* de OWL 2\.  
2. *Eficiencia de la materialización en Neo4j.* La buena práctica en grafos de propiedades etiquetados establece que las etiquetas correspondan a categorías genéricas y estables, no a entidades concretas. Mapear cada área de conocimiento concreta a una clase produciría una proliferación de etiquetas específicas que degrada la indexación y las consultas de recorrido. Con la decisión adoptada, cada clase de la T-Box se mapea a una etiqueta genérica y las entidades concretas son nodos bajo esas etiquetas, lo que permite recorridos de relaciones limpios y eficientes.  
3. *Mantenibilidad frente a la evolución de los estándares.* Dado que los estándares se actualizan periódicamente, mantener su contenido como A-Box permite actualizar el dominio mediante la re-ingesta de instancias —proceso contemplado en el pipeline de R4— sin modificar el esquema conceptual ni la lógica del sistema. El esquema permanece estable mientras el contenido evoluciona.

**Consecuencias.**

* La T-Box resultante será deliberadamente reducida y estable; su valor reside en la precisión del metamodelo y de sus relaciones, no en el volumen de clases.  
* El contenido del dominio se concentra en la A-Box, poblada por el pipeline de ingesta automatizada (R4), lo que refuerza la separación de responsabilidades entre R1 (esquema, principalmente) y R4 (contenido).  
* La regla de prioridad entre estándares (CS2023 como base, SWEBOK para Ingeniería de Software, CC2020 para competencias) opera en el nivel de poblamiento de instancias, no en el diseño del esquema.  
* La definición concreta de las clases del metamodelo, sus propiedades y sus restricciones queda pendiente de los pasos posteriores de la metodología Ontology Development 101, una vez analizado el contenido de los estándares.

## **DD-02 — Separación entre capa de referencia y capa de contenido en la A-Box**

**Estado:** Validada por el asesor especialista.

**Contexto.** La decisión DD-01 estableció una T-Box minimalista y relegó el contenido del dominio a la A-Box. Resta definir cómo se organiza esa A-Box, dado que se nutre de dos fuentes de naturaleza distinta: los estándares internacionales (CS2023, SWEBOK, CC2020), que son autoritativos, finitos y estables, y los sílabos del plan de estudios de la PUCP entre otros materiales, que son específicos de la institución y se procesan de forma automatizada. Ambas fuentes no pueden tratarse del mismo modo ni en el mismo resultado del proyecto, pues difieren en su exigencia de fidelidad y en su mecanismo de poblamiento.

**Decisión.** Se organiza la A-Box en dos capas con orígenes, resultados y reglas de escritura diferenciados:

* *Capa de referencia (backbone).* Conjunto de instancias derivadas de los estándares internacionales —Knowledge Areas y Knowledge Units del eje temático, refinadas con SWEBOK en la rama de Ingeniería de Software, y la estructura de competencias de CC2020—. Se construye de forma curada y verificada como parte de R1, conforme al Paso 7 de la metodología Ontology Development 101\. Constituye un esqueleto autoritativo y estable del dominio.  
* *Capa de contenido institucional.* Conjunto de instancias derivadas del plan de estudios de la PUCP —cursos, conceptos enseñados, recursos académicos—. Se puebla de forma automatizada mediante el pipeline de ingesta (R4) y se enlaza a la capa de referencia.

El pipeline de ingesta no crea, modifica ni elimina nodos de la capa de referencia; únicamente crea instancias institucionales, las enlaza a los nodos del backbone y fusiona las entidades extraídas con los nodos de referencia cuando existe correspondencia, evitando duplicados.

**Alternativa considerada.** Procesar tanto los estándares como los sílabos a través de un único flujo de ingesta automatizada. Se descarta porque los estándares y los sílabos tienen estructuras documentales distintas, porque someter la capa autoritativa a extracción mediante modelos de lenguaje introduce riesgo de omisión y alucinación sobre la fuente de verdad del sistema, y porque diluiría el criterio de validación del pipeline al mezclar contenido curado con contenido extraído.

**Justificación.**

1. *Fundamento metodológico.* La metodología Ontology Development 101 incluye la creación de instancias como su Paso 7; las instancias del backbone son, por tanto, parte natural de R1 y no una ampliación de alcance.  
2. *Autoridad y trazabilidad.* Al curar y verificar el backbone contra los índices canónicos de los estándares, la estructura autoritativa del dominio es fiel y trazable, en lugar de depender de la salida de un modelo de lenguaje.  
3. *Pipeline y validación limpios.* El criterio de precisión de extracción de R4 aplica exclusivamente al contenido institucional, lo que define un objetivo de validación acotado y verificable.  
4. *Mantenibilidad.* El backbone se actualiza mediante recuración ante cambios de versión de los estándares; el contenido institucional se actualiza mediante re-ingesta. Cada capa evoluciona por su propio mecanismo sin afectar a la otra.

**Consecuencias.**

* R1 produce la T-Box y la capa de referencia (backbone); su resultado pasa de "modelo ontológico (T-Box)" a "modelo ontológico (T-Box y capa de referencia e la A-Box)".  
* R4 produce la capa de contenido institucional, enlazada a la capa de referencia.  
* El backbone se cura exclusivamente desde CS2023 hasta nivel KU (ver DD-04). SWEBOK queda como referencia de alineación y CC2020 como referencia fundacional (ver DD-03); ninguno de los dos es fuente de extracción del backbone.  
* El criterio de aceptación de ≥ 75% de precisión de R4 aplica a la extracción y el enlace del contenido institucional, no a la capa de referencia.  
* El uso de los estándares es proporcionado a su rol: CS2023 es la fuente única del backbone; SWEBOK es referencia de alineación para la rama de Ingeniería de Software; CC2020 es referencia fundacional del paradigma de competencias (extensión futura). Solo CS2023 se extrae.

## **DD-03 — Alcance de la ontología limitado al Modelo de Conocimiento**

**Estado:** Validada por el asesor especialista.

**Contexto.** CS2023 adopta una arquitectura bimodal (Knowledge Model y Competency Model) que el propio estándar declara como vistas complementarias y separables del mismo continuo de aprendizaje. El Competency Model aplica el paradigma de CC2020 (Conocimiento \+ Habilidades \+ Disposiciones en contexto de Tarea) y responde a la dimensión de desempeño; el Knowledge Model (KA, KU, Topic) responde a la dimensión de contenido. Se requiere decidir qué dimensión modela la ontología de esta tesis.

**Decisión.** La ontología se limita al Modelo de Conocimiento. El Modelo de Competencias queda fuera del alcance y se documenta como extensión futura.

**Alternativa considerada.** Incorporar el Modelo de Competencias completo (Tasks, Skills, Dispositions). Se descarta porque ninguno de los tres problemas causa pertenece a la dimensión de desempeño —todos viven en la capa de conocimiento— y porque el modelado de competencias es un subdominio de complejidad alta y tangencial a los objetivos.

**Justificación.** (1) Alineación con los problemas causas 1, 2 y 3: son todos de la capa de conocimiento. (2) Separabilidad declarada por el propio CS2023. (3) Proporcionalidad: la capa de competencias añadiría complejidad significativa sin resolver ningún problema causa.

**Consecuencias y edits consecuentes:**

* **DD-01:** la lista de clases de la T-Box pierde Competence. Queda: KnowledgeArea, KnowledgeUnit, Topic/Concept (nivel a definir en diseño detallado), Course, LearningResource.  
* **DD-02:** el backbone se cura solo como estructura del Modelo de Conocimiento (KA/KU); se elimina la capa de competencias.  
* **CC2020** deja de ser fuente de extracción del backbone y pasa a referencia fundacional (origen del paradigma de competencias que CS2023 adopta; base de la extensión futura). Se cita en el marco conceptual; no se extrae para el backbone.

## **DD-04 — Fuente y granularidad del backbone: CS2023 como fuente única, hasta nivel KU**

**Estado:** Validada por el asesor especialista.

**Contexto.** DD-02 estableció que el backbone se cura desde los estándares en R1 y enunció una regla de prioridad preliminar (CS2023 base, SWEBOK para SE, CC2020 para competencias). Resta decidir qué estándar alimenta efectivamente el backbone y hasta qué nivel de la taxonomía “KA, KU, Topic” llega la curación. La decisión está condicionada por dos hechos: (i) CS2023 representa la Ingeniería de Software como una Knowledge Area cuyas Knowledge Units —Requisitos, Diseño, Calidad/V\&V, Proceso, Modelado, gestión de proyectos— comparten estructura con SWEBOK y bastan para anclar los cursos de SE del plan de Ingeniería Informática PUCP; (ii) la profundidad distintiva de SWEBOK reside por debajo de la KU, en el nivel de Topic, que es el nivel que el material institucional PUCP poblará en R4 con el vocabulario que el estudiante reconoce de sus sílabos.

**Decisión.** El backbone se cura exclusivamente desde CS2023, hasta el nivel de Knowledge Unit. SWEBOK deja de ser fuente de extracción y pasa a referencia de alineación (citada en el marco conceptual como cuerpo de conocimiento análogo de orientación profesional; no se materializa ninguna alineación en la ontología). Las clases Topic y Concept existen en la T-Box, pero no se instancian desde los estándares: sus instancias provienen íntegramente del material institucional PUCP, pobladas por el pipeline en R4 y enlazadas hacia arriba a la KU del backbone.

**Alternativa considerada.** Refinar la rama de Ingeniería de Software del backbone con la estructura de SWEBOK (como anticipaba DD-02). Se descarta porque: la profundidad de SWEBOK no agrega anclas a nivel KA/KU que CS2023 no provea ya; esa profundidad opera en el nivel de Topic, donde competiría con —y desplazaría a— el vocabulario PUCP que constituye el valor de navegación del producto; SWEBOK está orientado a certificación profesional, no a educación de pregrado, lo que introduce un compromiso ontológico ajeno al resto del backbone; y curar dos índices canónicos con solapamientos duplica el esfuerzo de validación sin retorno trazable a ninguna Pregunta de Competencia.

**Justificación.**

1. *Trazabilidad.* Todo nodo del backbone (capa de referencia) traza a un único índice canónico (CS2023). Un nodo SWEBOK que ninguna PC ni curso PUCP activa incumple la convención de trazabilidad del proyecto.  
2. *Homogeneidad de procedencia y granularidad.* Una sola fuente evita una rama (SE) desproporcionadamente profunda y de autoridad distinta al resto del backbone.  
3. *Coherencia con la visión de producto.* El nivel Topic se reserva al vocabulario institucional PUCP, garantizando el match directo entre el grafo y los temas tal como los nombran los cursos.  
4. *Factibilidad para tesis-1.* La curación se acota a un índice canónico, dejando el trabajo fino para Protégé con HermiT y validación con experto.

**Consecuencias.**

* El backbone (A-Box de estándares) contiene instancias de KnowledgeArea y KnowledgeUnit, y ninguna de Topic o Concept.  
* Las instancias de Topic y Concept, y su enlace a la KU correspondiente, son producidas por R4 a partir del material PUCP; este enlace Topic/Concept con KnowledgeUnit es la junta sobre la que descansan PC1–PC5 y PC7.  
* SWEBOK se cita en el marco conceptual como referencia análoga que justifica su no uso; no se extrae ni se representa en la ontología.  
* Obliga a editar DD-02 (regla de prioridad) y a actualizar el entregable 3 de tesis (Fases 1 y 3, y sección de estándares).  
* El riesgo asociado —que el razonamiento concepto con concepto descanse en la extracción de R4, sin andamiaje de conceptos curado— se asume explícitamente y se acota mediante el umbral de precisión de R4.

## **DD-05 — Distinción entre Topic y Concept como clases separadas**

**Estado:** Validada por el asesor especialista.

**Contexto.** La T-Box debe representar el conocimiento por debajo de la Knowledge Unit. CS2023 ofrece "Topics" ilustrativos y el metamodelo de Barron distingue el nivel de tema del de detalle. Resta decidir si Topic y Concept son una única clase recursiva o dos clases distintas, y cuál es la frontera operativa entre ambas, dado que esa frontera la aplicará el pipeline de extracción en R4.

**Decisión.** Se modelan como dos clases disjuntas, subclases de KnowledgeElement. Topic es la agrupación de nivel sílabo —la unidad temática tal como la nombra un curso, p. ej. "Segmentación Semántica"—; Concept es el nodo atómico sobre el que opera el razonamiento de prerrequisitos. Frontera operativa para R4: si el material lo presenta como unidad, semana o encabezado de un sílabo, es Topic; si es un término del que otros dependen para ser comprendidos, es Concept.

**Alternativa considerada.** Una única clase recursiva (Topic con isPartOf hacia sí misma y Concept como hoja). Se descarta porque impide asertar propiedades y axiomas distintos por nivel, vuelve frágil la consulta ("dame conceptos" equivaldría a "dame hojas") y disuelve el nivel atómico de prerrequisito que requieren PC1, PC2 y PC6.

**Justificación.** (1) Las preguntas de prerrequisito operan sobre el nodo atómico; separar Concept lo hace explícito y consultable. (2) La navegación de producto distingue "el tema que veo en mi curso" (Topic) de "lo que debo entender" (Concept). (3) Permite reglas distintas de recursos y prerrequisitos por nivel.

**Consecuencias.** Topic y Concept son subclases disjuntas de KnowledgeElement. La identidad de instancias de Topic se resuelve en el poblamiento (R4), no en la T-Box. La frontera debe ser suficientemente operativa para que la extracción de R4 la aplique de forma consistente bajo su umbral de precisión. Resuelve el "(nivel a definir)" que DD-03 dejaba abierto.

## **DD-06 — Partonomía en capas: super-propiedad transitiva con sub-propiedades simples por nivel**

**Estado:** Validada por el asesor especialista. 

**Contexto.** La jerarquía “KA, KU, Topic, Concept” es partonomía entre instancias, no subsunción (consecuencia de DD-01). Resta decidir cómo modelar esa relación: una sola propiedad o varias. 

**Decisión.** Una super-propiedad transitiva isPartOf (sobre KnowledgeElement), que sostiene el recorrido y el roll-up, con tres sub-propiedades simples de nivel preciso —conceptInTopic, topicInKnowledgeUnit, knowledgeUnitInKnowledgeArea— como subPropertyOf de isPartOf. 

**Alternativa considerada.** Una única isPartOf transitiva con dominio/rango KnowledgeElement. Se descarta porque su rango genérico impide a HermiT detectar aristas de nivel equivocado. 

**Justificación.** (1) Validación: con rango preciso más clases disjuntas, una arista mal nivelada produce contradicción detectable. (2) Las sub-propiedades, simples, admiten cardinalidad y funcionalidad que la transitiva tiene prohibidas en OWL 2 DL. (3) La transitividad y el recorrido a cualquier nivel se preservan en la super-propiedad. 

**Consecuencias.** Consultas de contención usan isPartOf; la validación de niveles usa las sub-propiedades; knowledgeUnitInKnowledgeArea puede declararse **funcional**.

## **DD-07 — Lo que se afirma frente a lo que se deriva**

**Estado:** Validada por el asesor especialista. 

**Contexto.** Varias respuestas (prerrequisito de curso, área de un concepto, recursos de un tema) pueden almacenarse o derivarse por consulta. 

**Decisión.** Se afirman solo hechos atómicos e intrínsecos —hasPrerequisite únicamente entre conceptos, isAbout solo al nivel que el recurso aborda directamente, las relaciones curso↔concepto— y se derivan por consulta los agregados y cruces de nivel: prerrequisito conceptual entre cursos, área de un concepto, recursos relevantes por roll-up, prerrequisito a nivel tema/curso/área. No se almacenan cierres transitivos ni aristas agregadas. 

**Alternativa considerada.** Afirmar también prerrequisitos de curso/tema y aristas de recurso agregadas. Se descarta por duplicar información (riesgo de contradicción afirmado/derivado) y por obsolescencia: un agregado almacenado se desactualiza al cambiar la estructura subyacente. 

**Justificación.** Una sola fuente de verdad, consistencia automática ante cambios estructurales, menor carga de extracción. Implementa la convención de controlar la profundidad en las consultas. **Consecuencias.** isAbout y specializes no transitivas; roll-up y cierres en consulta; el razonamiento “concepto a concepto” descansa en la extracción de R4 (riesgo asumido, acotado por el umbral de precisión).

## **DD-08 — Relaciones admitidas entre conceptos y frontera R1/R4 para relaciones**

**Estado:** Validada por el asesor especialista. 

**Contexto.** Más allá del prerrequisito existen relaciones "es un tipo de" (especialización), "es parte de" (meronimia) y asociativas vagas ("relacionado con", con descripción libre). Resta decidir cuáles entran en la T-Box validada. 

**Decisión.** En R1 se admiten dos relaciones concepto-concepto: hasPrerequisite y specializes (taxonómica, propia, no transitiva, inversa hasSpecialization). Se descarta la meronimia concepto-concepto. La relación asociativa vaga con descripción se relega a R4 como arista del grafo de propiedades, fuera del razonamiento validado. 

**Alternativa considerada.** Incluir meronimia y/o una relatedTo con descripción en la T-Box. Se descarta porque la meronimia se confunde con la partonomía estructural; y la asociativa vaga no tiene contenido lógico para HermiT, exige reificar para colgarle la descripción y se extrae con baja precisión, contaminando la capa validada. Se aplica la distinción de representación: OWL para relaciones con peso inferencial; el grafo de propiedades (R4) para relaciones atribuidas y best-effort. 

**Justificación.** Mantener en R1 solo lo que aporta a la validación; la visión de "conexiones ocultas" se puede realizar en R4/R4 sin pretender ser verdad validada. specializes se modela propia, no SKOS, para no introducir la clase ajena skos:Concept. **Consecuencias.** Se añade pregunta de competencia N° 7 (especialización). El cierre de especialización se computa en consulta. R4 puede poblar una arista asociativa con **descripción**.

## **DD-09 — Procedencia y trazabilidad de la ingesta**

**Estado:** Validada por el asesor especialista. 

**Contexto.** Se requiere que toda instancia y afirmación institucional sea trazable a su origen. La procedencia no tiene contenido lógico. 

**Decisión.** Procedencia de **nodo** en R1, vía wasDerivedFrom (instancia institucional a recurso fuente; las del backbone trazan a CS2023). Procedencia **por arista** en R4, como propiedades de arista del grafo de propiedades. No se reifica en OWL. 

**Alternativa considerada.** Representar la procedencia por arista también en la T-Box. Se descarta porque OWL no admite atributos en una tripleta sin reificar (bloat, inercia o reestructuración n-aria) y porque ese metadato no tiene contenido lógico aprovechable por HermiT, mientras el grafo de propiedades (LPG) lo maneja nativo y consultable. 

**Justificación.** Cada representación hace lo suyo. La procedencia por arista vive solo en R4. **Consecuencias.** wasDerivedFrom se declara en la T-Box (objeto, no funcional).

**Ajuste (octubre de 2026).** La procedencia por arista se especifica en R3 como una sola propiedad: el documento del que se derivó la arista (capítulo 5, Tabla 17).

## **DD-10 — Estrategia de validación: HermiT para consistencia, consultas de integridad para completitud**

**Estado:** Validada por el asesor especialista. 

**Contexto.** OWL razona bajo mundo abierto; HermiT detecta contradicciones, no ausencias. Se requiere definir cómo se valida la ontología. 

**Decisión.** La validación formal de R1 es HermiT (consistencia lógica). La completitud e integridad —nodos huérfanos, recursos sin locator, instancias sin procedencia— se verifican mediante consultas de integridad en R4 (mundo cerrado). No se emplea SHACL. El invariante de cuatro niveles se declara como axiomas existenciales acompañados de una anotación que advierte que, bajo mundo abierto, no son *enforced* por OWL y se verifican en R4. 

**Alternativa considerada.** Validar la completitud con SHACL como capa formal de mundo cerrado. Se descarta por proporcionalidad para tesis-1 y por validación del asesor. 

**Justificación.** Cada régimen con su herramienta: consistencia lógica (HermiT), completitud (consultas), precisión de extracción (gold standard). Evita sobre-ingeniería. 

**Consecuencias.** Los axiomas existenciales afirman el invariante pero no detectan su violación; la detección vive en R4. SHACL queda como extensión futura posible.