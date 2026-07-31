**PONTIFICIA UNIVERSIDAD CATÓLICA DEL PERÚ**  
**FACULTAD DE CIENCIAS E INGENIERÍA**  
![A blue circle with white text and a ship in the waterDescription automatically generated][image1]

**Diseño e implementación de un sistema de gestión de conocimiento (KMS) basado en grafos de conocimiento para la navegación y descubrimiento de recursos de Ingeniería Informática**

**Tesis para obtener el título profesional de Ingeniero Informático**  
**AUTOR:**  
Giano Sebastian Montaño Cruz  
**ASESORES:**  
Dr. Héctor Andrés Melgar, Mag. Eder Quispe

**Lima, Junio, 2026**

# **Resumen**

(NO NECESARIO EN LOS CURSOS DE TESIS)

- La extensión debe ser de 200 a 300 palabras, sin exceder a una página.  
- Escriba en tiempo verbal presente  
- El resumen debe contener información sobre:  
* La justificación de la investigación  
* Los objetivos o hipótesis  
* La teoría o supuestos teóricos o metodológicos en la que se sustenta  
* El método o procedimiento realizado (de ser necesario)  
* Los resultados (de ser necesario)  
* La conclusión principal

# **Tema FCI**

Aquí se debe colocar una copia del tema aprobado por el Decano de la FCI. No es necesario colocarlo durante los cursos de tesis.

# **Tabla de Contenido**

[**Capítulo 1\. Generalidades	7**](#generalidades)

[1.1 Problemática	7](#problemática)

[1.1.1 Árbol de Problemas	9](#árbol-de-problemas)

[1.1.2 Descripción	10](#descripción)

[1.1.3 Problema seleccionado	18](#problema-seleccionado)

[1.2 Objetivos	18](#objetivos)

[1.2.1 Objetivo general	18](#objetivo-general)

[1.2.2 Objetivos específicos	19](#objetivos-específicos)

[1.2.3 Resultados esperados y mapeo de verificación	19](#resultados-esperados-y-mapeo-de-verificación)

[1.3 Métodos, procedimientos y herramientas	24](#métodos,-procedimientos-y-herramientas)

[1.3.1 Métodos y procedimientos	25](#métodos-y-procedimientos)

[1.3.1.1 Procedimiento para el modelado ontológico \- R1	25](#procedimiento-para-el-modelado-ontológico---r1)

[1.3.1.2 Procedimiento para la instanciación en capa de referencia \- R2	27](#procedimiento-para-la-instanciación-en-capa-de-referencia---r2)

[1.3.1.3 Procedimiento para la documentación del módulo del grafo de conocimiento \- R3	27](#procedimiento-para-la-documentación-del-módulo-del-grafo-de-conocimiento---r3)

[1.3.1.4 Procedimiento para la construcción del módulo de KG y pipeline \- R4	30](#procedimiento-para-la-construcción-del-módulo-de-kg-y-pipeline---r4)

[1.3.1.5 Procedimiento para la documentación del mecanismo de navegación \- R5	31](#procedimiento-para-la-documentación-del-mecanismo-de-navegación---r5)

[1.3.1.6 Procedimiento para el prototipo de navegación \- R6	32](#procedimiento-para-el-prototipo-de-navegación---r6)

[1.3.2 Herramientas	33](#herramientas)

[1.3.2.1 Base de datos orientada a grafos: Neo4j y Cypher	33](#base-de-datos-orientada-a-grafos:-neo4j-y-cypher)

[1.3.2.2 Lenguajes y estándares semánticos: OWL 2 y RDF	33](#lenguajes-y-estándares-semánticos:-owl-2-y-rdf)

[1.3.2.3 Edición y validación ontológica: Protégé y HermiT	34](#edición-y-validación-ontológica:-protégé-y-hermit)

[1.3.2.4 Estándares Disciplinares (CC2020, CS2023 y SWEBOK)	34](#estándares-disciplinares-\(cc2020,-cs2023-y-swebok\))

[1.3.2.5 Python y FastAPI	34](#python-y-fastapi)

[1.3.2.6 Orquestación y LLMs	35](#orquestación-y-llms)

[1.3.2.7 Git y Github para versionado y repositorio de código y documentación	36](#git-y-github-para-versionado-y-repositorio-de-código-y-documentación)

[**Capítulo 2\. Marco Conceptual	37**](#marco-conceptual)

[2.1 Introducción	37](#introducción)

[2.2 Desarrollo del marco conceptual	37](#desarrollo-del-marco-conceptual)

[2.2.1 Dominio de la educación en informática	37](#dominio-de-la-educación-en-informática)

[2.2.1.1 Currículo universitario y fragmentación	37](#currículo-universitario-y-fragmentación)

[2.2.1.2 Dependencias conceptuales y relaciones de prerrequisito	38](#dependencias-conceptuales-y-relaciones-de-prerrequisito)

[2.2.2 Representación formal del conocimiento	39](#representación-formal-del-conocimiento)

[2.2.2.1 Ontología y sus componentes (T-Box, A-Box)	39](#ontología-y-sus-componentes-\(t-box,-a-box\))

[2.2.2.2 Grafo de conocimiento (Knowledge Graph)	39](#grafo-de-conocimiento-\(knowledge-graph\))

[2.2.3 Gestión del conocimiento	40](#gestión-del-conocimiento)

[2.2.4 Aprendizaje y navegación	40](#aprendizaje-y-navegación)

[2.2.4.1 Aprendizaje autodirigido (self-directed learning)	40](#aprendizaje-autodirigido-\(self-directed-learning\))

[2.2.4.2 Navegación y descubrimiento de recursos educativos	41](#navegación-y-descubrimiento-de-recursos-educativos)

[**Capítulo 3\. Estado del Arte	42**](#estado-del-arte)

[3.1 Introducción	42](#introducción-1)

[3.2 Objetivos de revisión	42](#objetivos-de-revisión)

[3.3 Preguntas de revisión	42](#preguntas-de-revisión)

[3.4 Estrategia de búsqueda	43](#estrategia-de-búsqueda)

[3.4.1 Motor de búsqueda a usar	44](#motor-de-búsqueda-a-usar)

[3.4.2 Cadenas de búsqueda a usar	44](#cadenas-de-búsqueda-a-usar)

[3.4.3 Documentos encontrados	45](#documentos-encontrados)

[3.4.4 Criterios de inclusión	49](#criterios-de-inclusión)

[3.4.5 Criterios de exclusión	50](#criterios-de-exclusión)

[3.5 Formulario de extracción de datos	50](#formulario-de-extracción-de-datos)

[3.6 Resultados de la revisión	52](#resultados-de-la-revisión)

[3.6.1 Respuesta a pregunta P1: modelado de currículos y dominios computacionales con ontologías y grafos	52](#respuesta-a-pregunta-p1:-modelado-de-currículos-y-dominios-computacionales-con-ontologías-y-grafos)

[3.6.2 Respuesta a pregunta P2: arquitecturas de KMS basados en grafos e ingesta automatizada	54](#respuesta-a-pregunta-p2:-arquitecturas-de-kms-basados-en-grafos-e-ingesta-automatizada)

[3.6.3 Respuesta a pregunta P3: mecanismos de navegación y descubrimiento semántico	56](#respuesta-a-pregunta-p3:-mecanismos-de-navegación-y-descubrimiento-semántico)

[3.7 Conclusiones	59](#conclusiones)

[**Capítulo 4\. Modelo del dominio del conocimiento de Ingeniería Informática	61**](#modelo-del-dominio-del-conocimiento-de-ingeniería-informática)

[4.1 Introducción	62](#introducción-2)

[4.2 Modelo ontológico formal del dominio de Ingeniería Informática	62](#modelo-ontológico-formal-del-dominio-de-ingeniería-informática)

[4.2.1 Introducción	62](#introducción-3)

[4.2.2 Desarrollo: estructura del modelo	63](#desarrollo:-estructura-del-modelo)

[4.2.3 Validación	64](#validación)

[4.3 Capa de referencia curada desde el estándar CS2023	66](#capa-de-referencia-curada-desde-el-estándar-cs2023)

[**Capítulo 5\. Conclusiones y trabajos futuros	66**](#conclusiones-y-trabajos-futuros)

[5.1 Conclusiones	66](#conclusiones-1)

[5.2 Trabajos futuros	66](#trabajos-futuros)

# **Índice de figuras**

[Figura 1\. Distribución de respondentes por ciclo (N=154). Fuente: elaboración propia a partir de la encuesta (Anexo D).	10](#figura-1.-distribución-de-respondentes-por-ciclo-\(n=154\).-fuente:-elaboración-propia-a-partir-de-la-encuesta-\(anexo-d\).)

[Figura 2\. Árbol de problemas	11](#figura-2.-árbol-de-problemas)

[Figura 3\. Facilidad percibida para identificar conocimientos previos antes de abordar un tema nuevo (1 \= nada fácil, 5 \= muy fácil; N=154). Fuente: elaboración propia (Anexo D).	14](#figura-3.-facilidad-percibida-para-identificar-conocimientos-previos-antes-de-abordar-un-tema-nuevo-\(1-=-nada-fácil,-5-=-muy-fácil;-n=154\).-fuente:-elaboración-propia-\(anexo-d\).)

[Figura 4\. Criterios usados para planificar cursos electivos (opción múltiple; N=154). Fuente: elaboración propia (Anexo D)	17](#figura-4.-criterios-usados-para-planificar-cursos-electivos-\(opción-múltiple;-n=154\).-fuente:-elaboración-propia-\(anexo-d\))

# **Índice de tablas**

[Tabla 1\. Ficha técnica de la encuesta de orientación del aprendizaje	8](#tabla-1.-ficha-técnica-de-la-encuesta-de-orientación-del-aprendizaje)

[Tabla 2\. Mapeo de resultados, medios de verificación e indicadores del objetivo O 1	20](#tabla-2.-mapeo-de-resultados,-medios-de-verificación-e-indicadores-del-objetivo-o-1)

[Tabla 3\. Mapeo de resultado, medios de verificación e indicadores del objetivo O 2	22](#tabla-3.-mapeo-de-resultado,-medios-de-verificación-e-indicadores-del-objetivo-o-2)

[Tabla 4\. Mapeo de resultado, medios de verificación e indicadores del objetivo O 3	23](#tabla-4.-mapeo-de-resultado,-medios-de-verificación-e-indicadores-del-objetivo-o-3)

[Tabla 5\. Herramientas, métodos y procedimientos por resultado	25](#tabla-5.-herramientas,-métodos-y-procedimientos-por-resultado)

[Tabla 6\. Uso de la técnica PICOC	43](#tabla-6.-uso-de-la-técnica-picoc)

[Tabla 7\. Palabras clave organizadas con técnica PICOC por pregunta	45](#tabla-7.-palabras-clave-organizadas-con-técnica-picoc-por-pregunta)

[Tabla 8\. Resultados de documentos en búsquedas y filtración	47](#tabla-8.-resultados-de-documentos-en-búsquedas-y-filtración)

[Tabla 9\. Documentos seleccionados finales	47](#tabla-9.-documentos-seleccionados-finales)

[Tabla 10\. Formulario de extracción de datos para la pregunta P1	51](#tabla-10.-formulario-de-extracción-de-datos-para-la-pregunta-p1)

[Tabla 11\. Formulario de extracción de datos para la pregunta P2	52](#tabla-11.-formulario-de-extracción-de-datos-para-la-pregunta-p2)

[Tabla 12\. Formulario de extracción de datos para la pregunta P3	52](#tabla-12.-formulario-de-extracción-de-datos-para-la-pregunta-p3)

1. # **Generalidades** {#generalidades}

Este capítulo presenta el contexto general del proyecto. Se describe la problemática que motiva el desarrollo del sistema, se enuncian los objetivos del trabajo y se detallan los métodos, procedimientos y herramientas que se emplearán para alcanzarlos.

1. ## **Problemática** {#problemática}

La caracterización de la problemática que sigue se sustenta en tres tipos de fuentes complementarias: el análisis del corpus académico institucional de la carrera (plan de estudios, sílabos, guías de concentración y plataformas docentes), que permite identificar las propiedades estructurales del cuerpo de conocimiento curricular en su estado actual; la literatura sobre representación del conocimiento educativo y estándares curriculares internacionales (CS2023, CC2020, SWEBOK), que aporta el marco conceptual para diagnosticar los déficits que afectan dicho corpus; y dos instrumentos empíricos (una encuesta de orientación del aprendizaje a 154 estudiantes de Ingeniería Informática de la PUCP, con análisis descriptivo en el Anexo D, y una entrevista semiestructurada al director de la carrera, Luis Flores, cuyo análisis temático se encuentra en el Anexo E) que documentan las consecuencias de esos déficits sobre los estudiantes de la carrera. Los datos de ambos instrumentos fueron analizados y se integran a lo largo de la descripción como manifestaciones empíricas de los déficits identificados.

###### **Tabla 1\. Ficha técnica de la encuesta de orientación del aprendizaje** {#tabla-1.-ficha-técnica-de-la-encuesta-de-orientación-del-aprendizaje}

| Campo | Detalle |
| :---- | :---- |
| Instrumento | Cuestionario autoadministrado en línea (Google Forms) |
| Población | Estudiantes de Ingeniería Informática, PUCP |
| Respuestas | 157 recibidas; 154 de Ingeniería Informática (analizadas) |
| Muestreo | No probabilístico por conveniencia |
| Periodo | 13 de mayo del 2026 \- 14 de mayo del 2026 |
| Estructura | 17 ítems (Likert 1-5, opción única, opción múltiple, abierta) |
| Análisis | Descriptivo (ítems cerrados, anexo D) y temático (ítems abiertos y entrevista, Anexo E) |
| Anexos | Análisis descriptivo de los datos de la encuesta (ítems cerrados): Anexo D  Análisis temático de los datos de la entrevista e ítems abiertos de la encuesta: Anexo E |

La encuesta de orientación del aprendizaje se aplicó mediante un cuestionario autoadministrado en línea (Google Forms) dirigido a estudiantes de Ingeniería Informática de la PUCP, difundido por correo electrónico y canales estudiantiles entre el 13 y 14 de mayo del 2026\. Se recibieron 157 respuestas, de las cuales 154 corresponden a estudiantes de Ingeniería Informática y constituyen la base del análisis; las 3 restantes, de otras especialidades, se excluyeron. El instrumento consta de 17 ítems que combinan escalas de Likert de 1 a 5, preguntas de opción única, de opción múltiple y de respuesta abierta, y cubre cuatro dimensiones: identificación de dependencias conceptuales, acceso a recursos de estudio, estrategia de aprendizaje y valoración de la propuesta (no considerada para el sustento de la problemática). Los ítems cerrados se analizaron mediante análisis descriptivo (Anexo D). La muestra es no probabilística por conveniencia y presenta sobre-representación del noveno ciclo (Figura 1), por lo que sus resultados se interpretan como evidencia indicativa del fenómeno, no como estimaciones poblacionales. ![][image2]

##### **Figura 1\. Distribución de respondentes por ciclo (N=154). Fuente: elaboración propia a partir de la encuesta (Anexo D).** {#figura-1.-distribución-de-respondentes-por-ciclo-(n=154).-fuente:-elaboración-propia-a-partir-de-la-encuesta-(anexo-d).}

Por otro lado, la entrevista semiestructurada con el director de carrera de Ingeniería Informática, Luis Flores, ha sido transcrita y analizada mediante análisis temático (Anexo E) junto a las respuestas de preguntas abiertas de la encuesta (dimensión de valoración de la propuesta que no está siendo considerada para respaldar la problemática).

1. ### **Árbol de Problemas** {#árbol-de-problemas}

| Problemas efectos | Tiempo significativo en identificar prerrequisitos conceptuales para abordar temas nuevos, con detección tardía de brechas de conocimiento una vez iniciado el estudio.  | Búsqueda dispersa de material para un mismo tema, con uso frecuente de IA generativa de propósito general como apoyo conceptual sin anclaje al currículo institucional. | Planificación del recorrido curricular guiada principalmente por canales informales (recomendaciones, horario disponible), con dificultad para articular el itinerario de forma autónoma. |  |
| :---- | :---- | :---- | :---- | ----- |
| **Problema central** | Los elementos del currículo de Ingeniería Informática PUCP (cursos, conceptos, recursos, etc.) no están disponibles de forma articulada en un medio digital integrado que permita consultarlos de forma transversal.  |  |  |  |
| **Problemas causa** | Las dependencias entre los contenidos de la carrera están especificadas a nivel de cursos (prerrequisitos formales entre asignaturas), pero no a nivel de los conceptos y temas subyacentes.  | Los recursos académicos de la carrera se encuentran distribuidos entre múltiples plataformas y formatos, sin vinculación explícita con los elementos del currículo que abordan.  | La información sobre las relaciones entre los elementos del currículo (entre cursos, entre conceptos, entre recursos) se encuentra repartida entre múltiples documentos institucionales. |  |

##### **Figura 2\. Árbol de problemas** {#figura-2.-árbol-de-problemas}

2. ### **Descripción** {#descripción}

El cuerpo de conocimiento de la carrera de Ingeniería Informática de la PUCP, entendido como el conjunto articulado de cursos, conceptos y recursos académicos que componen el dominio formativo de la disciplina, se encuentra documentado en un conjunto de artefactos institucionales heterogéneos: el plan de estudios oficial, los sílabos por asignatura, las guías de concentración y los repositorios de material docente alojados en distintas plataformas. El análisis de este corpus revela tres déficits estructurales que limitan su aprovechamiento como activo informativo digital: la representación de las dependencias entre contenidos se detiene en el nivel de curso y no desciende al nivel conceptual; los recursos académicos asociados al currículo se encuentran distribuidos sin vinculación explícita con los elementos del dominio que abordan; y las relaciones entre los elementos del currículo se reparten entre múltiples documentos institucionales sin estar articuladas entre sí. Las consecuencias observables de estos déficits sobre los estudiantes de la carrera, recogidas mediante una encuesta a 154 respondentes y una entrevista al director de carrera, permiten dimensionar la magnitud y el carácter del problema.

El primer déficit afecta la representación de las dependencias entre contenidos. El plan de estudios de Ingeniería Informática vigente en la facultad[^1] (Anexo F) establece prerrequisitos entre asignaturas como unidades atómicas: un curso A debe aprobarse antes que un curso B. Esta formalización es necesaria para la gestión académica, pero deja fuera el nivel donde efectivamente operan las dependencias de aprendizaje: el de los conceptos y temas subyacentes a cada asignatura. Por ejemplo, en el plan de estudios vigente el curso de Inteligencia Artificial (1INF24) tiene como único prerrequisito formal a Algoritmos Avanzados (1INF32) (Anexo F); sin embargo, los conceptos de probabilidad y estadística que sostienen el aprendizaje automático, impartidos en Probabilidad y Estadística (1EST22), no forman parte de esa cadena formal de prerrequisitos, pese a constituir base conceptual directa de la materia; la dependencia de aprendizaje existe, pero la estructura formal de prerrequisitos entre cursos no la representa. La literatura sobre representación del conocimiento educativo identifica este nivel de granularidad (el de los conceptos y temas dentro y entre cursos) como la unidad fundamental para soportar el razonamiento curricular automatizado [(Tsidylo & Kozibroda, 2024\)](https://www.zotero.org/google-docs/?yfOcfI), y los estándares internacionales de Computer Science Curriculum (CS2023, CC2020, SWEBOK) estructuran sus recomendaciones explícitamente sobre *Knowledge Areas, Units y Topics* jerárquicamente articulados, no sobre cursos [(Barron et al., 2026\)](https://www.zotero.org/google-docs/?yB4EsN).

La práctica pedagógica institucional ha intentado paliar este déficit mediante la recomendación de que los profesores expliciten en sus sílabos las conexiones con cursos previos y posteriores, pero el director de la carrera reconoce que el cumplimiento es heterogéneo: "algunos lo hacen con mayor éxito que otros" (L. Flores, entrevista, 2026). La consecuencia se manifiesta en los datos de la encuesta: aproximadamente el 78% de los respondentes reporta dificultad para identificar qué conocimientos previos necesita dominar antes de abordar un tema nuevo (análisis descriptivo de la encuesta sobre orientación de aprendizaje, Anexo D), y más del 86% declara haber descubierto con cierta o mucha frecuencia, ya iniciado el estudio de un tema, que le faltaba base de algún curso que no había considerado (Anexo D). Los comentarios cualitativos ilustran el fenómeno: "No te das cuenta de que te hace falta más matemática hasta que llevas Inteligencia Artificial" (respondente, ciclo 9). Desde la psicología educativa, esta situación corresponde a un déficit metacognitivo: en ausencia de un modelo explícito del dominio, el estudiante no puede dirigir eficientemente su esfuerzo hacia las brechas que más le afectan [(Buitrago & Chiappe, 2019; National Research Council, 2000\)](https://www.zotero.org/google-docs/?0InSV7). La evidencia sugiere, sin embargo, que este efecto no es uniforme a lo largo de la carrera: tiende a ser más pronunciado en los ciclos iniciales y medios, y se reduce en ciclos avanzados a medida que el estudiante construye, por exposición acumulada, una comprensión más integrada del dominio.

![][image3]

##### **Figura 3\. Facilidad percibida para identificar conocimientos previos antes de abordar un tema nuevo (1 \= nada fácil, 5 \= muy fácil; N=154). Fuente: elaboración propia (Anexo D).** {#figura-3.-facilidad-percibida-para-identificar-conocimientos-previos-antes-de-abordar-un-tema-nuevo-(1-=-nada-fácil,-5-=-muy-fácil;-n=154).-fuente:-elaboración-propia-(anexo-d).}

El segundo déficit afecta la vinculación entre los recursos académicos y los elementos del currículo a los que pertenecen. Los materiales producidos durante la formación (presentaciones, lecturas, guías de laboratorio, evaluaciones, grabaciones de clase) se alojan en plataformas y formatos heterogéneos: Paideia organiza el contenido por curso y por ciclo, los profesores mantienen repositorios individuales con sus propios criterios de organización, y los materiales externos consultados por los estudiantes (libros, papers, videos, sitios docentes) residen en infraestructuras ajenas a la universidad. Ninguna de estas fuentes mantiene metadatos compartidos que vinculen un recurso específico con los conceptos o temas del currículo que aborda, de modo que un mismo concepto cubierto en dos cursos distintos aparece como contenido aislado en cada uno, sin que la representación digital del currículo refleje su transversalidad. La literatura sobre construcción de grafos de conocimiento educativos identifica este tipo de integración heterogénea como un obstáculo central para el aprovechamiento del corpus académico institucional [(Wang, 2025\)](https://www.zotero.org/google-docs/?bjsNMW). Los datos lo confirman en el caso PUCP: más del 57% de los respondentes consulta entre dos y tres fuentes distintas cuando busca material para un concepto específico, y cerca del 28% consulta entre cuatro o más, con baja frecuencia de encontrar inmediatamente lo pertinente (Anexo D). De forma cada vez más central, las herramientas de inteligencia artificial generativa de propósito general (ChatGPT, Gemini) aparecen mencionadas en aproximadamente el 65-70% de las respuestas sobre estrategias de conexión entre temas (Anexo D), funcionando como el mecanismo de orientación conceptual más utilizado en la carrera; esta adopción masiva no resuelve el déficit de vinculación, sino que lo desplaza hacia un mediador externo que carece de contextualización al plan de estudios institucional y de trazabilidad académica verificable [(Huang et al., 2026; Y. Li et al., 2024; Z. Li et al., 2025\)](https://www.zotero.org/google-docs/?LdLcxs). La diferencia entre una orientación mediada por IA de propósito general y una representación anclada al currículo PUCP no es trivial: es la diferencia entre una respuesta plausible y una respuesta trazable.

Existen, además, condiciones institucionales que explican por qué la integración no ha ocurrido hasta ahora. El director de la carrera identifica tres barreras estructurales: los materiales docentes están protegidos por derechos de autor de sus autores individuales; los contenidos de un mismo curso varían entre ciclos a medida que los profesores actualizan su propuesta pedagógica; y el material de un ciclo anterior puede resultar incongruente con la versión vigente del curso (L. Flores, entrevista, 2026). Estas restricciones no invalidan la propuesta técnica de esta tesis (cuyo objeto no es indexar archivos físicos sino modelar semánticamente los conceptos del currículo y sus relaciones, vinculando los recursos por referencia) pero constituyen condiciones del contexto institucional que deben informar el diseño del sistema y su estrategia de mantenimiento.

El tercer déficit afecta la consolidación de las relaciones entre los elementos del currículo. Mientras los dos déficits anteriores se refieren a la representación interna de cada elemento (sus conceptos componentes; sus recursos asociados), este se refiere a cómo los elementos se conectan entre sí a nivel macroestructural: qué cursos contribuyen a una concentración de especialización, qué cursos comparten conceptos o temas transversales, qué recorridos coherentes existen entre áreas del conocimiento de la disciplina. Esta información existe parcialmente en la institución, pero se encuentra repartida entre artefactos separados: el plan de estudios oficial enumera los cursos por ciclo y los prerrequisitos, las guías de concentración describen los electivos asociados a cada línea, los sílabos detallan cada curso de forma autocontenida, y la articulación entre estos artefactos depende en gran medida del conocimiento tácito de profesores especialistas. El director de la carrera confirma este patrón: cuando un estudiante busca orientación sobre Inteligencia Artificial busca al profesor Beltrán o al profesor Villanueva; cuando se inclina por Ingeniería de Software, al profesor Dávila (L. Flores, entrevista, 2026, Anexo E). La orientación de calidad existe en la facultad, pero opera como conocimiento distribuido entre personas, no como representación accesible del currículo. La literatura sobre exploración de currículos educativos describe esta fragmentación como una de las barreras principales para la planificación de trayectorias formativas coherentes [(Nguyen et al., 2022\)](https://www.zotero.org/google-docs/?RNQgv5)

Los datos empíricos reflejan la consecuencia de este déficit sobre la planificación curricular de los estudiantes. La elección de cursos electivos se realiza, en aproximadamente el 43% de las respuestas, sobre la base de recomendaciones de compañeros (Anexo D), por detrás únicamente de la consulta del plan de estudios oficial. Cerca del 84% reporta dificultad media o alta para trazar su propio itinerario de aprendizaje (Anexo D). El director describe el patrón desde la perspectiva institucional: "muchas veces los alumnos simplemente terminan eligiendo los electivos que les cuadran en horario, más que teniendo un plan" (L. Flores, entrevista, 2026). Reconoce, además, que los estudiantes con menor promedio (CRAEST) tienen menor libertad de elección por el sistema de turnos de matrícula, lo que introduce una dimensión de desigualdad en el acceso a la orientación informal disponible. El resultado es que la articulación entre cursos, áreas y trayectorias profesionales, aunque existe en los documentos institucionales y en el conocimiento de profesores especialistas, no se encuentra disponible como representación consultable de forma autónoma por el estudiante.

![][image4]

##### **Figura 4\. Criterios usados para planificar cursos electivos (opción múltiple; N=154). Fuente: elaboración propia (Anexo D)** {#figura-4.-criterios-usados-para-planificar-cursos-electivos-(opción-múltiple;-n=154).-fuente:-elaboración-propia-(anexo-d)}

La consecuencia acumulada de estos tres déficits estructurales es que el cuerpo de conocimiento curricular de Ingeniería Informática de la PUCP, aunque existe distribuido entre múltiples artefactos institucionales y profesores expertos, no se encuentra disponible como activo digital articulado e integrado consultable de forma transversal. Los datos lo dimensionan: identificar qué se necesita aprender para un tema nuevo toma, en la moda de la muestra, más de un día, y en una proporción relevante de casos varios días o semanas (Anexo D); la orientación informal por pares funciona, pero depende del acceso de cada estudiante a redes de pares y a profesores especialistas; y la mediación de facto vía IA generativa de propósito general, aunque accesible, carece de anclaje al currículo institucional. A esto se suma que aproximadamente el 17% de los respondentes declara no tener todavía clara su área de interés profesional (Anexo D), concentrado en ciclos intermedios, un dato que sugiere que el activo digital propuesto debería habilitar tanto la navegación dirigida hacia metas conocidas como la exploración abierta del dominio para quienes aún se encuentran en fase de construcción de su identidad profesional.

Para abordar este desnivel, el presente proyecto plantea el desarrollo de un sistema de gestión del conocimiento (KMS) basado en grafos para la disciplina de Ingeniería Informática. La solución se construirá a partir de tres ejes metodológicos alineados con los déficits identificados: la formalización del dominio curricular mediante un modelado ontológico que descienda al nivel de conceptos y temas (atendiendo al primer déficit); un pipeline de ingesta automatizada que, mediante técnicas de procesamiento de lenguaje natural y modelos de lenguaje de gran escala (LLMs), extraiga y vincule los recursos académicos a los elementos del dominio que abordan (segundo déficit); y una interfaz de navegación visual que permita recorrer las relaciones del currículo como un todo articulado, identificar dependencias conceptuales, descubrir recursos pertinentes y trazar rutas de aprendizaje coherentes con metas profesionales o con la exploración abierta del dominio (tercer déficit). A diferencia de las herramientas de IA generativa de propósito general que los estudiantes utilizan actualmente, este sistema estará contextualizado al plan de estudios PUCP, anclado en estándares disciplinares verificados, y diseñado para ofrecer trazabilidad académica sobre las relaciones que representa.

3. ### **Problema seleccionado** {#problema-seleccionado}

El cuerpo de conocimiento curricular de la carrera de Ingeniería Informática de la PUCP no se encuentra disponible como un activo digital articulado e integrado que permita consultar de forma transversal sus elementos (cursos, conceptos y recursos académicos) y las relaciones entre ellos. Las dependencias entre contenidos están formalizadas a nivel de prerrequisitos entre cursos, pero no descienden al nivel conceptual donde efectivamente operan; los recursos académicos asociados a la carrera se encuentran distribuidos en plataformas y formatos heterogéneos sin vinculación explícita con los elementos del currículo que abordan; y las relaciones entre los propios elementos del currículo, aunque existen en distintos documentos institucionales y en el conocimiento tácito de profesores especialistas, no se encuentran articuladas en una representación consultable de forma autónoma. Esta situación se manifiesta en un proceso de orientación del aprendizaje que es costoso en tiempo, que se apoya en mediadores externos (IA generativa de propósito general) sin anclaje al currículo institucional ni trazabilidad académica, y que depende fuertemente de canales informales para la planificación del recorrido formativo.

2. ## **Objetivos** {#objetivos}

   1. ### **Objetivo general** {#objetivo-general}

Diseñar e implementar un sistema de gestión de conocimiento basado en grafos de conocimiento que permita a los estudiantes de Ingeniería Informática de la PUCP navegar el dominio de su carrera y descubrir recursos académicos de forma semántica y trazable, explicitando las dependencias conceptuales entre los contenidos.

2. ### **Objetivos específicos**  {#objetivos-específicos}

1. Modelar el dominio del conocimiento de la carrera de Ingeniería Informática mediante una ontología formal que represente cursos, conceptos, temas, áreas de conocimiento  y sus relaciones, tomando como referencia el plan de estudios de la PUCP y el estándar CS2023.   
2. Diseñar e implementar un módulo de gestión del grafo de conocimiento que, bajo la ontología definida, integre recursos académicos heterogéneos mediante un pipeline de ingesta automatizada y exponga una interfaz programática para su consulta y gestión.  
3. Diseñar e implementar un mecanismo de navegación y descubrimiento semántico de recursos que permita al estudiante explorar el grafo de conocimiento de forma visual identificando relaciones conceptuales a distintos niveles.

   3. ### **Resultados esperados y mapeo de verificación** {#resultados-esperados-y-mapeo-de-verificación}

###### **Tabla 2\. Mapeo de resultados, medios de verificación e indicadores del objetivo O 1** {#tabla-2.-mapeo-de-resultados,-medios-de-verificación-e-indicadores-del-objetivo-o-1}

| Objetivo: O 1: Modelar el dominio del conocimiento de la carrera de Ingeniería Informática mediante una ontología formal que represente cursos, conceptos, temas, áreas de conocimiento  y sus relaciones, tomando como referencia el plan de estudios de la PUCP y el estándar CS2023. |  |  |
| :---- | :---- | :---- |
| **Resultado** | **Medio de verificación** | **Indicador objetivamente verificable** |
| R1. Modelo ontológico formal del dominio de Ingeniería Informática que define clases, relaciones semánticas tipadas, y restricciones del dominio. | Documento de especificación de la ontología revisado y aprobado por el asesor especialista. Documento de decisiones de diseño de ontología. | Validación de experto en Ingeniería de Conocimiento respecto al diseño de la ontología y decisiones tomadas. Validación de la consistencia de la ontología mediante HermiT Define al menos 5 clases y 3 tipos de relaciones.[^2] |
| R2. Capa de referencia (instancias) curada desde el estándar CS2023. | Documento de especificación de la ontología | Validación de la consistencia de la ontología mediante HermiT |

###### **Tabla 3\. Mapeo de resultado, medios de verificación e indicadores del objetivo O 2** {#tabla-3.-mapeo-de-resultado,-medios-de-verificación-e-indicadores-del-objetivo-o-2}

| Objetivo: O 2: Diseñar e implementar un módulo de gestión del grafo de conocimiento que, bajo la ontología definida, integre recursos académicos heterogéneos mediante un pipeline de ingesta automatizada y exponga una interfaz programática para su consulta y gestión. |  |  |
| :---- | :---- | :---- |
| **Resultado** | **Medio de verificación** | **Indicador objetivamente verificable** |
| R3. Documentación del módulo del grafo de conocimiento que especifica el modelo de datos del grafo, los componentes internos del sistema y las decisiones de diseño y arquitectura evaluadas. | Documentos de arquitectura con diagramas C4, modelo de datos y ADRs. Documento de casos de prueba para validación de la ingesta automatizada del pipeline.  | Validación con respuesta positiva del experto en Ingeniería de Conocimiento. |
| R4. Módulo de gestión del grafo de conocimiento implementado que incluye el pipeline de ingesta automatizada de documentos académicos (sílabos PDF) y una API documentada para consulta y gestión del grafo. | Código fuente del módulo Documentación técnica de la API (endpoints, esquema de datos, ejemplos de uso) Reporte de extracción sobre el conjunto de pruebas. | Verificación manual de la precisión de entidades extraídas mayor o igual a un 75% (nodos o conceptos del grafo de conocimiento).[^3] |

###### **Tabla 4\. Mapeo de resultado, medios de verificación e indicadores del objetivo O 3** {#tabla-4.-mapeo-de-resultado,-medios-de-verificación-e-indicadores-del-objetivo-o-3}

| Objetivo: O 3: Diseñar e implementar un mecanismo de navegación y descubrimiento semántico de recursos que permita al estudiante explorar el grafo de conocimiento de forma visual identificando relaciones conceptuales a distintos niveles. |  |  |
| :---- | :---- | :---- |
| **Resultado** | **Medio de verificación** | **Indicador objetivamente verificable** |
| R5. Documentación del mecanismo de navegación y descubrimiento semántico (frontend) que especifica tecnologías a emplear, componentes internos del sistema y las decisiones de diseño y arquitectura evaluadas. | Documentos de arquitectura con diagramas C4 y ADRs. | Validación con respuesta positiva del experto en Ingeniería de Conocimiento. |
| R6. Prototipo funcional de navegación visual del grafo de conocimiento, que consume el módulo R4 como caja negra y permite al estudiante explorar relaciones conceptuales, visualizar prerrequisitos e identificar recorridos entre conceptos o temas.  | Código fuente Casos de prueba documentados y sus resultados.   | \- Pasa exitosamente las pruebas de aceptación (con **asesor de tesis**), donde se comprueba que el sistema responde correctamente a al menos un caso de exploración por nodo y uno de acceso a recursos asociados. |

3. ## **Métodos, procedimientos y herramientas** {#métodos,-procedimientos-y-herramientas}

En esta sección se detallarán los métodos y procedimientos necesarios para obtener los resultados. Se presenta un resumen en la Tabla 5\.

###### **Tabla 5\. Herramientas, métodos y procedimientos por resultado** {#tabla-5.-herramientas,-métodos-y-procedimientos-por-resultado}

| Resultado | Herramientas | Métodos o procedimientos |
| :---- | :---- | :---- |
| R1 \- Modelo ontológico | Protégé   OWL 2 HermiT | Metodología Ontology Development 101 (Noy & McGuinness, 2001), adaptada con validación dual (validación con experto y validación de consistencia con razonador HermiT), esquema de clases informado por Barron et al. (2026) y estándares internacionales de guías curriculares (CS2023) como referencia de vocabulario de dominio. |
| R2 \- Capa de referencia | Protégé   OWL 2 HermiT | Paso 7 de OD101: instanciación curada desde CS2023 hasta nivel KU. |
| R3 \- Documentación del módulo | Modelo C4 (Brown, 2018\) Git y Github  | Diseño arquitectónico iterativo Documentación con niveles 1-3 del Modelo C4 Registro de decisiones técnicas mediante Architecture Decision Records.  Diseño y documentación de los casos de prueba de la ingesta |
| R4 \- Módulo KG y pipeline | Neo4j Python (FastAPI) PydanticAI LLM (GPT-4o/Gemini) Git y Github Cypher (lenguaje de consulta de grafos) Git y Github  | Procedimiento de *Ontology Population* mediante extracción de información asistida por LLM y curación de contenido previa. |
| R5 \- Documentación del mecanismo | Modelo C4 Git/GitHub | Diseño documentado con C4 (niveles 1-3) y ADRs; diseño de flujos de interacción y wireframes |
| R6 \- Mecanismo de navegación | Librería de visualización de grafos (a definir según evaluación técnica) Framework frontend (a definir) Git y Github  | Prototipado iterativo; diseño de flujos de interacción; pruebas de aceptación de funcionalidades core. |

1. ### **Métodos y procedimientos** {#métodos-y-procedimientos}

   1. #### **Procedimiento para el modelado ontológico \- R1** {#procedimiento-para-el-modelado-ontológico---r1}

Para el desarrollo del modelo ontológico formal (T-Box) que representará el dominio de la Ingeniería Informática, se aplicará la metodología Ontology Development 101 propuesta por Noy y McGuinness (2001). Esta metodología iterativa ha sido adaptada para ajustarse a las particularidades del dominio educativo universitario, estructurando el procedimiento en tres fases secuenciales que agrupan los pasos de la metodología:

**Fase 1: Especificación y conceptualización del dominio**

Determinación del alcance: El dominio se delimita a los conocimientos de Ciencias de la Computación e Ingeniería de Software que toma la malla de Ingeniería Informática en la PUCP.

Adopción del metamodelo educativo: Se utilizará la arquitectura de clases de Barron et al. (2026) como esquema de referencia. Esto permite definir las clases de alto nivel y sus relaciones. Las clases de alto nivel se limitan al **modelo de conocimiento**; la clase “Competence” queda fuera del alcance actual como punto de extensión futura. Sin embargo, la referencia raíz es el modelo de conocimiento del estándar internacional CS2023.

Modelado de la capa de recursos**:** Se definirán las clases y propiedades necesarias para representar los metadatos de los recursos (sílabos, materiales, archivos). Esta capa no almacena el archivo físico, sino su **semántica** (ej. "el PDF X aborda el concepto Y"), permitiendo la navegación en el grafo posteriormente. 

**Fase 2: Formalización e implementación**

En esta fase, el diseño conceptual se traslada al entorno de desarrollo Protégé. Los pasos críticos incluyen:

- Definición de la jerarquía de clases: Implementación de las clases raíz y subclases según los estándares definidos.  
- Modelado de relaciones (propiedades de objetos): Se implementarán las relaciones fundamentales del dominio, con especial énfasis en la propiedad de prerrequisito; al ser un axioma núcleo de la ontología, esta relación permitirá los posteriores recorridos conceptuales entre nodos del grafo.  
- Serialización: El modelo será formalizado utilizando el lenguaje estándar OWL 2\.

**Fase 3: Validación dual (estructural y lógica)**

Validación de diseño con experto: De manera concurrente a la edición en Protégé, el esquema de clases, las restricciones de dominio y las propiedades serán validadas mediante revisiones directas con el asesor especialista. Finalmente se ejecutará HermiT sobre el modelo para garantizar la consistencia lógica de la T-Box.

2. #### **Procedimiento para la instanciación en capa de referencia \- R2** {#procedimiento-para-la-instanciación-en-capa-de-referencia---r2}

Conforme al Paso 7 de la metodología Ontology Development 101, se poblará la ontología con las instancias que conforman la capa de referencia del dominio: un esqueleto autoritativo y estable derivado del estándar CS2023, sobre el cual la capa de contenido institucional (R4) se enlazará sin modificarlo.

**Fase 1: Instanciación curada de la taxonomía**

Se puebla la ontología con las instancias de Área de Conocimiento y Unidad de Conocimiento del eje temático (Ciencias de la Computación e Ingeniería de Software) a partir del CS2023. La curación se detiene en el nivel de KU; las instancias de Topic y Concept se poblarán en R4 desde el material PUCP.

Registro de procedencia: cada instancia del backbone registra su estándar de origen mediante una propiedad de procedencia, habilitando la trazabilidad de la representación.

Esta capa de referencia no será modificada por el pipeline de ingesta automatizada (R4); este último únicamente podrá crear instancias institucionales y enlazarlas a los nodos del backbone.

**Fase 2: Validación**

Se ejecuta el razonador HermiT sobre la T-Box junto con la capa de referencia, verificando la ausencia de inconsistencias y el respeto de las relaciones funcionales y de las disjuntas declaradas.

3. #### **Procedimiento para la documentación del módulo del grafo de conocimiento \- R3** {#procedimiento-para-la-documentación-del-módulo-del-grafo-de-conocimiento---r3}

El objetivo de este procedimiento es producir la documentación del módulo: su modelo de datos, su arquitectura y decisiones de diseño, y los casos de prueba que validarán la ingesta del pipeline. Se emplea el Modelo C4 (Brown, s. f.) en sus niveles 1 a 3, complementado con Architecture Decision Records, y un diseño guiado por un conjunto acotado de atributos de calidad priorizados.

**Fase 1 \- Definición de atributos de calidad**

Antes de modelar componentes, se identifican los atributos de calidad que guiarán las decisiones arquitectónicas. Para este sistema, los atributos prioritarios son: mantenibilidad (el módulo de grafo debe ser modificable sin afectar el frontend), extensibilidad, y rendimiento suficiente para consultas de navegación sobre un grafo de escala universitaria.

**Fase 2 \- Modelado C4**

Se producirán tres niveles de diagramas:

Nivel 1 (Contexto del sistema): Muestra el KMS como una caja negra y sus relaciones con los actores externos: el estudiante que navega el grafo y las fuentes de datos académicos (sílabos, guías) que alimentan el pipeline.

Nivel 2 (Contenedores): Descompone el sistema en sus unidades desplegables independientes.

Nivel 3 (Componentes): Descompone el interior de cada contenedor en sus componentes lógicos. 

Esta diagramación permitirá planificar y comunicar mejor la estructura del módulo para facilitar su mantenimiento y extensión [(Brown, s. f.)](https://www.zotero.org/google-docs/?JDm2DW); así como evitar la deuda técnica. 

**Fase 3 \- Modelado del esquema de datos LPG**

Se especificará la transición del modelo ontológico OWL definido en R1 al modelo físico de Grafos de Propiedades Etiquetadas (LPG) para su implementación en Neo4j. Este paso es necesario porque OWL opera con semántica de lógicas de descripción mientras que Neo4j opera con un modelo de propiedades más eficiente para consultas de navegación. La transición preserva las clases y relaciones fundamentales de la T-Box, pero las traduce a nodos con etiquetas, relaciones con tipos y propiedades escalares.

El esquema contempla dos capas de instancias que comparten la misma estructura de etiquetas y tipos de relación: una capa de referencia (backbone), conformada por las instancias derivadas de los estándares producidas en R2, que se carga una sola vez y permanece estable; y una capa de contenido institucional, poblada incrementalmente por el pipeline de ingesta de R4, cuyas instancias se enlazan a los nodos del backbone. Esta distinción se materializa mediante una propiedad de procedencia que registra el origen de cada nodo, y condiciona las restricciones de escritura del sistema: el pipeline de ingesta opera exclusivamente sobre la capa de contenido institucional.

**Fase 4 \- Registro de decisiones (ADR)**

Las decisiones arquitectónicas de mayor impacto se documentarán mediante **Architecture Decision Records (ADRs)**, siguiendo la propuesta original de Michael Nygard. Un ADR es un registro breve de una decisión arquitectónica significativa, junto con su contexto, la alternativa o alternativas evaluadas, la decisión tomada y sus consecuencias para el sistema. Las decisiones mínimas a documentar incluirán la elección de Neo4j como motor de grafos frente a alternativas RDF, la elección del LLM para el pipeline de ingesta y la arquitectura de la interfaz del módulo.

**Fase 5 \- Diseño de casos de prueba de la ingesta**

Se define el conjunto de casos de prueba que verificarán la extracción del pipeline sobre el conjunto piloto, incluyendo el protocolo de evaluación manual y el criterio de aceptación de precisión. Este documento es el medio de verificación de la ingesta y será ejecutado en R4.

4. #### **Procedimiento para la construcción del módulo de KG y pipeline \- R4** {#procedimiento-para-la-construcción-del-módulo-de-kg-y-pipeline---r4}

**Fase 1 \- Preparación del entorno de datos**

Se configurará Neo4j con el esquema LPG derivado de la T-Box (R1) y documentado en R3, creando los índices y restricciones necesarios para garantizar la unicidad de nodos y la eficiencia de las consultas de navegación. Como paso previo a la ingesta automatizada, se carga la capa de referencia (backbone) producida en R2, que provee la estructura fija de áreas y unidades de conocimiento del dominio. El conjunto piloto de documentos a procesar comprende los sílabos de los cursos del eje temático de Ciencias de la Computación e Ingeniería de Software.

**Fase 2 \- Pipeline de ingesta automatizada**

El pipeline transforma documentos académicos no estructurados en instancias del grafo (A-Box) siguiendo el esquema de la T-Box definida en R1. El proceso consta de tres etapas:

Preprocesamiento documental: Los sílabos en formato PDF se pre-procesan con librerías especializadas. La salida es texto estructurado listo para su análisis semántico.

Extracción semántica con LLM: Mediante PydanticAI se orquesta la llamada al LLM seleccionado con prompts estructurados que instruyen al modelo a extraer únicamente entidades y relaciones definidas en la T-Box. La salida del LLM es un grafo parcial en formato JSON estructurado.

Carga en Neo4j: las entidades y relaciones extraídas se traducen a sentencias Cypher para su persistencia. Se implementa una estrategia de merge que reconcilia las entidades extraídas con la capa de referencia: cuando un concepto extraído de un sílabo coincide con un nodo del backbone, se enlaza a este en lugar de crear un duplicado; cuando no existe correspondencia, se crea como instancia institucional enlazada a la unidad de conocimiento que le corresponde. El pipeline no crea ni modifica nodos de la capa de referencia.

**Fase 3 \- Implementación de la API REST**

Se implementará el backend con Python y FastAPI, exponiendo los endpoints necesarios para que el mecanismo de navegación pueda operar sin conocer Cypher directamente. La API se documentará automáticamente con la especificación OpenAPI generada por FastAPI.

**Fase 4 \- Validación del pipeline**

La precisión del pipeline se evaluará manualmente siguiendo los casos de prueba documentados en R3 sobre el conjunto piloto: un evaluador (puede ser el mismo tesista) revisará una muestra de las entidades y relaciones extraídas y las comparará con el contenido del sílabo de origen. El criterio de aceptación de este resultado es una precisión de extracción mayor o igual al 75% sobre el conjunto de pruebas. Este criterio de precisión aplica a la extracción y el enlace de las instancias institucionales (conceptos, relaciones y vínculos al *backbone*); no aplica a la capa de referencia, que es curada y verificada en R2.

5. #### **Procedimiento para la documentación del mecanismo de navegación \- R5** {#procedimiento-para-la-documentación-del-mecanismo-de-navegación---r5}

El objetivo de este procedimiento es producir la documentación de diseño y arquitectura del mecanismo de navegación (frontend) antes de su implementación.

**Fase 1 \- Diseño de flujos e interfaz**

A partir del esquema del grafo definido en R3 y del conjunto de datos piloto disponible tras la ingesta de R4, se diseñan los flujos de interacción principales del mecanismo y se especifican sus casos de uso. Esta fase produce los wireframes de las pantallas principales.

**Fase 2 \- Documentación arquitectónica**

La arquitectura del frontend se documenta con el Modelo C4 en sus niveles 1 a 3 y se registran las decisiones de diseño relevantes mediante Architecture Decision Records, entre ellas la elección de la librería de visualización de grafos y del framework frontend en función de los requisitos de la visualización (escalabilidad de nodos, soporte para interacción de tipo drill-down, entre otros). El producto de este resultado es el documento de arquitectura, que constituye su medio de verificación.

6. #### **Procedimiento para el prototipo de navegación \- R6** {#procedimiento-para-el-prototipo-de-navegación---r6}

Se aplica un enfoque de prototipado iterativo centrado en la exploración del grafo sin requerir conocimiento del lenguaje de consulta subyacente.

**Fase 1 \- Implementación del prototipo**

Se implementa el mecanismo como una aplicación web que consume los endpoints de la API REST del módulo (R4) mediante llamadas HTTP. La lógica de navegación semántica permanece encapsulada en el backend de R4; el frontend es responsable únicamente de presentar los resultados de forma visual e interactiva, conforme a los flujos y wireframes definidos en R5.

**Fase 2 \- Pruebas de aceptación**

Las funcionalidades del prototipo se verifican mediante un plan de pruebas de aceptación ejecutado con el asesor de tesis. Cada caso de prueba especifica la entrada, la acción esperada y el criterio de aceptación, comprobando que el sistema responde correctamente a al menos un caso de exploración por nodo y uno de acceso a recursos asociados. El medio de verificación de este resultado es el código fuente del prototipo junto con los casos de prueba documentados y sus resultados.

2. ### **Herramientas** {#herramientas}

   1. #### **Base de datos orientada a grafos: Neo4j y Cypher** {#base-de-datos-orientada-a-grafos:-neo4j-y-cypher}

Se ha seleccionado Neo4j por su eficiencia en la gestión de relaciones complejas y transversales, típicas de un currículo académico. Neo4j implementa un modelo de *labeled property graph* (LPG) en el que los nodos representan entidades del dominio, las relaciones son dirigidas y tanto nodos como relaciones pueden poseer propiedades; en esta tesis, este modelo se empleará para materializar la A-Box y ejecutar consultas de navegación semántica mediante Cypher [(*Neo4j Documentation*, s. f.)](https://www.zotero.org/google-docs/?cr5imP).

A diferencia de un razonador OWL, Cypher se utilizará como un motor de recorrido de caminos y coincidencia de patrones. La principal limitación de este enfoque es que Neo4j no infiere jerarquías automáticamente, por lo que relaciones como la transitividad deberán quedar explicitadas mediante el pipeline o mediante consultas recursivas.

2. #### **Lenguajes y estándares semánticos: OWL 2 y RDF** {#lenguajes-y-estándares-semánticos:-owl-2-y-rdf}

OWL 2 se empleará para la especificación formal del dominio en la T-Box, ya que el estándar está concebido para representar ontologías con significado formal. RDF se usará como fundamento conceptual del modelo semántico, dado que define la información como grafos de triples sujeto-predicado-objeto. [(*OWL 2 Web Ontology Language Document Overview 2nd Edition*, 2012; *RDF 1.1 Concepts and Abstract Syntax*, 2014\)](https://www.zotero.org/google-docs/?V4MSIa)

3. #### **Edición y validación ontológica: Protégé y HermiT** {#edición-y-validación-ontológica:-protégé-y-hermit}

Para la edición del modelo ontológico se utilizará Protégé, un editor de ontologías de código abierto con soporte para OWL 2 y conexión directa con razonadores como HermiT. La validación lógica automática de la ontología se realizará con HermiT, un razonador OWL 2 conforme con OWL 2 Direct Semantics, con el fin de verificar la consistencia del modelo y la ausencia de clases insatisfacibles [(Glimm et al., 2014; *Protégé*, s. f.)](https://www.zotero.org/google-docs/?PSkzKb).

4. #### **Estándares Disciplinares (CC2020, CS2023 y SWEBOK)** {#estándares-disciplinares-(cc2020,-cs2023-y-swebok)}

Los estándares internacionales fundamentan la capa de referencia (*backbone*) de la ontología, limitada al modelo de conocimiento. Sus roles son diferenciados:

* CS2023 (ACM/IEEE): fuente primaria de la estructura del backbone (áreas y unidades de conocimiento del eje temático).

* SWEBOK: referencia de alineación de la rama de Ingeniería de Software. Las KAs de SE de CS2023 y SWEBOK son análogas pero no idénticas. No es fuente de extracción del backbone.

* CC2020: referencia fundacional. CC2020 introduce el paradigma de competencias que CS2023 adopta; el modelado de competencias queda fuera del alcance de este trabajo.

Las instancias derivadas de estos estándares conforman nodos fijos que el pipeline de ingesta (R4) no modifica; este únicamente enlaza el contenido institucional de la PUCP a ellos.

5. #### **Python y FastAPI** {#python-y-fastapi}

Python es un lenguaje ampliamente adoptado en computación científica, análisis de datos e inteligencia artificial, con un ecosistema maduro y portable; esto es en parte gracias a la amplitud de su ecosistema de librerías especializadas en procesamiento de lenguaje natural, manipulación de grafos y orquestación de modelos de lenguaje; además se destaca su legibilidad, flexibilidad y utilidad [(Millman & Aivazis, 2011\)](https://www.zotero.org/google-docs/?14VgsK). En este proyecto, Python constituye el entorno unificado que integra las distintas etapas del módulo KG: el preprocesamiento documental, la extracción semántica con PydanticAI y la persistencia en Neo4j mediante el driver oficial de Python.

Para la exposición de la interfaz programática del módulo, se utilizará FastAPI, un framework web moderno de alto rendimiento que permite construir APIs REST basadas en anotaciones de tipo (type hints) y con generación automática de documentación en formato OpenAPI (Swagger). La elección de FastAPI sobre alternativas como Flask o Django REST Framework se sustenta en tres criterios técnicos relevantes para este proyecto: su soporte nativo para esquemas de datos con Pydantic (que garantiza la validación de las respuestas del grafo contra un esquema definido), su rendimiento asíncrono basado en ASGI, y la generación automática de documentación interactiva que facilita la verificación de los endpoints durante el desarrollo [(Ramírez, s. f.)](https://www.zotero.org/google-docs/?DPK8wv).

6. #### **Orquestación y LLMs**  {#orquestación-y-llms}

Para automatizar la extracción de información desde sílabos y otros documentos extensos, se emplearán modelos de lenguaje de gran escala (LLMs como Gemini, GPT, etc.). Sin embargo, dado que el objetivo del módulo no es generar texto libre sino producir instancias, relaciones y restricciones compatibles con un esquema formal, la orquestación se implementará con PydanticAI. Este framework está concebido como un agente en Python orientado a aplicaciones de producción, con salidas tipadas, uso de herramientas y orquestación multiagente; posee ventajas como que cuando una salida no cumple el esquema, activa un mecanismo de reintento sobre la validación en lugar de aceptar silenciosamente un resultado inválido. A esto se suma que Pydantic genera y personaliza esquemas JSON directamente desde modelos, lo que permite representar cada entidad, relación y restricción como un contrato verificable alineado con la ontología del grafo [(Pydantic, 2024/2026)](https://www.zotero.org/google-docs/?ECK3fa).

Esta elección resulta más adecuada que una aproximación más generalista con LangChain para el núcleo de poblamiento ontológico. LangChain ofrece una arquitectura de agente preconstruida e integraciones amplias; sin embargo, allí la salida estructurada es una capacidad dentro de un ecosistema más amplio, mientras que en PydanticAI la validación tipada y el control del esquema constituyen el centro del diseño (LangChain, s. f.; Pydantic, 2024/2026). Para un pipeline cuyo foco es la consistencia semántica, la normalización y la trazabilidad, esa diferencia es metodológicamente relevante.

Extracción con LLM: Se prioriza el uso de modelos con alta capacidad de razonamiento (few-shot) para identificar relaciones complejas que no siempre son explícitas en el texto del sílabo.

7. #### **Git y Github para versionado y repositorio de código y documentación** {#git-y-github-para-versionado-y-repositorio-de-código-y-documentación}

Para los resultados R3, R4, R5 y R6 se empleará como principal repositorio Github, ya que esta herramienta sirve no solo para mantener el código, sino que su uso se extiende a la documentación técnica de arquitectura (modelo C4) y registro de decisiones arquitectónicas (ADRs) en archivos Markdown (.md) al  “vivir cerca del código” y aprovechar el versionado para poder tener registro histórico y trazabilidad de la evolución del proyecto durante todo su ciclo de vida. 

2. # **Marco Conceptual** {#marco-conceptual}

   1. ## **Introducción** {#introducción}

Este capítulo presenta los conceptos fundamentales que enmarcan el problema y la solución propuesta en esta tesis. Se organiza en cuatro bloques temáticos: el dominio de la educación en informática, con énfasis en la fragmentación curricular y las dependencias conceptuales entre contenidos; la representación formal del conocimiento mediante ontologías y grafos; los sistemas de gestión del conocimiento como infraestructura para hacer ese conocimiento accesible y útil; y los principios de aprendizaje autodirigido y navegación semántica que sustentan la interacción del estudiante con el sistema propuesto.

2. ## **Desarrollo del marco conceptual** {#desarrollo-del-marco-conceptual}

   1. ### **Dominio de la educación en informática**  {#dominio-de-la-educación-en-informática}

      1. #### **Currículo universitario y fragmentación** {#currículo-universitario-y-fragmentación}

En el ámbito de la computación, un currículo se define formalmente como la materia educativa que estructura el curso de estudio, especificando temas, pedagogías y resultados de aprendizaje para cada experiencia educativa. Tradicionalmente, este dominio se ha organizado bajo un enfoque de Aprendizaje Basado en el Conocimiento (KBL) mediante el modelo jerárquico KA-KU-LO (Knowledge Area, Knowledge Unit, Learning Outcome), donde estándares como el CS2023 identifican áreas que deben ser "empaquetadas" en cursos para conformar una oferta coherente.

Sin embargo, esta estructura jerárquica enfrenta el problema de la fragmentación, exacerbado por lo que el informe CC2020 denomina el "Desafío de la Torre de Babel", donde la falta de una nomenclatura universal y el uso de términos con significados divergentes entre instituciones generan silos de información. En la problemática específica de la PUCP, esta fragmentación se manifiesta en la forma en que el conocimiento del currículo se documenta y distribuye. El plan de estudios propone una construcción progresiva e interconectada a lo largo de los diez ciclos, pero los artefactos institucionales que lo soportan (sílabos individuales, guías de concentración, materiales por curso en Paideia) presentan los cursos como unidades autocontenidas, sin que las relaciones entre ellos queden articuladas en una representación accesible.

2. #### **Dependencias conceptuales y relaciones de prerrequisito** {#dependencias-conceptuales-y-relaciones-de-prerrequisito}

La arquitectura de un currículo en informática se sostiene sobre el concepto de andamiaje (scaffolding), donde el aprendizaje de nuevos conceptos requiere obligatoriamente de una base de conocimientos previos verificados. Los estándares internacionales como CC2020 y CS2023 establecen que la competencia no es solo la suma de saberes, sino la integración de conocimiento, habilidades y disposiciones en una tarea específica. Para operativizar esta progresión, las universidades utilizan prerrequisitos formales, los cuales intentan garantizar que el estudiante posea la base necesaria para avanzar.

En el contexto del plan de estudios de Ingeniería Informática de la PUCP, se observa una distinción crítica entre la dependencia administrativa y la dependencia conceptual. Por ejemplo, el curso de Inteligencia Artificial (1INF24) tiene como prerrequisito formal Algoritmos Avanzados (1INF32). No obstante, las relaciones conceptuales subyacentes, como la dependencia específica de ciertos modelos matemáticos o estructuras de datos para implementar redes neuronales, no se encuentran formalizadas ni explicitadas en los documentos institucionales. Los prerrequisitos de curso constituyen, por tanto, una representación de granularidad agregada que sirve a la gestión académica pero no expone las dependencias del dominio a nivel de los conceptos, temas subyacentes. Esta diferencia de granularidad explica por qué las relaciones operativas del aprendizaje quedan implícitas en el conocimiento tácito de cada profesor en lugar de estar disponibles como representación consultable.

2. ### **Representación formal del conocimiento** {#representación-formal-del-conocimiento}

   1. #### **Ontología y sus componentes (T-Box, A-Box)** {#ontología-y-sus-componentes-(t-box,-a-box)}

Una ontología es una especificación formal y explícita de una conceptualización compartida dentro de un dominio determinado (Gruber, 1993). Provee el vocabulario común necesario para que sistemas de IA compartan y reutilicen conocimiento. Según Di Giacomo y Lenzerini (1996), un sistema basado en lógica de descripción (que proporcionan una semántica formal para los lenguajes de ontologías) se divide en dos componentes:

T-Box (Terminological Box): Representa el esquema o estructura conceptual, definiendo clases y relaciones (ej. "Una Unidad de Conocimiento es parte de un Área de Conocimiento").

A-Box (Assertion Box): Contiene las aserciones sobre individuos o instancias específicas (ej. "El curso INF241 es una instancia de la clase Curso").

En esta tesis, la T-Box define el esquema del dominio, mientras que la A-Box se divide en dos capas pobladas con los datos específicos del CS2023 (Áreas de Conocimiento y Unidades de Conocimiento*)* y del plan de estudios de la PUCP respectivamente.

2. #### **Grafo de conocimiento (Knowledge Graph)** {#grafo-de-conocimiento-(knowledge-graph)}

El concepto de grafo de conocimiento fue popularizado por Google en 2012 bajo el lema "cosas, no cadenas" (things, not strings), buscando pasar de la búsqueda de texto plano a la búsqueda de entidades del mundo real. Una definición más formal establece que un grafo de conocimiento adquiere e integra información en una ontología y aplica un razonador para derivar nuevo conocimiento (Ehrlinger & Wöß, 2016).

A diferencia de una base de datos tradicional, el grafo de conocimiento permite representar relaciones complejas y realizar inferencias semánticas. Ejemplo: Si un estudiante busca "Estructuras de Datos", el grafo no solo devuelve un nodo que abarque directamente ese tema, sino que conecta semánticamente con otros recursos como guías de práctica y videos que apoyan conceptos específicos dentro de ese tema y relacionados.

3. ### **Gestión del conocimiento** {#gestión-del-conocimiento}

   1. **Sistemas de gestión del conocimiento (KMS)**

Un KMS es un sistema basado en tecnologías de la información diseñado para apoyar y mejorar los procesos organizacionales de creación, almacenamiento, recuperación, transferencia y aplicación del conocimiento. Según Alavi y Leidner (2001), el objetivo de un KMS no es solo almacenar datos, sino facilitar que la información sea poseída en la mente de los individuos como conocimiento personalizado.

En el contexto de esta tesis, el KMS propuesto busca consolidar el conocimiento que se encuentra disperso en documentos académicos y plataformas separadas, exponiéndolo como representación relacional accesible para la toma de decisiones del estudiante.

4. ### **Aprendizaje y navegación** {#aprendizaje-y-navegación}

   1. #### **Aprendizaje autodirigido (self-directed learning)** {#aprendizaje-autodirigido-(self-directed-learning)}

El aprendizaje autodirigido es una competencia humana básica definida como la capacidad de aprender por cuenta propia. El modelo de Garrison (1997) propone tres dimensiones interconectadas:

* Autogestión: El control de las tareas y recursos de aprendizaje.  
* Automonitoreo: La responsabilidad cognitiva de construir significado y monitorear el propio proceso de aprendizaje.  
* Motivación: El impulso para iniciar y persistir en la tarea de aprendizaje.

La dimensión del automonitoreo es particularmente sensible al estado del dominio: cuando las relaciones conceptuales de la disciplina no están explicitadas en una representación accesible, el estudiante puede no identificar con precisión las brechas de conocimiento que aún debe cubrir, fenómeno descrito en la literatura como la dificultad de "ignorar que se ignora". El automonitoreo efectivo, por tanto, no depende solo de la disposición individual del estudiante, sino también de la disponibilidad de un modelo del dominio que permita ubicar los propios conocimientos respecto al conjunto.

2. #### **Navegación y descubrimiento de recursos educativos** {#navegación-y-descubrimiento-de-recursos-educativos}

La búsqueda exploratoria en grafos de conocimiento ocurre cuando un usuario necesita entender y extraer información de un dominio que no le es familiar. A diferencia de una búsqueda tradicional de palabras clave, la navegación semántica permite al estudiante expandir nodos progresivamente (drill-down) para acceder a niveles de detalle crecientes.

Sistemas actuales en informática utilizan estas interfaces para generar rutas de aprendizaje personalizadas (ej. el camino más corto entre dos conceptos) y visualizar dependencias de prerrequisitos mediante métricas de centralidad (Li et al., 2019; Chen et al., 2023; Dong et al., 2023; Liu & Zhan, 2025). Esto permite que el estudiante trace una ruta hacia una meta profesional específica, descubriendo recursos que apoyan directamente su plan de carrera.

3. # **Estado del Arte** {#estado-del-arte}

   1. ## **Introducción** {#introducción-1}

En este capítulo se presenta la revisión sistemática de literatura realizada como sustento del presente proyecto. El proceso sigue las tres fases establecidas por Kitchenham y Charters (2007): planificación, que comprende la definición del objetivo de revisión y las preguntas de investigación; ejecución, que incluye la estrategia de búsqueda, los criterios de selección y la extracción de datos; y reporte, que sintetiza los hallazgos en respuesta a cada pregunta formulada.

2. ## **Objetivos de revisión** {#objetivos-de-revisión}

La presente revisión sistemática tiene como objetivo identificar y analizar el estado actual de la investigación en tres áreas que fundamentan el presente proyecto: el modelado ontológico de dominios curriculares en computación, las arquitecturas de sistemas de gestión de conocimiento basados en grafos con ingesta para contextos educativos, y los mecanismos de navegación y descubrimiento semántico de recursos académicos. A partir de esta revisión se busca identificar las limitaciones de los enfoques existentes y fundamentar las decisiones de diseño del sistema propuesto.

3. ## **Preguntas de revisión** {#preguntas-de-revisión}

###### **Tabla 6\. Uso de la técnica PICOC** {#tabla-6.-uso-de-la-técnica-picoc}

| Criterio | Descripción |
| ----- | ----- |
| **P \- Población** | Estudiantes universitarios, sistemas educativos, currículos de Ingeniería Informática |
| **I \- Intervención** | Grafos de conocimiento, ontologías, sistemas de gestión de conocimiento semántico |
| **C- Comparación** | No aplica (no se comparan métodos entre sí, sino se caracteriza el estado del arte) |
| **O \- Resultados** | Modelado curricular, ingesta automatizada de contenido, navegación semántica, rutas de aprendizaje |
| **Cx \- Contexto** | Educación superior, ingeniería informática, ciencias de la computación |

Las preguntas de revisión formuladas son:

* P1. ¿Cómo se han modelado currículos universitarios y dominios de conocimiento computacional mediante grafos de conocimiento u ontologías, y qué limitaciones presentan los enfoques existentes?

* P2. ¿Qué arquitecturas de sistemas de gestión de conocimiento basados en grafos han sido propuestas para contextos educativos, y cómo se ha implementado la ingesta automatizada de contenido académico?

* P3. ¿Qué mecanismos de navegación y descubrimiento semántico de recursos educativos han sido evaluados, y qué evidencia existe sobre su efectividad para apoyar el aprendizaje autodirigido?

  4. ## **Estrategia de búsqueda** {#estrategia-de-búsqueda}

Para la elaboración del presente estado del arte, se realizó una Revisión Sistemática de Literatura (SLR) siguiendo los lineamientos de Kitchenham (2007). Se seleccionaron las bases de datos ACM Digital Library y Scopus, aplicando cadenas de búsqueda centradas en la intersección de la gestión del conocimiento y la ingeniería de software. Los criterios de inclusión se enfocaron en estudios publicados en los últimos 7 años que aborden los temas de cada pregunta.

1. ### **Motor de búsqueda a usar** {#motor-de-búsqueda-a-usar}

- Scopus  
- ACM Digital Library

  2. ### **Cadenas de búsqueda a usar** {#cadenas-de-búsqueda-a-usar}

Las cadenas se construyeron a partir del método PICOC, priorizando los criterios I (Intervención), O (Resultados) y Cx (Contexto), que concentran los términos más discriminantes para cada pregunta. La tabla 6 muestra las palabras clave organizadas por criterio PICOC y por pregunta.

###### **Tabla 7\. Palabras clave organizadas con técnica PICOC por pregunta** {#tabla-7.-palabras-clave-organizadas-con-técnica-picoc-por-pregunta}

| Criterio | P1 | P2 | P3 |
| :---- | :---- | :---- | :---- |
| **I** | "educational knowledge graph", "ontology", "semantic model" | "knowledge graph", "knowledge management system", "knowledge base" | "knowledge graph", "semantic model" |
| **O** | "curriculum", "course", "syllabus", "learning outcome", "competency" | "information extraction", "knowledge extraction", "ingestion", "ontology population", "document processing" | "resource discovery", "navigation", "visualization", "exploratory search" |
| **Cx** | "computer science", "computing education" | "education", "academic", "e-learning", "university" | "student", "learner", "self-directed learning" |

La estructura de cada cadena sigue la forma (I) AND (O) AND (Cx):

P1: 

("educational knowledge graph" OR “ontology” OR ontological OR "semantic model") AND

(curriculum OR curricula OR curricular OR syllabus OR syllabi OR course OR courses OR prerequisite OR prerequisites OR "learning outcome\*" OR competence OR competency ) AND

("computer science" OR "computing education")

P2: 

("knowledge graph" OR "knowledge base" OR "knowledge management system") AND 

("information extraction" OR "knowledge extraction" OR “ingestion” OR "ontology population" OR "document processing") AND 

(“education” OR “academic” OR "e-learning" OR university)

P3: 

("knowledge graph" or “semantic model”) AND 

("resource discovery" OR “navigation” OR “visualization” OR "exploratory search") AND 

(“student” OR “learner” OR "self-directed learning")

3. ### **Documentos encontrados** {#documentos-encontrados}

El proceso de selección de documentos se realizó en tres etapas. En la primera etapa se ejecutaron las cadenas de búsqueda en Scopus (por título, resumen y palabras clave), aplicando filtros de Subject Area (Computer Science), rango de años (2019-2026) y tipo de documento (Article, Conference Paper); y en ACM Digital Library (ACM Full-Text Collection) se ejecutó las mismas cadenas (por resumen) aplicando los mismos filtros de rango de años. En la segunda etapa se revisaron los títulos y resúmenes de los resultados obtenidos, descartando aquellos claramente fuera del dominio de interés y aplicando los criterios de inclusión y exclusión definidos. En la tercera etapa se realizó la lectura completa de los documentos que superaron las etapas anteriores, descartando aquellos que, pese a pasar el filtro de título y resumen, no aportaban información relevante para responder las preguntas de revisión; también se descartaron los que no eran accesibles o eran de pago. La Tabla 7 resume los resultados de cada etapa por cadena de búsqueda por base de datos.

###### **Tabla 8\. Resultados de documentos en búsquedas y filtración** {#tabla-8.-resultados-de-documentos-en-búsquedas-y-filtración}

| Cadena | Base de datos | Resultados iniciales | Tras filtros de base de datos | Duplicados entre bases de datos | Tras filtro de título y abstract | Seleccionados finales |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **P1** | **Scopus** | 196 | 40 | 2 | 5 | 5 |
| **P1** | **ACM** | 12 | 3 |  | 0 | 0 |
| **P2** | **Scopus** | 233 | 124 | 12 | 10 | 10 |
| **P2** | **ACM** | 17 | 14 |  | 0 | 0 |
| **P3** | **Scopus** | 151 | 106 | 2 | 7 | 7 |
| **P3** | **ACM** | 2 | 2 |  | 0 | 0 |
| **Total** |  | 580 | 309 | 0 | 22 | 22 |

###### **Tabla 9\. Documentos seleccionados finales** {#tabla-9.-documentos-seleccionados-finales}

| Título de la publicación | Autor | Año | Fuente | Pregunta relacionada |
| :---- | :---- | :---- | :---- | :---- |
| A Courses Ontology System for Computer Science Education | Wang, Y., Wang, Z., Hu, X., Bai, T., Yang, S., & Huang, L. | 2019 | Scopus | P1 |
| A Ontology Construction Method of Course Knowledge Graph Based on Dependency of Knowledge Points | Bin, Q., Zuhairi, M. F., Morcos, J., & Zhengqiu, L. | 2025 | Scopus | P1 |
| An Educational Ontology for Formal Languages and Compilers | Oprea, M. | 2020 | Scopus | P1 |
| Ontology-based representation and design of subject domains for Computer Science education | Tsidylo, I. M., & Kozibroda, S. V. | 2024 | Scopus | P1 |
| Towards a Computer Science Topics Ontology | Barron, J., Feldhausen, R., & Bean, N. H. | 2026 | Scopus | P1 |
| Course Recommendation System Based on Course Knowledge Graph Generated by Large Language Models | Chen, X., Yin, C., Chen, H., Rong, W., Ouyang, Y., & Chai, Y. ( | 2024 | Scopus | P2 |
| Automatic Construction System for Curriculum Knowledge Graphs Based on Large Language Models LLM-Based Curriculum Map Construction | Li, S., Xiao, Y., Li, J., & Li, Y. | 2026 | Scopus | P2 |
| Multi-Source Education Knowledge Graph Construction and Fusion for College Curricula | Li, Z., Cheng, L., Zhang, C., Zhu, X., & Zhao, H. | 2023 | Scopus | P2 |
| Construction of Programming Knowledge Graph Based on Student Knowledge Needs | Liu, L. | 2024 | Scopus | P2 |
| Research on Triple Joint Extraction Method of Knowledge Graph for Education Domain | Liu, Y., Zuo, Q., Zhang, S., Li, Y., Wang, C., Han, F., & Cheng, X. | 2026 | Scopus | P2 |
| An approach to constructing a graph data repository for course recommendation based on IT career goals in the context of big data | Nguyen, T., Vu, N., & Ly, B. | 2022 | Scopus | P2 |
| Knowledge Graph for University Course Construction Based on Gated Graph Attention Networks | Pan, J., Liu, J., Wei, D., Zhuang, J., Qiu, S., & Du, J. | 2023 | Scopus | P2 |
| Study on Multi-source Heterogeneous Data Fusion and Knowledge Graph Construction Techniques in Higher Education Institutions | Wang, C. | 2025 | Scopus | P2 |
| LLM-Powered Construction of Course Knowledge-Competency Graphs | Xu, J., & Che, M. | 2025 | Scopus | P2 |
| GLM-4-Based Method for Automatic Construction of Content Graph | Yang, M., Diao, M., Luo, J., Shen, W., & Zhang, C. | 2025 | Scopus | P2 |
| Design and Development of a Knowledge Service Platform in the Field of Computer Science: Knowledge Service Platform in Computer Science: Design and Development | Chen, C., Zhu, S., Tao, Q., Wu, Q., & Shi, Y. | 2023 | Scopus | P3 |
| Gradual Study Advising with Course Knowledge Graphs | Dong, J., Li, W., Wang, Y., Li, Q., Baciu, G., Cao, J., Huang, X., Li, R. C., & Ng, P. H. F. | 2023 | Scopus | P3 |
| Web-Based Learning Object Search Engine Solution Together with Data Visualization: The Case of MERLOT II | Gunarathne, W. K. T. M., Chootong, C., Sommool, W., Ochirbat, A., Chen, Y.-C., Reisman, S., & Shih, T. K. | 2018 | Scopus | P3 |
| Construction, visualization and application of knowledge graph of computer science major | Li, Y., Zhao, J., Yang, L., & Zhang, Y. | 2019 | Scopus | P3 |
| The ESW of Wikidata: Exploratory search workflows on Knowledge Graphs | Lissandrini, M., Prando, G., & Silvello, G. | 2025 | Scopus | P3 |
| Research on Visual Learning Platform for Database Principles Knowledge Points Integrating Knowledge Graph and Deep Learning | Liu, P., & Zhan, C. | 2025 | Scopus | P3 |
| AI-driven Interactive Hierarchical Concept Maps for Digital Learning Environments and Intelligent Textbooks | Tytenko, S. | 2025 | Scopus | P3 |

4. ### **Criterios de inclusión** {#criterios-de-inclusión}

- Publicado entre 2019 y 2026  
- Publicado en revista con peer review o en conferencia indexada (ACM, IEEE, Springer, Elsevier)  
- El estudio propone, implementa o evalúa al menos uno de los siguientes temas centrales con respecto a las preguntas de investigación: (a) un modelo ontológico o grafo de conocimiento aplicado a un dominio curricular o educativo, (b) un sistema de gestión de conocimiento para contextos de aprendizaje que incluye ingesta de contenido, o (c) un mecanismo de navegación o descubrimiento de recursos académicos  
- Disponible en inglés o español

  5. ### **Criterios de exclusión** {#criterios-de-exclusión}

- Literatura gris (preprints sin revisar, blogs, repositorios GitHub, tweets), salvo validación explícita del asesor  
- Estudios que mencionan "knowledge graph" o "ontology" únicamente como contexto o trabajo futuro, sin implementación ni diseño formal  
- Aplicaciones fuera del dominio educativo sin transferibilidad clara al contexto universitario.  
- Acceso bloqueado o de pago.  
- Estudios duplicados dentro de la misma pregunta de revisión

  5. ## **Formulario de extracción de datos** {#formulario-de-extracción-de-datos}

Una vez seleccionados los estudios primarios y verificada su calidad, se aplicó un formulario de extracción para registrar de manera homogénea la información relevante de cada trabajo. Este instrumento permitió sistematizar los datos bibliográficos y las variables de análisis asociadas a cada pregunta de revisión, de modo que la evidencia pudiera compararse y sintetizarse con mayor precisión. Para mantener trazabilidad y orden en el análisis, el formulario se organizó en una hoja independiente por cada pregunta de revisión.

###### **Tabla 10\. Formulario de extracción de datos para la pregunta P1** {#tabla-10.-formulario-de-extracción-de-datos-para-la-pregunta-p1}

| Campo | Descripción de lo que se extrae | Justificación para la revisión |
| :---- | :---- | :---- |
| ¿Qué entidades modela? | Cursos, conceptos, unidades de conocimiento, entre otras | Permite comparar el nivel de granularidad y cobertura del modelo propuesto. |
| ¿Qué tecnología de representación usa? | OWL, RDF, grafo de propiedades, entre otras | Sirve para contrastar formalismos de representación semántica. |
| ¿Cómo se alinea a un estándar disciplinar? | Alineación con CC2020, CS2023, ACM, IEEE u otros marcos | Permite evaluar si el modelo está sustentado en un referente curricular reconocido. |
| ¿Qué limitaciones declara el autor? | Cobertura limitada, falta de validación, problemas de escalabilidad, entre otras | Ayuda a identificar vacíos que justifican la propuesta de la tesis. |

###### **Tabla 11\. Formulario de extracción de datos para la pregunta P2** {#tabla-11.-formulario-de-extracción-de-datos-para-la-pregunta-p2}

| Campo | Descripción de lo que se extrae | Justificación para la revisión |
| :---- | :---- | :---- |
| ¿Qué componentes tiene el sistema? | Ingesta, almacenamiento, consulta, interfaz, exportación, recomendación, etc. | Permite caracterizar la arquitectura funcional del sistema. |
| ¿Cómo se integra/ingesta el contenido? | Scraping, NLP, reglas, LLM, extracción manual o enfoques híbridos | Sirve para comparar estrategias de construcción automática del conocimiento. |
| ¿Qué tecnología de almacenamiento usa? | Neo4j, triplestore RDF, bases relacionales, u otras | Permite evaluar decisiones de persistencia y modelado de datos. |
| ¿Cómo expone el conocimiento? | API REST, Cypher, SPARQL, interfaz web u otro mecanismo | Ayuda a identificar cómo el sistema hace accesible el grafo al usuario o a otras aplicaciones. |
| ¿Qué limitaciones declara el autor? | Precisión, escalabilidad, dependencia del dominio, cobertura, entre otras | Permite detectar debilidades técnicas y de aplicación que orientan mejoras. |

###### **Tabla 12\. Formulario de extracción de datos para la pregunta P3** {#tabla-12.-formulario-de-extracción-de-datos-para-la-pregunta-p3}

| Campo | Descripción de lo que se extrae | Justificación para la revisión |
| :---- | :---- | :---- |
| ¿Qué tipo de interfaz de exploración propone? | Grafo visual, interfaz conversacional, lista, vista mixta u otra | Permite clasificar el modo de interacción ofrecido al usuario. |
| ¿Qué funcionalidades de navegación implementa? | Rutas de aprendizaje, filtros, búsqueda semántica, recomendación, visualización, etc. | Sirve para comparar el alcance funcional de cada propuesta. |
| ¿Cómo evalúa la efectividad? | Experimentos con usuarios, validación experta, métricas automáticas, cuestionarios, etc. | Permite valorar la solidez de la evidencia reportada. |
| ¿Qué resultado reporta? | Mejora en orientación, satisfacción, rapidez de búsqueda, comprensión, entre otros | Ayuda a sintetizar el aporte concreto del mecanismo propuesto. |
| ¿Qué limitaciones declara el autor? | Dominio acotado, falta de validación, usabilidad limitada, dependencia de expertos, etc. | Permite detectar vacíos que justifican el diseño de la solución propia. |

El detalle del formulario de extracción para cada pregunta de investigación puede ser consultado en el siguiente enlace:

[https://docs.google.com/spreadsheets/d/1TIa564pZofJFd22sXDC10J2rh9d6sZlQ7LabbzptVk8/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1TIa564pZofJFd22sXDC10J2rh9d6sZlQ7LabbzptVk8/edit?usp=sharing)

O puede consultarse en el **anexo A, B y C**.

6. ## **Resultados de la revisión** {#resultados-de-la-revisión}

   1. ### **Respuesta a pregunta P1: modelado de currículos y dominios computacionales con ontologías y grafos** {#respuesta-a-pregunta-p1:-modelado-de-currículos-y-dominios-computacionales-con-ontologías-y-grafos}

Los estudios revisados revelan una tendencia consistente hacia la modelización jerárquica del currículo, donde la unidad básica de representación es el **punto de conocimiento** o **concepto**, agrupado en estructuras de mayor granularidad como unidades temáticas, cursos y áreas de conocimiento. Esta arquitectura de tres o más niveles es reconocible en prácticamente todos los trabajos analizados (Wang et al., 2019; Bin et al., 2025; Oprea, 2020). Sin embargo, los modelos más recientes amplían el alcance ontológico más allá del contenido disciplinar: Tsidylo y Kozibroda (2024) incorporan explícitamente competencias (universales, profesionales e instrumentales) junto con el perfil del estudiante y los recursos educativos, mientras que Barron et al. (2026) añaden resultados de aprendizaje, niveles de habilidad según la Taxonomía de Bloom revisada y criterios de evaluación. Esta evolución sugiere un desplazamiento desde ontologías centradas en el **qué se enseña** hacia modelos que intentan capturar **cómo se evalúa y a quién**. No obstante, la alineación con estándares disciplinares internacionales sigue siendo la excepción: la mayoría de los trabajos se ancla en currículos institucionales propios o en sílabos de curso específicos (Wang et al., 2019; Bin et al., 2025; Oprea, 2020; Tsidylo & Kozibroda, 2024), y únicamente Barron et al. (2026) adoptan explícitamente el marco ACM Computer Science Curricula 2023 como referente externo, lo que dificulta la interoperabilidad y comparabilidad entre las propuestas.

En cuanto a las tecnologías de representación, existe una predominio claro de OWL (Web Ontology Language) como lenguaje de modelado, utilizado en la totalidad de los estudios revisados, en combinación con la herramienta Protégé para el diseño de la jerarquía ontológica (Wang et al., 2019; Bin et al., 2025; Oprea, 2020; Tsidylo & Kozibroda, 2024; Barron et al., 2026). El estrato de almacenamiento y consulta incorpora tecnologías de la Web Semántica como RDF (Tsidylo & Kozibroda, 2024\) y el lenguaje de consultas SPARQL (Barron et al., 2026), lo que posiciona la pila tecnológica de la Web Semántica como el paradigma dominante en el área. Resulta significativa la ausencia total de enfoques basados en grafos de propiedad etiquetada (Labeled Property Graphs, LPG) o plataformas como Neo4j, lo que sugiere que la comunidad investigadora orientada a la representación curricular ha optado mayoritariamente por la semántica formal de la web semántica en detrimento de soluciones de grafos nativos más escalables. En los trabajos que requieren construcción automatizada del grafo, se emplean frameworks complementarios como Jena con Java (Wang et al., 2019\) o scripts de scraping en Python con BeautifulSoup (Bin et al., 2025), evidenciando que la capa de adquisición de datos permanece ad hoc y poco estandarizada.

Las limitaciones declaradas por los autores representan un vacío de investigación sistemático que trasciende los estudios individuales. En primer lugar, se identifica un problema generalizado de **escala reducida y cobertura parcial**; los modelos se construyen sobre un único curso o área de conocimiento acotada, y los propios autores advierten que la extensión a dominios más amplios plantea desafíos de rendimiento y consistencia (Bin et al., 2025; Barron et al., 2026). En segundo lugar, persiste una dependencia significativa del **trabajo manual** para la extracción y validación de conceptos a partir de libros de texto y sílabos, lo que compromete la escalabilidad y reproducibilidad de los métodos (Bin et al., 2025; Oprea, 2020). En tercer lugar, varios trabajos admiten carecer de **validación empírica** con usuarios reales o de un proceso formal para evaluar la maestría del estudiante sobre los nodos del grafo (Barron et al., 2026; Tsidylo & Kozibroda, 2024). Finalmente, el uso de datos sintéticos o placeholders para poblar partes del modelo (Barron et al., 2026\) pone de manifiesto que la brecha entre la estructura ontológica propuesta y una implementación instanciada y operativa sigue sin cerrarse. En conjunto, estos hallazgos señalan la necesidad de enfoques que combinen alineación con estándares curriculares reconocidos, automatización en la construcción del grafo y mecanismos de validación formales que permitan verificar la utilidad pedagógica del modelo resultante.

2. ### **Respuesta a pregunta P2: arquitecturas de KMS basados en grafos e ingesta automatizada** {#respuesta-a-pregunta-p2:-arquitecturas-de-kms-basados-en-grafos-e-ingesta-automatizada}

El análisis arquitectónico de los sistemas de gestión del conocimiento basados en grafos para educación revela un patrón estructural recurrente compuesto por cuatro capas funcionales: ingesta y preprocesamiento de datos, extracción y procesamiento del conocimiento, almacenamiento en grafo, y visualización o exposición (Liu, 2024; Xu & Che, 2025; Wang, 2025; Li et al., 2023). En lo que respecta a la tecnología de almacenamiento, Neo4j se consolida como la plataforma dominante de manera evidente, adoptada prácticamente en la totalidad de los estudios que especifican un motor de base de datos (Nguyen et al., 2022; Li et al., 2026; Liu, 2024; Yang et al., 2025; Pan et al., 2023; Xu & Che, 2025; Li et al., 2023; Wang, 2025). Esta preferencia responde a su modelo de datos nativo, el Labeled Property Graph (LPG), y a su capacidad para representar relaciones complejas entre entidades curriculares de forma eficiente. Como excepción notable, Wang (2025) adopta un enfoque híbrido que combina Neo4j para la gestión del grafo con tripletas RDF para el almacenamiento semántico del conocimiento, complementado por una capa de caché en Redis, lo que refleja una arquitectura más sofisticada orientada a entornos institucionales de mayor escala. En contraste, Chen et al. (2024) y Liu et al. (2026) no especifican el motor de almacenamiento, limitando la comparabilidad técnica de sus propuestas.

La evolución en los métodos de ingesta y construcción automática de grafos describe una trayectoria clara desde enfoques basados en reglas y anotación manual hacia pipelines híbridos cada vez más dependientes de modelos de lenguaje de gran escala (Large Language Models, LLMs). Los trabajos más tempranos del corpus utilizan técnicas de web scraping  con modelos de aprendizaje profundo de tipo BiLSTM+CRF o GGAT para el reconocimiento de entidades y relaciones (Liu, 2024; Pan et al., 2023; Chen et al., 2024), mientras que los estudios más recientes desplazan el peso del procesamiento hacia LLMs (como GLM-4, DeepSeek, Qwen o ChatGLM-6B) para la extracción semántica automatizada de conceptos y relaciones a partir de documentos curriculares no estructurados (Yang et al., 2025; Li et al., 2026; Xu & Che, 2025). No obstante, esta transición no implica la eliminación del componente manual: prácticamente todos los sistemas mantienen alguna forma de intervención humana, ya sea para la anotación de datos de entrenamiento, la validación experta de la ontología o la corrección de extracciones erróneas (Pan et al., 2023; Xu & Che, 2025; Liu et al., 2026). Ello evidencia que la automatización plena del proceso de construcción del grafo sigue siendo un problema abierto, donde la supervisión experta actúa como mecanismo de control de calidad indispensable.

Respecto a la exposición de las funcionalidades, predomina la visualización interactiva como modalidad principal de acceso que es a menudo integrada directamente en plataformas educativas institucionales (Yang et al., 2025), mientras que los mecanismos de consulta estructurada mediante el lenguaje Cypher constituyen la segunda opción más frecuente (Liu, 2024; Yang et al., 2025). Solo un caso adopta una arquitectura de servicios basada en APIs RESTful y consultas SPARQL, orientada a la integración con sistemas externos (Wang, 2025), lo que pone de manifiesto la escasa interoperabilidad entre plataformas que caracteriza este conjunto de propuestas. En cuanto a las limitaciones críticas, se identifican tres vacíos transversales: en primer lugar, la fragilidad en la precisión de la extracción, especialmente ante relaciones semánticas ambiguas, conceptos abstractos o términos con alta especificidad disciplinar (Li et al., 2026; Yang et al., 2025; Xu & Che, 2025; Liu et al., 2026); en segundo lugar, la dependencia de datos de dominio cerrado o de baja cobertura, que compromete la generalización de los modelos entrenados (Chen et al., 2024; Li et al., 2023); y, en tercer lugar, la escasez de conjuntos de datos públicos anotados específicos para el dominio educativo, lo que dificulta la replicación y la comparación sistemática entre propuestas (Liu et al., 2026). En conjunto, estos hallazgos sugieren que la madurez arquitectónica de los sistemas es considerablemente mayor que su madurez en términos de calidad del conocimiento representado y su capacidad de validación empírica a escala real.

3. ### **Respuesta a pregunta P3: mecanismos de navegación y descubrimiento semántico** {#respuesta-a-pregunta-p3:-mecanismos-de-navegación-y-descubrimiento-semántico}

El conjunto de propuestas analizadas converge hacia interfaces de tipo mixto que integran visualización interactiva de grafos, y funcionalidades de búsqueda y navegación estructurada siendo este el paradigma dominante frente a las interfaces puramente conversacionales o basadas en listas (Li et al., 2019; Chen et al., 2023; Dong et al., 2023; Liu & Zhan, 2025). La funcionalidad más recurrente es la generación de rutas de aprendizaje, presente en múltiples sistemas bajo distintas implementaciones: desde el cálculo del camino más corto entre nodos de conocimiento (Li et al., 2019\) hasta la optimización mediante redes neuronales de grafos convolucionales (Liu & Zhan, 2025\) o la visualización de dependencias de prerrequisitos con métricas de centralidad como PageRank (Dong et al., 2023). Un segundo patrón destacado es la navegación jerárquica de tipo drill-down, que permite al usuario expandir progresivamente nodos para acceder a niveles de granularidad creciente, incluyendo variantes con generación dinámica de sub-mapas impulsada por LLMs (Tytenko, 2025). En el extremo más técnico del espectro se sitúan propuestas orientadas a usuarios expertos, como los flujos de trabajo exploratorios sobre grafos Wikidata mediante consultas SPARQL secuenciadas en entornos de notebook (Lissandrini et al., 2025), y la exploración jerárquica por clusters temáticos en motores de búsqueda de objetos de aprendizaje (Gunarathne et al., 2018), ambas con un perfil de usuario claramente diferenciado del estudiante autodirigido típico.

La evidencia empírica sobre la efectividad de estos mecanismos es heterogénea tanto en rigor metodológico como en los resultados que reporta. El estudio más robusto del corpus corresponde a Liu & Zhan (2025), quienes desarrollan un experimento longitudinal de dieciséis semanas con 180 estudiantes divididos en grupos de control y experimental, reportando mejoras cuantificables en dominio del conocimiento (22.7%), eficiencia de aprendizaje (19.6%) y satisfacción del usuario (32.1%). Por su parte, Tytenko (2025) recurre a cuestionarios de satisfacción con estudiantes universitarios, obteniendo valoraciones elevadas (8.91/10 en satisfacción general y 91.4% de percepción de mayor compromiso), aunque sin métricas objetivas de rendimiento académico. En el plano de las métricas automáticas, Gunarathne et al. (2018) validan la calidad del algoritmo de agrupamiento mediante el coeficiente de Silueta, y Lissandrini et al. (2025) emplean precisión, recall y F-score sobre flujos de consulta de referencia, aunque en ambos casos la evaluación se centra en el rendimiento técnico del sistema más que en el impacto sobre el aprendizaje. Los trabajos restantes se limitan a ilustraciones cualitativas o comparativas funcionales frente a métodos tradicionales, sin experimentos formales con usuarios (Li et al., 2019; Dong et al., 2023; Chen et al., 2023), lo que debilita significativamente las afirmaciones de efectividad pedagógica que formulan.

Las limitaciones declaradas por los autores revelan tensiones estructurales que condicionan la validez y escalabilidad de estas propuestas. En el plano de la usabilidad, la desorientación del usuario en grafos grandes y complejos emerge como un problema transversal: Tytenko (2025) reporta *topic drift* e inconsistencias estructurales en niveles profundos de navegación jerárquica, mientras que Dong et al. (2023) reconocen la dificultad de los estudiantes para localizar conceptos clave cuando el grafo crece en densidad. En cuanto al dominio, la mayoría de los sistemas opera en entornos acotados: un curso, una disciplina o un conjunto reducido de palabras clave de prueba; esto limita drásticamente su generalización (Gunarathne et al., 2018; Liu & Zhan, 2025). Adicionalmente, la falta de validación experimental completa constituye un vacío crítico: Dong et al. (2023) admiten explícitamente que el algoritmo central de recomendación de rutas no está implementado y se delega al trabajo futuro, mientras que Chen et al. (2023) no reportan evaluación con usuarios reales. Finalmente, las métricas empleadas en los estudios que sí evalúan formalmente presentan sus propias restricciones: Lissandrini et al. (2025) señalan que sus indicadores de calidad no consideran similitud semántica, lo que puede penalizar respuestas correctas semánticamente equivalentes a las de referencia. En síntesis, la evidencia disponible apunta a un potencial pedagógico prometedor de estas interfaces, pero la ausencia de evaluaciones controladas, a escala y con métricas de aprendizaje reales constituye el vacío más significativo que la investigación futura deberá abordar.

7. ## **Conclusiones** {#conclusiones}

El análisis de la literatura revisada permite concluir que la comunidad investigadora ha alcanzado un nivel de madurez razonable en la representación formal del conocimiento curricular mediante ontologías. Los trabajos examinados demuestran que es posible modelar con rigor conceptos, competencias, resultados de aprendizaje y relaciones pedagógicas mediante OWL y tecnologías de la Web Semántica (Wang et al., 2019; Barron et al., 2026; Tsidylo & Kozibroda, 2024). Sin embargo, este avance en la representación no se ha trasladado de forma equivalente a la automatización de la construcción del grafo. La ingesta de contenido educativo heterogéneo (sílabos, libros de texto, diapositivas y materiales multimodales) continúa siendo un cuello de botella crítico: los sistemas más establecidos dependen de anotación manual intensiva o de modelos supervisados entrenados sobre corpus de dominio cerrado (Pan et al., 2023; Liu, 2024), mientras que los enfoques más recientes basados en LLMs, aunque prometedores, acusan fragilidades en la extracción de relaciones abstractas y muestran alta sensibilidad a la calidad de los datos de preentrenamiento (Li et al., 2026; Yang et al., 2025; Xu & Che, 2025). La consecuencia directa es que ningún sistema del corpus ha demostrado ser capaz de construir y mantener un grafo de conocimiento curricular completo, actualizado y semánticamente validado a escala institucional real.

En el plano de la navegación y el descubrimiento, la evidencia sugiere que las interfaces basadas en grafos interactivos tienen el potencial de mejorar la orientación académica y la autonomía del estudiante de manera más efectiva que los métodos instruccionales tradicionales. Los resultados más sólidos provienen de entornos experimentales controlados donde la visualización de rutas de aprendizaje, la exploración jerárquica y la recomendación personalizada se combinan en una experiencia integrada (Liu & Zhan, 2025; Tytenko, 2025). No obstante, esta evidencia positiva está sistemáticamente acotada: los sistemas evaluados operan sobre un único curso o disciplina, utilizan datos sintéticos o de prueba, y no han sido sometidos a validaciones con grupos de usuarios amplios en condiciones ecológicamente válidas (Dong et al., 2023; Chen et al., 2023; Gunarathne et al., 2018). La usabilidad se deteriora a medida que el grafo crece en complejidad, y problemas como la desorientación en niveles profundos de navegación o la dificultad para localizar conceptos clave en estructuras densas permanecen sin solución sistemática (Tytenko, 2025; Dong et al., 2023). En consecuencia, el salto desde el prototipo experimental hacia un sistema de descubrimiento semántico funcional a escala curricular real no ha sido dado por ningún trabajo del corpus.

La síntesis de los tres ejes de análisis permite identificar con precisión el vacío de investigación que justifica la presente propuesta. No existe, en la literatura revisada, un sistema que integre de forma cohesionada y operativa los tres componentes que la evidencia señala como necesarios: una ontología curricular formalmente alineada con un estándar disciplinar internacional de amplia adopción (como ACM/IEEE CC2020 o CS2023), un pipeline de ingesta automatizada capaz de procesar documentos curriculares heterogéneos a escala mediante LLMs con control de calidad semántico, y una interfaz de descubrimiento que traduzca esa representación formal en mecanismos de navegación y recomendación efectivos para el estudiante autodirigido. Los trabajos orientados a la representación ontológica carecen de automatización y de capa de interacción (Wang et al., 2019; Oprea, 2020); los sistemas de construcción automática de grafos priorizan la ingesta sobre la calidad semántica y la interoperabilidad (Li et al., 2023; Liu et al., 2026); y las interfaces de navegación operan sobre grafos de cobertura restringida sin ancla en estándares curriculares reconocidos (Li et al., 2019; Dong et al., 2023). Este triple vacío de formalización estándar, automatización escalable y validación pedagógica integrada constituye la brecha que el sistema de gestión del conocimiento (KMS) propuesto en esta investigación busca cerrar, ofreciendo al estudiante universitario de Ciencias de la Computación un entorno coherente para comprender, navegar y planificar su trayectoria de aprendizaje con base en una representación curricular formalmente fundamentada.

4. # **Modelo del dominio del conocimiento de Ingeniería Informática** {#modelo-del-dominio-del-conocimiento-de-ingeniería-informática}

   1. ## **Introducción** {#introducción-2}

Este capítulo presenta el resultado central de este entregable: el modelo ontológico formal del dominio (R1), primer componente del objetivo específico O1. Es el esquema conceptual sobre el que se asienta el resto del sistema, ya construido y validado. La exposición plantea el resultado y lo vincula con su objetivo, describe la estructura del modelo (sus clases, las relaciones tipadas que lo articulan y las restricciones lógicas que gobiernan su uso) y detalla la estrategia con que se valida su construcción, por revisión de un experto y por verificación automática de consistencia. El poblamiento de ese esquema, tanto la capa de referencia curada desde el estándar CS2023 como el contenido institucional, corresponde a resultados posteriores del proyecto.

2. ## **Modelo ontológico formal del dominio de Ingeniería Informática** {#modelo-ontológico-formal-del-dominio-de-ingeniería-informática}

   1. ### **Introducción** {#introducción-3}

El primer resultado (R1) es el modelo ontológico formal que define el esquema conceptual (T-Box) del dominio: sus clases, las relaciones semánticas tipadas entre ellas y las restricciones lógicas que gobiernan su uso. Responde al primer objetivo: modelar el dominio mediante una ontología formal, al fijar la estructura sobre la cual el sistema representa cursos, conceptos, temas, áreas de conocimiento y recursos, y las dependencias entre ellos. Es importante precisar el alcance de este resultado: R1 es el esquema, no su contenido. Su poblamiento, tanto la capa de referencia curada desde el estándar como el contenido institucional extraído, corresponde a resultados posteriores.

El modelo se construyó aplicando la metodología Ontology Development 101 (Noy & McGuinness, 2001), adaptada al dominio educativo, y se validó por dos vías: la revisión de un experto en Ingeniería de Conocimiento y la verificación automática de consistencia lógica con el razonador HermiT. La especificación completa de la ontología se encuentra en el Anexo G y el registro razonado de las decisiones de diseño en el Anexo I. La estructura que se presenta a continuación resulta de los pasos de definición de clases, propiedades y facetas de esa metodología.

2. ### **Desarrollo: estructura del modelo** {#desarrollo:-estructura-del-modelo}

El desarrollo inició con la delimitación del dominio a las áreas de Ciencias de la Computación e Ingeniería de Software y de un conjunto de preguntas de competencia que el modelo debe poder responder: qué conocimientos preceden a un concepto, a qué unidad y área pertenece, qué recursos lo tratan, entre otras. Como punto de partida estructural se reutilizó el metamodelo curricular de Barron et al. (2026), alineado con el estándar CS2023. Sobre esa base se definieron las clases, las propiedades y las restricciones del esquema.

El modelo adopta una T-Box minimalista: solo las categorías estructurales del dominio se representan como clases, mientras que las entidades concretas (un área, un curso o un concepto particular) son instancias. Esta decisión mantiene el esquema estable y traslada el volumen del dominio a la capa de instancias, más eficiente de poblar y de consultar. Se definen ocho clases: una superclase abstracta, Elemento de Conocimiento, que agrupa los cuatro niveles del dominio (Área de Conocimiento, Unidad de Conocimiento, Tema y Concepto) y tres clases para los recursos y su empaquetamiento: Curso, Recurso de Aprendizaje y Tipo de Recurso.

La decisión estructural central es que la cadena de cuatro niveles no es una jerarquía de subsunción sino una partonomía: una unidad de conocimiento no es un tipo de área, sino una parte de ella. Dado que las entidades concretas son instancias, la relación entre ellas es una propiedad entre individuos y no una relación entre clases. En consecuencia, el árbol de clases es plano (las cuatro subclases dependen directamente de la superclase abstracta y son disjuntas entre sí) y la profundidad del dominio se expresa mediante relaciones, no mediante anidamiento de clases.

Sobre esa base, el modelo define las propiedades de objeto bajo un principio de economía: se afirman únicamente los hechos atómicos y los agregados se derivan por consulta. La composición se modela como una relación transitiva de tipo "parte de", con sub-relaciones simples para cada nivel; el prerrequisito se afirma solo entre conceptos, de modo que los prerrequisitos a nivel de tema, curso o área se infieren en lugar de almacenarse. Dos relaciones entre curso y concepto (los conceptos que un curso enseña y los que asume como entrada) permiten inferir el prerrequisito conceptual entre cursos, que tampoco se almacena. El esquema se completa con la especialización entre conceptos, la relación que vincula un recurso con aquello de lo que trata, el tipo de recurso y la procedencia que registra la fuente de cada nodo.

Las restricciones lógicas son las que sostienen la integridad del esquema. La superclase abstracta (Elemento de Conocimiento) se declara como la unión disjunta de sus cuatro subclases, lo que le da su carácter no instanciable y vuelve mutuamente excluyentes los cuatro niveles; la pertenencia de una unidad de conocimiento a su área es funcional; y un invariante de cuatro niveles obliga a que todo concepto pertenezca a un tema, todo tema a una unidad y toda unidad a un área. El comportamiento de estas restricciones bajo razonamiento automático se detalla en la validación; la especificación completa de clases, propiedades y axiomas figura en el Anexo G y su justificación razonada en el Anexo I (decisiones de diseño).

3. ### **Validación** {#validación}

La validación de R1 sigue una estrategia dual, con una herramienta por régimen.

**Consistencia lógica (HermiT)**

Una vez implementada en OWL con Protégé, la ontología se sometió a razonamiento automático con HermiT, que verifica la ausencia de clases insatisfacibles y la correcta inferencia de la jerarquía. Gracias a los axiomas de disyunción y a los dominios y rangos precisos de las propiedades, HermiT detecta situaciones como un individuo clasificado a la vez como Topic y Concept, una unidad de conocimiento enlazada a dos áreas distintas, o una arista de composición de nivel equivocado.

Límite de mundo abierto: HermiT detecta contradicciones, no ausencias. El invariante de cuatro niveles (todo concepto pertenece al menos a un tema; todo tema, al menos a una unidad; toda unidad, al menos a un área) se afirma mediante axiomas existenciales acompañados de una anotación que advierte que, bajo el supuesto de mundo abierto, su incumplimiento no es detectado por el razonador. La verificación de completitud (nodos huérfanos, recursos sin enlace, instancias sin procedencia) se realiza mediante consultas de integridad en una etapa posterior del proyecto, no en R1.

**Validación de experto**

La T-Box y el conjunto de decisiones de diseño que la sustentan fueron revisados y aprobados por el experto en Ingeniería del Conocimiento y asesor, Andrés Melgar; el registro de esa validación se adjunta como evidencia en el Anexo H.

**Indicador**

El modelo define ocho clases y diecisiete propiedades de objeto (incluyendo las inversas declaradas), por encima del piso de al menos cinco clases y tres tipos de relación que se desprenden de las preguntas de competencia.

4. ### **Relevancia para el proyecto**

Aunque R1 no es todavía un sistema en funcionamiento, es la pieza que condiciona todo lo que viene. El modelo fija el contrato estructural que el resto del proyecto debe respetar: la capa de referencia (R2) se cura contra sus clases, el pipeline de ingesta puebla instancias conformes a sus restricciones y el mecanismo de navegación recorre las relaciones que aquí se definen. Tres decisiones del modelo concentran ese valor: 

- La composición en cuatro niveles permite consultar a qué unidad o área pertenece cualquier contenido sin almacenar esa información de forma redundante.   
- La afirmación del prerrequisito únicamente entre conceptos, junto con las dos relaciones que distinguen lo que un curso enseña de lo que asume como entrada, hace que el prerrequisito conceptual entre cursos sea inferible en lugar de declararse a mano.   
- La procedencia registrada en cada nodo mantiene trazable el origen de la información, condición de la confiabilidad que el sistema promete. 

En conjunto, R1 es lo que vuelve operable el planteamiento del proyecto: tratar el currículo como un activo de información formalizable y consultable, y no como un conjunto de documentos dispersos.

3. ## **Capa de referencia curada desde el estándar CS2023** {#capa-de-referencia-curada-desde-el-estándar-cs2023}

El segundo resultado del primer objetivo específico consiste en poblar el modelo con una capa de referencia: el conjunto de instancias que fija el vocabulario estructural del dominio antes de incorporar contenido institucional. Esta capa se cura exclusivamente desde el estándar CS2023 y llega hasta el nivel de unidad de conocimiento, conforme a la decisión de diseño que establece ese estándar como fuente única del backbone.

La curación produjo diecisiete áreas de conocimiento y 162 unidades, cotejadas contra el índice canónico del estándar. Cada instancia registra su nombre legible, su pertenencia de capa (que distingue lo curado de lo que poblará posteriormente el pipeline de ingesta) y su procedencia, que la vincula al documento del que se derivó. Cada unidad se enlaza además a su área mediante la propiedad de pertenencia correspondiente, que es funcional: una unidad pertenece a exactamente un área.

La carga se realizó de forma programática, mediante un script que transforma la tabla curada en instancias del modelo. Esta decisión responde a tres criterios: reproducibilidad (el backbone puede regenerarse íntegramente desde la tabla fuente), trazabilidad de la curación, y eliminación del error de transcripción manual que introduciría el poblamiento a mano de más de un centenar de individuos.

La verificación operó en tres niveles. Primero, la correspondencia con el estándar: se contrastaron los conteos de áreas y unidades y se verificó por muestreo la asignación de unidades a sus áreas. Segundo, la consistencia lógica: se ejecutó el razonador sobre el modelo y la capa de referencia en conjunto, sin detectar inconsistencias ni clases insatisfacibles. Para que esta verificación sea efectiva fue necesario declarar explícitamente la identidad distinta entre todas las instancias del backbone, pues el supuesto de mundo abierto de la lógica descriptiva no asume nombres únicos: sin esa declaración, un enlace erróneo de una unidad a dos áreas distintas llevaría al razonador a inferir que ambas áreas son la misma entidad en lugar de señalar la contradicción. Tercero, la revisión del asesor especialista.

Conviene precisar el alcance de esta verificación. El razonador garantiza que la capa de referencia no contiene contradicciones lógicas, no que reproduzca fielmente el estándar: la fidelidad al documento fuente se establece por cotejo documental y revisión experta, no por inferencia automática. Las clases de tema y concepto permanecen sin instanciar en esta capa; sus instancias provienen íntegramente del material institucional y se incorporan en el resultado correspondiente al módulo de ingesta.

5. # **Conclusiones y trabajos futuros** {#conclusiones-y-trabajos-futuros}

   1. ## **Conclusiones** {#conclusiones-1}

   2. ## **Trabajos futuros** {#trabajos-futuros}

# **Referencias**

Alavi, M., & Leidner, D. E. (2001). *Review*: Knowledge Management and Knowledge Management Systems: Conceptual Foundations And Research Issues1,2. *MIS Quarterly*, *25*(1), 107-136. [https://doi.org/10.2307/3250961](https://doi.org/10.2307/3250961)

Angles, R., Thakkar, H., & Tomaszuk, D. (2019). *RDF and Property Graphs Interoperability: Status and Issues*.

Barron, J., Feldhausen, R., & Bean, N. H. (2026). *Towards a Computer Science Topics Ontology*. 101-106. Scopus. [https://doi.org/10.1145/3770762.3772566](https://doi.org/10.1145/3770762.3772566)

Bin, Q., Zuhairi, M. F., Morcos, J., & Zhengqiu, L. (2025). *A Ontology Construction Method of Course Knowledge Graph Based on Dependency of Knowledge Points*. Scopus. Proceedings of the 2025 19th International Conference on Ubiquitous Information Management and Communication, IMCOM 2025\. [https://doi.org/10.1109/IMCOM64595.2025.10857583](https://doi.org/10.1109/IMCOM64595.2025.10857583)

Brown, S. (s. f.). *Home*. C4 Model. Recuperado 15 de mayo de 2026, de [https://c4model.com/](https://c4model.com/)

Buitrago, M., & Chiappe, A. (2019). Representation of knowledge in digital educational environments: A systematic review of literature. *Australasian Journal of Educational Technology*, *35*(4). [https://doi.org/10.14742/ajet.4041](https://doi.org/10.14742/ajet.4041)

Cc2020 Task Force. (2020). *Computing Curricula 2020: Paradigms for Global Computing Education*. ACM. [https://doi.org/10.1145/3467967](https://doi.org/10.1145/3467967)

Chen, C., Zhu, S., Tao, Q., Wu, Q., & Shi, Y. (2023). *Design and Development of a Knowledge Service Platform in the Field of Computer Science: Knowledge Service Platform in Computer Science: Design and Development*. 57-65. Scopus. [https://doi.org/10.1145/3606094.3606108](https://doi.org/10.1145/3606094.3606108)

Chen, X., Yin, C., Chen, H., Rong, W., Ouyang, Y., & Chai, Y. (2024). *Course Recommendation System Based on Course Knowledge Graph Generated by Large Language Models*. Scopus. 2024 IEEE International Conference on Teaching, Assessment and Learning for Engineering, TALE 2024 \- Proceedings. [https://doi.org/10.1109/TALE62452.2024.10834324](https://doi.org/10.1109/TALE62452.2024.10834324)

Dong, J., Li, W., Wang, Y., Li, Q., Baciu, G., Cao, J., Huang, X., Li, R. C., & Ng, P. H. F. (2023). *Gradual Study Advising with Course Knowledge Graphs*. *14409 LNCS*, 125-138. Scopus. [https://doi.org/10.1007/978-981-99-8385-8\_10](https://doi.org/10.1007/978-981-99-8385-8_10)

Ehrlinger, L., & Wöß, W. (2016). *Towards a Definition of Knowledge Graphs*. International Conference on Semantic Systems. [https://www.semanticscholar.org/paper/Towards-a-Definition-of-Knowledge-Graphs-Ehrlinger-W%C3%B6%C3%9F/b18e4272a7b9fa2e1c970d258ab5ea99ed5e2284](https://www.semanticscholar.org/paper/Towards-a-Definition-of-Knowledge-Graphs-Ehrlinger-W%C3%B6%C3%9F/b18e4272a7b9fa2e1c970d258ab5ea99ed5e2284)

Garrison, D. (1997). Self-Directed Learning: Toward a Comprehensive Model. *Adult Education Quarterly \- ADULT EDUC QUART*, *48*, 18-33. [https://doi.org/10.1177/074171369704800103](https://doi.org/10.1177/074171369704800103)

Giacomo, G. D., & Lenzerini, M. (1996). *TBox and ABox Reasoning in Expressive Description Logics*.

*GitHub*. (s. f.). GitHub Docs. Recuperado 15 de mayo de 2026, de [https://docs-internal.github.com/es](https://docs-internal.github.com/es)

Glimm, B., Horrocks, I., Motik, B., Stoilos, G., & Wang, Z. (2014). HermiT: An OWL 2 Reasoner. *Journal of Automated Reasoning*, *53*(3), 245-269. [https://doi.org/10.1007/s10817-014-9305-1](https://doi.org/10.1007/s10817-014-9305-1)

Gruber, T. R. (1993). A translation approach to portable ontology specifications. *Knowledge Acquisition*, *5*(2), 199-220. [https://doi.org/10.1006/knac.1993.1008](https://doi.org/10.1006/knac.1993.1008)

Gunarathne, W. K. T. M., Chootong, C., Sommool, W., Ochirbat, A., Chen, Y.-C., Reisman, S., & Shih, T. K. (2018). *Web-Based Learning Object Search Engine Solution Together with Data Visualization: The Case of MERLOT II*. *1*, 1026-1031. Scopus. [https://doi.org/10.1109/COMPSAC.2018.00179](https://doi.org/10.1109/COMPSAC.2018.00179)

Huang, J., Lai, F., Zheng, Z., Lai, R., Chen, X., Tian, J., & Zheng, Y. (2026). Design and Evaluation of a Question-Answering System Based on Knowledge Graph-Augmented Large Language Models in K–12 Artificial Intelligence Curriculum. *Applied Sciences*, *16*(7), 3552\. [https://doi.org/10.3390/app16073552](https://doi.org/10.3390/app16073552)

Kitchenham, B., & Charters, S. (2007). *Guidelines for performing Systematic Literature Reviews in Software Engineering*. *2*.

Kumar, A. N., Raj, R. K., Aly, S. G., Anderson, M. D., Becker, B. A., Blumenthal, R. L., Eaton, E., Epstein, S. L., Goldweber, M., Jalote, P., Lea, D., Oudshoorn, M., Pias, M., Reiser, S., Servin, C., Simha, R., Winters, T., & Xiang, Q. (2024). *Computer Science Curricula 2023*. ACM. [https://doi.org/10.1145/3664191](https://doi.org/10.1145/3664191)

*LangChain: Observe, Evaluate, and Deploy Reliable AI Agents*. (s. f.). Recuperado 15 de mayo de 2026, de [https://www.langchain.com/](https://www.langchain.com/)

Li, S., Xiao, Y., Li, J., & Li, Y. (2026). *Automatic Construction System for Curriculum Knowledge Graphs Based on Large Language Models LLM-Based Curriculum Map Construction*. 252-257. Scopus. [https://doi.org/10.1145/3785987.3786028](https://doi.org/10.1145/3785987.3786028)

Li, Y., Qu, S., Shen, J., Min, S., & Yu, Z. (2024). Curriculum-Driven Edubot: A Framework for Developing Language Learning Chatbots through Synthesizing Conversational Data. En T. Kawahara, V. Demberg, S. Ultes, K. Inoue, S. Mehri, D. Howcroft, & K. Komatani (Eds.), *Proceedings of the 25th Annual Meeting of the Special Interest Group on Discourse and Dialogue* (pp. 400-419). Association for Computational Linguistics. [https://doi.org/10.18653/v1/2024.sigdial-1.35](https://doi.org/10.18653/v1/2024.sigdial-1.35)

Li, Y., Zhao, J., Yang, L., & Zhang, Y. (2019). *Construction, visualization and application of knowledge graph of computer science major*. 43-47. Scopus. [https://doi.org/10.1145/3322134.3322153](https://doi.org/10.1145/3322134.3322153)

Li, Z., Cheng, L., Zhang, C., Zhu, X., & Zhao, H. (2023). *Multi-Source Education Knowledge Graph Construction and Fusion for College Curricula*. 359-363. Scopus. [https://doi.org/10.1109/ICALT58122.2023.00111](https://doi.org/10.1109/ICALT58122.2023.00111)

Li, Z., Wang, Z., Wang, W., Hung, K., Xie, H., & Wang, F. L. (2025). Retrieval-augmented generation for educational application: A systematic survey. *Computers and Education: Artificial Intelligence*, *8*, 100417\. [https://doi.org/10.1016/j.caeai.2025.100417](https://doi.org/10.1016/j.caeai.2025.100417)

Lissandrini, M., Prando, G., & Silvello, G. (2025). The ESW of Wikidata: Exploratory search workflows on Knowledge Graphs. *Journal of Web Semantics*, *85*. Scopus. [https://doi.org/10.1016/j.websem.2024.100860](https://doi.org/10.1016/j.websem.2024.100860)

Liu, L. (2024). *Construction of Programming Knowledge Graph Based on Student Knowledge Needs*. 120-123. Scopus. [https://doi.org/10.1109/ICCECE61317.2024.10504170](https://doi.org/10.1109/ICCECE61317.2024.10504170)

Liu, P., & Zhan, C. (2025). *Research on Visual Learning Platform for Database Principles Knowledge Points Integrating Knowledge Graph and Deep Learning*. 276-280. Scopus. [https://doi.org/10.1145/3768421.3768468](https://doi.org/10.1145/3768421.3768468)

Liu, Y., Zuo, Q., Zhang, S., Li, Y., Wang, C., Han, F., & Cheng, X. (2026). *Research on Triple Joint Extraction Method of Knowledge Graph for Education Domain*. 134-139. Scopus. [https://doi.org/10.1145/3785987.3786009](https://doi.org/10.1145/3785987.3786009)

Millman, K., & Aivazis, M. (2011). Python for Scientists and Engineers. *Computing in Science & Engineering*, *13*, 9-12. [https://doi.org/10.1109/MCSE.2011.36](https://doi.org/10.1109/MCSE.2011.36)

National Research Council. (2000). *How People Learn: Brain, Mind, Experience, and School: Expanded Edition*. National Academies Press.

*Neo4j documentation*. (s. f.). Neo4j Graph Data Platform. Recuperado 15 de mayo de 2026, de [https://neo4j.com/docs/](https://neo4j.com/docs/)

Nguyen, T., Vu, N., & Ly, B. (2022). *An approach to constructing a graph data repository for course recommendation based on IT career goals in the context of big data*. 301-308. Scopus. [https://doi.org/10.1109/BigData55660.2022.10020436](https://doi.org/10.1109/BigData55660.2022.10020436)

Nygard, M. (2011, noviembre 15). *Documenting Architecture Decisions*. Cognitect.Com. [https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

Oprea, M. (2020). *An Educational Ontology for Formal Languages and Compilers*. 54-60. Scopus. [https://www.scopus.com/pages/publications/85103847070?origin=resultslist](https://www.scopus.com/pages/publications/85103847070?origin=resultslist)

*OWL 2 Web Ontology Language Document Overview 2nd Edition*. (2012). [https://www.w3.org/TR/owl2-overview/](https://www.w3.org/TR/owl2-overview/)

Pan, J., Liu, J., Wei, D., Zhuang, J., Qiu, S., & Du, J. (2023). *Knowledge Graph for University Course Construction Based on Gated Graph Attention Networks*. 60-65. Scopus. [https://doi.org/10.1109/MLCR61158.2023.00021](https://doi.org/10.1109/MLCR61158.2023.00021)

*Protégé*. (s. f.). Recuperado 15 de mayo de 2026, de [https://protege.stanford.edu/](https://protege.stanford.edu/)

Pydantic. (2026). *Pydantic/pydantic-ai* \[Python\]. [https://github.com/pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) (Obra original publicada en 2024\)

Ramírez, S. (s. f.). *FastAPI*. Recuperado 15 de mayo de 2026, de [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)

*RDF 1.1 Concepts and Abstract Syntax*. (2014). [https://www.w3.org/TR/rdf11-concepts/](https://www.w3.org/TR/rdf11-concepts/)

Singhal, A. (2012, mayo 16). *Introducing the Knowledge Graph: Things, not strings*. Google. [https://blog.google/products-and-platforms/products/search/introducing-knowledge-graph-things-not/](https://blog.google/products-and-platforms/products/search/introducing-knowledge-graph-things-not/)

Tsidylo, I. M., & Kozibroda, S. V. (2024). *Ontology-based representation and design of subject domains for Computer Science education*. *3820*, 56-62. Scopus. [https://www.scopus.com/pages/publications/85209346746?origin=resultslist](https://www.scopus.com/pages/publications/85209346746?origin=resultslist)

Tytenko, S. (2025). *AI-driven Interactive Hierarchical Concept Maps for Digital Learning Environments and Intelligent Textbooks*. *4010*, 3-16. Scopus. [https://www.scopus.com/pages/publications/105013470614?origin=resultslist](https://www.scopus.com/pages/publications/105013470614?origin=resultslist)

Wang, C. (2025a). *Study on Multi-source Heterogeneous Data Fusion and Knowledge Graph Construction Techniques in Higher Education Institutions*. 506-510. Scopus. [https://doi.org/10.1145/3765325.3765409](https://doi.org/10.1145/3765325.3765409)

Wang, C. (2025b). *Study on Multi-source Heterogeneous Data Fusion and Knowledge Graph Construction Techniques in Higher Education Institutions*. 506-510. Scopus. [https://doi.org/10.1145/3765325.3765409](https://doi.org/10.1145/3765325.3765409)

Wang, Y., Wang, Z., Hu, X., Bai, T., Yang, S., & Huang, L. (2019). *A Courses Ontology System for Computer Science Education*. 251-254. Scopus. [https://doi.org/10.1109/CSEI47661.2019.8938930](https://doi.org/10.1109/CSEI47661.2019.8938930)

Xu, J., & Che, M. (2025). *LLM-Powered Construction of Course Knowledge-Competency Graphs*. 66-73. Scopus. [https://doi.org/10.1145/3766557.3766569](https://doi.org/10.1145/3766557.3766569)

Yang, M., Diao, M., Luo, J., Shen, W., & Zhang, C. (2025). GLM-4-Based Method for Automatic Construction of Content Graph. *IEEE Access*, *13*, 197300-197311. Scopus. [https://doi.org/10.1109/ACCESS.2025.3548590](https://doi.org/10.1109/ACCESS.2025.3548590)

# **Anexos**

# **Anexo A. Formulario de extracción de la pregunta 1 de investigación**

| Título de la publicación | Autor | Año | ¿Qué entidades modela? | ¿Qué tecnología de representación usa? | ¿Cómo se alinea a un estándar disciplinar? | ¿Qué limitaciones declara el autor? |
| :---- | :---- | ----- | :---- | :---- | :---- | :---- |
| A Courses Ontology System for Computer Science Education | Wang, Y., Wang, Z., Hu, X., Bai, T., Yang, S., & Huang, L. | 2019 | El sistema modela cursos (courses), unidades (units) y puntos de conocimiento (knowledge points). Estos se organizan en una estructura jerárquica donde los cursos incluyen unidades y estas, a su vez, contienen puntos de conocimiento. También se consideran términos de computación y diversas relaciones entre ellos, como liderazgo (leading), seguimiento (trailing), inclusión (inclusion) y propiedad (ownership) | Utiliza OWL (Web Ontology Language), implementado específicamente a través de la Protégé OWL API y el framework Jena para la construcción automática de la ontología. El sistema completo está desarrollado en Java. | El sistema no menciona alineación con estándares internacionales como CC2020, ACM o IEEE. En su lugar, la ontología se construye a partir de los catálogos de cursos de veinte universidades famosas de China y sitios web de educación en red. | El autor menciona que existen cursos individuales donde no es posible verificar la relevancia al seleccionar pares de palabras clave relacionados. Asimismo, se señala la necesidad de expandir la cobertura de los datos para mejorar el rendimiento y la integridad del sistema. No se mencionan explícitamente limitaciones de escalabilidad o falta de validación formal en los fragmentos analizados. |
| A Ontology Construction Method of Course Knowledge Graph Based on Dependency of Knowledge Points | Bin, Q., Zuhairi, M. F., Morcos, J., & Zhengqiu, L. | 2025 | Modela principalmente puntos de conocimiento (knowledge points), conceptos, y cursos (específicamente el curso "Desarrollo de Aplicaciones Móviles"). También integra atributos relacionados con el estudiante, como su nivel cognitivo y su grado de maestría sobre cada punto de conocimiento | ¿Qué tecnología de representación usa?: Utiliza OWL (Web Ontology Language) como lenguaje de representación y la herramienta Protégé para el diseño de la jerarquía de la ontología. Para la recolección de datos, emplea scripts en Python con las librerías urllib.request y bs4 | El documento indica que la estructura jerárquica y el alcance de la ontología se definen basándose específicamente en el sílabo del curso (course syllabus), libros de texto y la validación de expertos en la materia, sin mencionar alineación con estándares externos. | Escalabilidad y rendimiento: El autor declara que la escala actual del grafo es relativamente pequeña y advierte que, al construir grafos a gran escala, podrían surgir desafíos de rendimiento, mayor consumo de recursos computacionales y una posible disminución en la eficiencia de las consultas.Carga de trabajo: El proceso de búsqueda manual y extracción de conceptos a partir de libros de texto implica una carga de trabajo manual sustancial y laboriosa. Complejidad de relaciones: Aunque el modelo es flexible, el autor señala que otros cursos con relaciones más intrincadas podrían requerir modificar o dividir las categorías de relación actuales. |
| An Educational Ontology for Formal Languages and Compilers | Oprea, M. | 2020 | Modela conceptos básicos y avanzados de los dominios de Lenguajes Formales, Compiladores y Lenguajes de Programación, junto con sus relaciones jerárquicas y semánticas. | Utiliza el formato OWL (Web Ontology Language) y fue desarrollada con la herramienta Protégé 4.3. | Propio. Se basa en las especificaciones y recursos (libros de texto y notas de clase) del curso de la Universidad Petroleum-Gas de Ploiesti. | Se presenta como un prototipo diseñado para una primera etapa de uso como vocabulario. El autor indica que requiere ser extendida con más conceptos en trabajos futuros. |
| Ontology-based representation and design of subject domains for Computer Science education | Tsidylo, I. M., & Kozibroda, S. V. | 2024 | DataDomain, Competencias (universales, profesionales, científicas, instrumentales, socio-personales), Conceptos, Habilidades, Capacidades, Estudiante, Recursos Educativos (Curso, Lección, Lab, Tarea, Test) y Lenguaje. | OWL, RDF y el entorno Protégé. | Propio (basado en el currículo de la disciplina y la matriz de competencias específica) | No especificado (se enfoca en los beneficios experimentales y solo menciona trabajo futuro sobre integración en sistemas de tutoría) |
| Towards a Computer Science Topics Ontology | Barron, J., Feldhausen, R., & Bean, N. H. | 2026 | Knowledge Area (Área de conocimiento), Knowledge Unit (Unidad), Learning Outcomes (Resultados de aprendizaje), Topic (Tema), Subtopic, Skill Level (Nivel de habilidad), Competency Area, Programming Language, Lesson (Lección), Evaluation Criteria y Learning Goal | Estándares de la Web Semántica de la W3C (triples), OWL (vía Owlready2), SPARQL para consultas y Protégé | ACM Computer Science Curricula 2023 y la Taxonomía de Bloom revisada | Uso de datos sintéticos (placeholders) para lecciones y criterios de evaluación, cobertura limitada (enfocado solo en CS1 y el área de "Software Development Fundamentals") y falta de una definición para el proceso de evaluación de maestría de los estudiantes. |

# **Anexo B. Formulario de extracción de la pregunta 2 de investigación**

| Título de la publicación | Autor | Año | ¿Qué componentes tiene el sistema? | ¿Cómo se integra/ingesta el contenido? | ¿Qué tecnología de almacenamiento usa? | ¿Cómo expone el conocimiento (API, consulta, otro)? | ¿Qué limitaciones declara el autor? |
| :---- | :---- | ----- | :---- | :---- | :---- | :---- | :---- |
| An approach to constructing a graph data repository for course recommendation based on IT career goals in the context of big data | Nguyen, T., Vu, N., & Ly, B. | 2022 | Ingesta (Web Scraper, Competency Handler), Almacenamiento (Neo4j), UI (aplicación web con dashboards de gestión) y módulo de exportación | Scraping (vía framework Scrapy), NLP/Deep Learning (modelo BERT para reconocimiento de entidades \- NER) y filtrado Manual opcional por expertos. | Neo4j (bajo el modelo de datos Labeled Property Graph \- LPG) | UI (interfaz gráfica del sistema) y Exportación de datos en formatos JSON y CSV. (No se especifica una API o lenguaje de consulta para usuarios externos). | Necesidad de mejorar la precisión del componente de Deep Learning, requerimiento de integrar más plataformas de Big Data para aumentar el rendimiento y falta de determinación de los pesos (weights) en las propiedades de las relaciones |
| Automatic Construction System for Curriculum Knowledge Graphs Based on Large Language Models LLM-Based Curriculum Map Construction | Li, S., Xiao, Y., Li, J., & Li, Y. | 2026 | Marco de trabajo web Flask, motor de base de datos de grafos (Neo4j), base de datos relacional para usuarios (SQLite) y la API de DeepSeek Chat (LLM) | Procesamiento automático de documentos docx mediante LLM (DeepSeek), segmentación de documentos basada en optimización y algoritmos de extracción de entidades/relaciones basados en aprendizaje profundo. | Neo4j para el grafo de conocimiento y SQLite para la gestión de cuentas de usuario. | Visualización de mapas de conocimiento y funciones de recuperación inteligente a través de una interfaz web- | Capacidad limitada para reconocer conceptos abstractos, baja tasa de recuperación en relaciones ambiguas o dispersas entre capítulos, y alta sensibilidad a la calidad y cobertura de los datos de pre-entrenamiento del modelo. |
| Construction of Programming Knowledge Graph Based on Student Knowledge Needs | Liu, L. | 2024 | Ingesta (rastreadores/crawlers), Procesamiento (modelo BiLSTM+CRF para extracción), Almacenamiento (base de datos de grafos) y Consulta (lenguaje Cypher) | Scraping (vía crawlers de sitios como CSDN y Zhihu), NLP (identificación de entidades y relaciones con BiLSTM+CRF) y Manual (corrección de textos obtenidos de libros mediante reconocimiento de caracteres) | Neo4j | Consulta mediante el lenguaje Cypher y uso de la librería py2neo de Python.. | No especificado (el autor concluye que el sistema es efectivo y satisface las necesidades de los estudiantes sin detallar debilidades finales) |
| Course Recommendation System Based on Course Knowledge Graph Generated by Large Language Models | Chen, X., Yin, C., Chen, H., Rong, W., Ouyang, Y., & Chai, Y. ( | 2024 | Ingesta (rastreadores web/crawlers), módulo de Extracción de información (NLP/LLM) y un Módulo de recomendación (que integra BiLSTM, mecanismos de atención y MLP) | Scraping (mediante rastreadores a plataformas como MOOC de la Universidad de China y NetEase Cloud Classroom) , Reglas (para identificar relaciones de prerrequisitos) y LLM (uso de ChatGLM-6B para generar datos de entrenamiento y LlaMa para el reconocimiento de entidades) | No especificado (el documento describe la estructura como una red semántica de tripletas y utiliza técnicas de embedding como TransD, pero no menciona un software de base de datos específico). | A través de un Algoritmo de recomendación personalizada que genera puntuaciones para cursos sugeridos basándose en el historial del estudiante. | Cobertura limitada por falta de descripciones textuales en algunos cursos, escalabilidad y adaptabilidad limitadas de los métodos basados en reglas y un rendimiento en la métrica MRR@10 ligeramente inferior al de algunos modelos de referencia. |
| GLM-4-Based Method for Automatic Construction of Content Graph | Yang, M., Diao, M., Luo, J., Shen, W., & Zhang, C. | 2025 | Ingesta (importación de recursos no estructurados), Procesamiento (GLM-4, GQA), Almacenamiento (Neo4j) y UI/Visualización (integrado en la plataforma SuperStar) | LLM (uso de GLM-4 para análisis semántico y extracción de entidades), NLP (mecanismo de atención GQA para inferir relaciones) y Reglas (módulo de análisis lógico basado en reglas del dominio educativo) | Neo4j | Consulta (vía lenguaje Cypher) y Visualización interactiva para navegación de cursos y recomendaciones de rutas de aprendizaje. | Precisión inferior a la extracción manual experta y rendimiento relativamente bajo en la identificación de relaciones específicas de prerrequisitos y sucesores en comparación con otros tipos de entidades. |
| Knowledge Graph for University Course Construction Based on Gated Graph Attention Networks | Pan, J., Liu, J., Wei, D., Zhuang, J., Qiu, S., & Du, J. | 2023 | Ingesta (extractores de características BERT y GGAT, más etiquetador CRF), Almacenamiento (base de datos de grafos) y UI (módulo de visualización) | Reglas (para texto de libros y detalles), Deep Learning (modelo GGAT para extracción de entidades y relaciones) y Manual (anotación parcial para entrenamiento y diseño de ontología top-down) | Neo4j | Visualización interactiva (permitiendo navegación multidimensional y de niveles). (No menciona una API o lenguaje de consulta para el usuario final). | No especificado. (El autor se centra en demostrar la superioridad del modelo propuesto sobre métodos previos como CNN, LSTM y GCN). |
| LLM-Powered Construction of Course Knowledge-Competency Graphs | Xu, J., & Che, M. | 2025 | Ingesta (adquisición y limpieza de datos), Procesamiento (extracción de conocimiento y fusión de capas), Almacenamiento (base de datos de grafos) y Aplicación/Visualización. | LLM (uso de modelos como Qwen o DeepSeek mediante ingeniería de prompts), Reglas (para la fusión entre las capas de conocimiento y competencia) y Manual (validación experta de la ontología y selección docente de objetivos). | Neo4j | ¿Cómo expone el conocimiento?: Visualización de grafos multidimensionales (KWA) y soporte para sistemas de recomendación de rutas de aprendizaje y evaluación de competencias. | Dificultades en el control de granularidad (sobre-extracción), posibles inconsistencias en la extracción y falta de exhaustividad (Recall) en puntos de conocimiento fragmentados o con límites ambiguos. |
| Multi-Source Education Knowledge Graph Construction and Fusion for College Curricula | Li, Z., Cheng, L., Zhang, C., Zhu, X., & Zhao, H. | 2023 | Ingesta (extracción y limpieza), Almacenamiento (Neo4j), Fusión de grafos, UI/Visualización y un módulo de Estadísticas (cálculo de relevancia de currículo y ranking de conceptos) | NLP (Reconocimiento de Entidades Nombradas \- NER), Reglas (expresiones regulares para dividir documentos), Deep Learning (modelo de corrección de errores lingüísticos) y conversión automática de libros de texto y diapositivas. | Neo4j | UI (búsqueda de conceptos, visualización interactiva de nodos/atributos) y visualización de estadísticas auxiliares (popularidad de conceptos y correlación entre cursos) | Errores en la conversión de texto, problemas de codificación de formato, anomalías en entidades (como fórmulas o símbolos incompletos) y limitaciones algorítmicas de los modelos NER y expresiones regulares. |
| Research on Triple Joint Extraction Method of Knowledge Graph for Education Domain | Liu, Y., Zuo, Q., Zhang, S., Li, Y., Wang, C., Han, F., & Cheng, X. | 2026 | El framework comprende tres módulos principales: un módulo de recolección de corpus, un módulo de extracción de conocimiento (reconocimiento de entidades, relaciones y atributos) y un módulo de corrección (desambiguación semántica, fusión de conocimiento y evaluación de calidad) | Se basa en la recolección de diversos tipos de datos (materiales de enseñanza, puntos de conocimiento y datos de docentes/alumnos). La extracción se realiza mediante un modelo de extracción conjunta basado en redes neuronales múltiples que combina BERT, BiGRU y CNN. También menciona la construcción de un dataset mediante anotación manual de recursos educativos | No especificado (el documento describe el proceso para generar el grafo y muestra un repositorio de datos en su arquitectura, pero no menciona un software específico) | No especificado. El autor indica que el sistema proporcionará soporte técnico para búsqueda y sistemas de preguntas y respuestas (Q\&A), pero no especifica una tecnología de exposición (como API o lenguajes de consulta) para el usuario final | El dominio educativo presenta una alta complejidad por el anidamiento de palabras (word nesting) y abundancia de términos profesionales . Además, señala la escasez de datasets públicos de extracción conjunta para este dominio y la dificultad de la anotación manual |
| Study on Multi-source Heterogeneous Data Fusion and Knowledge Graph Construction Techniques in Higher Education Institutions | Wang, C. | 2025 | Ingesta (herramientas ETL, adquisición, preprocesamiento), Procesamiento (alineación de entidades, extracción de relaciones), Almacenamiento (gestión de grafos), Interfaz de servicio (arquitectura de microservicios) y Visualización (framework ECharts). | ETL (desde bases de datos, archivos de texto y hojas de cálculo), NLP/Deep Learning (modelos BERT, word2vec y Bi-LSTM con atención), Supervisión remota, Reglas (expresiones regulares) y Manual (etiquetado previo de datos para entrenamiento). | Neo4j (para la gestión eficiente del grafo) y tripletas RDF (para el almacenamiento de conocimiento). Utiliza además un clúster de Redis como capa de caché. | Consultas SPARQL, RESTful APIs y Visualización interactiva (implementando 12 métodos de visualización). | El autor indica que el trabajo futuro debe centrarse en mejorar las capacidades de razonamiento de conocimiento, incorporar algoritmos de aprendizaje automático más avanzados y desarrollar un análisis semántico más sofisticado para soportar la toma de decisiones complejas. |

# **Anexo C. Formulario de extracción de la pregunta 3 de investigación**

| Título de la publicación | Autor | Año | ¿Qué tipo de interfaz de exploración propone? | ¿Qué funcionalidades de navegación implementa? | ¿Cómo evalúa la efectividad? | ¿Qué resultado reporta? | ¿Qué limitaciones declara el autor? |
| :---- | :---- | ----- | :---- | :---- | :---- | :---- | :---- |
| Ejemplo |  |  | Visual/grafo, conversacional, lista, mixta, otros | Rutas de aprendizaje, filtros, búsqueda semántica, recomendación, otros | Experimento con usuarios, expertos, métricas automáticas, ninguna, otros | Mejora en orientación, satisfacción, tiempo, otros | Dominio acotado, sin validación, usabilidad limitada, etc. |
| AI-driven Interactive Hierarchical Concept Maps for Digital Learning Environments and Intelligent Textbooks | Tytenko, S. | 2025 | Mapas de conceptos interactivos con nodos y enlaces jerárquicos. | Navegación jerárquica drill-down (permite expandir nodos para ver subtemas), drill-down infinito (generación dinámica de sub-mapas mediante IA), panel de información contextual (detalles del concepto al hacer clic) y exploración autodirigida. . | (Estudiantes universitarios de ingeniería de software y ciencia de datos). Mediante cuestionarios y encuestas de satisfacción | Satisfacción elevada (8.91/10), percepción de efectividad para aprender nuevos contenidos (8.31/10), mayor compromiso/disfrute (91.4%) y utilidad confirmada del 100% para la navegación en mapas anidados. Los estudiantes destacaron la mejora en la claridad de la estructura visual y las relaciones entre temas. | Desorientación del usuario en niveles profundos de navegación, deriva del tema (topic drift) por parte del LLM, inconsistencias estructurales entre mapas padre e hijo, dependencia de percepciones subjetivas en lugar de métricas de rendimiento objetivo y el tiempo requerido para el refinamiento manual por expertos. |
| Construction, visualization and application of knowledge graph of computer science major | Li, Y., Zhao, J., Yang, L., & Zhang, Y. | 2019 | Mixta. Ofrece visualizaciones de grafos interactivos en 2D y 3D, una barra de navegación para entradas y una interfaz para recursos multimedia como videos. | Rutas de aprendizaje (cálculo del camino más corto entre dos puntos), búsqueda de nodos, resaltado de nodos adyacentes (contexto) y acceso directo a recursos educativos como videos, diapositivas y tests. | No especificado. El documento describe la implementación y funciones, pero no reporta un experimento formal con usuarios o métricas de validación externa en los fragmentos proporcionados. | Capacidad para realizar una planificación de aprendizaje eficiente, una visión general clara del área de Ciencias de la Computación y una alta precisión en la clasificación de grupos de conocimiento mediante algoritmos. | Se ignoran los tipos de relaciones por simplicidad, la eficiencia algorítmica de la Distancia de Google Normalizada (NGD) disminuye con grandes volúmenes de datos y persisten puntos de conocimiento aislados que afectan la construcción exacta del grafo. |
| Design and Development of a Knowledge Service Platform in the Field of Computer Science: Knowledge Service Platform in Computer Science: Design and Development | Chen, C., Zhu, S., Tao, Q., Wu, Q., & Shi, Y. | 2023 | Mixta. Combina una visualización de grafo interactivo (usando la librería D3.js) con una interfaz de búsqueda por palabras clave y páginas de detalles para cada nodo de conocimiento | Búsqueda (fuzzy query) para localizar nodos, visualización de detalles (con soporte multimedia como video, PDF y VR), guía remedial (redirección automática a nodos de conocimiento tras errores en pruebas online) y navegación semántica a través de las relaciones del grafo. | El autor realiza una comparativa funcional frente a la enseñanza tradicional basada en PPTs, evaluando dimensiones como la representación, extracción, expansión y aplicación del conocimiento. | Mejora en la expresión, extensión y aplicación del conocimiento. Se reporta que la plataforma supera a los métodos tradicionales al ofrecer una visión estructurada y panorámica del sistema de computación, facilitando una mejor comprensión por parte de los estudiantes. | Riesgos de calidad en el contenido (posibilidad de contenido ilegal, plagiado o de baja calidad debido al modelo de crowdsourcing) y el alto costo de producción inicial para construir grafos de dominio de alta calidad de forma manual. |
| Gradual Study Advising with Course Knowledge Graphs | Dong, J., Li, W., Wang, Y., Li, Q., Baciu, G., Cao, J., Huang, X., Li, R. C., & Ng, P. H. F. | 2023 | Mixta. Ofrece un sistema web interactivo con visualización de grafos (usando Neo4j y mapas mentales) y una interfaz de lista para visualizar rutas textuales que contienen cursos específicos. | Rutas de aprendizaje personalizadas, visualización de relaciones de prerrequisitos (red de cursos), centralidad de conceptos (usando métricas como Degree y PageRank para resaltar nodos clave) y un buscador de rutas relacionales. | El autor afirma la efectividad del sistema a través de "extensas ilustraciones" y casos de uso dentro del currículo de Ciencias de la Computación, pero no reporta un experimento formal con usuarios o métricas automáticas en los fragmentos proporcionados. | Mejora en la orientación académica y de carrera, facilitando la comprensión de la estructura del programa universitario y la identificación rápida de conceptos fundamentales dentro de un curso. | Sin validación experimental completa y funcionalidad incompleta (el algoritmo de recomendación de rutas de aprendizaje aún no está implementado y se deja como trabajo futuro). También señala la dificultad de los estudiantes para localizar conceptos clave en grafos grandes y complejos. |
| Research on Visual Learning Platform for Database Principles Knowledge Points Integrating Knowledge Graph and Deep Learning | Liu, P., & Zhan, C. | 2025 | Utiliza una plataforma de aprendizaje visual inteligente con un diseño interactivo y una disposición jerárquica de capas. La interfaz permite expandir o colapsar nodos y ofrece una función de resaltado de rutas para trazar caminos conceptuales. | Rutas de aprendizaje personalizadas (optimizadas mediante GCN), filtros y sistema de búsqueda, recomendación inteligente de puntos de conocimiento, rastreo de prerrequisitos y vistas personalizadas basadas en el progreso del estudiante. | Experimento con usuarios (un estudio de 16 semanas con 180 estudiantes de pregrado divididos en grupos de control y experimental). También utiliza métricas automáticas (precisión, recall, F1-score) para evaluar el rendimiento del modelo de recomendación de aprendizaje profundo. | Mejora significativa en comparación con los métodos tradicionales: un incremento del 22.678% en el dominio del conocimiento, un 19.6% en la eficiencia del aprendizaje y un 32.1% en la satisfacción del usuario. | El autor señala como trabajo futuro la necesidad de expandir la cobertura del grafo de conocimiento, mejorar el rendimiento del algoritmo en el procesamiento de datos dispersos (sparse data) e integrar recursos de aprendizaje multimodales. |
| The ESW of Wikidata: Exploratory search workflows on Knowledge Graphs | Lissandrini, M., Prando, G., & Silvello, G. | 2025 | El estudio propone y utiliza una interfaz de consulta directa mediante SPARQL integrada en Jupyter notebooks para la fase de recolección de datos. Para la exploración de la colección resultante (ESW), propone un punto final (endpoint) SPARQL y acceso a los datos en formato RDF y JSON | Implementa flujos de trabajo exploratorios divididos en tareas de búsqueda progresivas (sub-tareas) que guían al usuario en el descubrimiento de información. Ofrece funcionalidades de reformulación de consultas, secuenciación de tareas y la provisión de flujos de referencia (gold standards) para guiar la exploración. | Mediante métricas automáticas de Precisión, Recuperación (Recall) y F-score, comparando los resultados de las consultas de los usuarios con los flujos de referencia. También analiza los tiempos de ejecución de las consultas y utiliza una puntuación de calidad de los participantes basada en su desempeño académico. | La creación de una colección de referencia con 234 flujos de trabajo y 10,645 consultas SPARQL reales. Reporta que la efectividad es mayor en tareas de "completitud" que en tareas "informativas" y observa un aumento progresivo en la complejidad y el tiempo de ejecución de las consultas a medida que avanza la sesión exploratoria. | Generalización limitada debido al uso de estudiantes en un entorno controlado; dificultad para evaluar el recall en tareas con objetivos vagos; métricas de evaluación que pueden ser excesivamente penalizadoras al no considerar la similitud semántica; e inconsistencias derivadas de la falta de uniformidad en el almacenamiento de datos de Wikidata. |
| Web-Based Learning Object Search Engine Solution Together with Data Visualization: The Case of MERLOT II | Gunarathne, W. K. T. M., Chootong, C., Sommool, W., Ochirbat, A., Chen, Y.-C., Reisman, S., & Shih, T. K. | 2018 | Visual/grafo (específicamente un grafo de conocimiento jerárquico interactivo de tres niveles que organiza los resultados de búsqueda en clusters | Exploración jerárquica por clusters (permite navegar desde la palabra clave raíz hacia grupos temáticos y luego a objetos de aprendizaje individuales), búsqueda por palabra clave única y acceso directo a las páginas de los recursos educativos al hacer clic en los nodos. | Métricas automáticas. Se utiliza el método del coeficiente de Silueta Promedio (Average Silhouette) para validar la precisión y calidad técnica del algoritmo de agrupamiento (clustering) SHRINK-H aplicado a los datos. | Mejora en la visión general (overview) de los resultados. El sistema permite obtener una estructura clara de los materiales de aprendizaje, eliminando datos irrelevantes que aparecen en las búsquedas tradicionales de MERLOT II y facilitando una navegación independiente de las calificaciones de usuarios o revisiones editoriales. | Tiempo de procesamiento elevado en la extracción de datos en tiempo real, dominio acotado (la demo se restringió a 10 palabras clave específicas de computación para las pruebas) y falta de claridad en el etiquetado (algunas etiquetas de clusters generadas automáticamente pueden no ser familiares o claras para el usuario). |

# **Anexo D. Análisis estadístico (descriptivo) de los datos de encuesta sobre orientación de aprendizaje**

[https://docs.google.com/document/d/17Sz2ZTTspc6XKC1Jn5jP3O\_Y-\_xXs\_Er22Jdms2rmho/edit?tab=t.0\#heading=h.b3jfx56khh04](https://docs.google.com/document/d/17Sz2ZTTspc6XKC1Jn5jP3O_Y-_xXs_Er22Jdms2rmho/edit?tab=t.0#heading=h.b3jfx56khh04) 

# **Anexo E. Análisis temático de entrevista semiestructurada al director Luis Flores y preguntas abiertas de encuesta sobre orientación de aprendizaje**

[https://docs.google.com/document/d/1RZvywLgE7mWeTRZI2Crsdl6KpSe7E29Th6m9G4Ja8cg/edit?tab=t.0](https://docs.google.com/document/d/1RZvywLgE7mWeTRZI2Crsdl6KpSe7E29Th6m9G4Ja8cg/edit?tab=t.0) 

# **Anexo F. Plan de estudios de Ingeniería Informática PUCP, recuperado el 16 de junio del 2026**

[https://drive.google.com/file/d/1yO\_Cw0fxbb72hmbqk7mgl0NZIItq2\_W-/view?usp=drive\_link](https://drive.google.com/file/d/1yO_Cw0fxbb72hmbqk7mgl0NZIItq2_W-/view?usp=drive_link) 

# **Anexo G. Documento de especificación de la ontología.**

[https://docs.google.com/document/d/1NNPbBKxT-8QtkLgzQCWGAnAMl9sn7XvpWnvfIcMzLcg/edit?tab=t.0](https://docs.google.com/document/d/1NNPbBKxT-8QtkLgzQCWGAnAMl9sn7XvpWnvfIcMzLcg/edit?tab=t.0) 

# **Anexo H. Constancia de validación experta del Resultado 1**

[https://docs.google.com/document/d/1I\_0G-BFlAjpL33KI8Zy\_NAGJ\_X-jL2E7iPWTHG2Axc0/edit?tab=t.0\#heading=h.h3l5l0alhqcs](https://docs.google.com/document/d/1I_0G-BFlAjpL33KI8Zy_NAGJ_X-jL2E7iPWTHG2Axc0/edit?tab=t.0#heading=h.h3l5l0alhqcs) 

# **Anexo I. Documento de decisiones de diseño de la ontología**

[https://docs.google.com/document/d/1xZYwS8VMiZj3fbcyX9nDIt3S-ul-Cgakw5VMzgZ4BAg/edit?tab=t.o4xqjhg9d2s0](https://docs.google.com/document/d/1xZYwS8VMiZj3fbcyX9nDIt3S-ul-Cgakw5VMzgZ4BAg/edit?tab=t.o4xqjhg9d2s0) 

# **Anexo J: Plan de Proyecto**

* **Proyecto**

Sistema de gestión de conocimiento basado en grafos de conocimiento para el currículo de Ingeniería Informática de la PUCP.

**Objetivos**

* O1. Modelar el dominio del conocimiento de la carrera mediante una ontología formal.  
* O2. Diseñar e implementar el módulo de gestión del grafo de conocimiento, con pipeline de ingesta automatizada e interfaz programática.  
* O3. Diseñar e implementar el mecanismo de navegación y descubrimiento semántico.

**Resultados**

* R1. Modelo ontológico formal del dominio (T-Box).  
* R2. Capa de referencia (instancias) curada desde el estándar CS2023.  
* R3. Documentación del módulo del grafo de conocimiento.  
* R4. Módulo del grafo implementado (pipeline de ingesta y API).  
* R5. Documentación del mecanismo de navegación y descubrimiento.  
* R6. Prototipo funcional de navegación del grafo.

* **Justificación**

El proyecto responde a una deficiencia estructural verificada: las relaciones del currículo de Ingeniería Informática (entre cursos, conceptos, temas y áreas) no están disponibles de forma articulada en un medio consultable, y los recursos académicos se encuentran dispersos sin unión semántica. 

El beneficiario directo es el estudiante de la carrera. Al explicitar las dependencias conceptuales y vincularlas con sus recursos, el artefacto reduce el esfuerzo que hoy demanda reconstruir esas relaciones por cuenta propia: la evidencia recogida (Anexos D y E) registra que orientarse sobre qué estudiar antes de profundizar en un tema toma con frecuencia más de un día, que es habitual descubrir tarde la falta de una base de otro curso, y que la búsqueda de material se dispersa entre varias fuentes sin anclaje al currículo. El sistema no interviene la conducta del estudiante ni busca cambiar sus hábitos; ofrece un medio donde esa información está articulada y es navegable, de modo que el esfuerzo de reconstrucción deja de ser necesario.

El beneficio alcanza también a la gestión académica: la coordinación y el cuerpo docente obtienen una vista del currículo como grafo consultable (prerrequisitos conceptuales, cobertura de temas por curso, recursos asociados) útil para revisar la articulación del plan más allá de los prerrequisitos formales entre asignaturas.

Por último, el enfoque es escalable. El modelo del dominio es independiente del contenido particular de la PUCP y su capa de referencia se ancla a un estándar internacional (CS2023) que puede sustituirse por otro; en consecuencia, el método (formalizar un currículo como ontología y grafo, y poblarlo desde sus documentos) es trasladable a otras carreras o instituciones con un costo de adaptación acotado.

* **Viabilidad**

**Técnica**

El proyecto es viable técnicamente porque se apoya en tecnologías maduras de web semántica y de bases de datos orientadas a grafos, cuyo comportamiento ya quedó comprobado en la primera fase del trabajo, donde el modelo del dominio se construyó y validó sin contratiempos. Para la gestión del grafo, una base orientada a grafos resuelve de forma natural las consultas de dependencia y de recorrido que en un modelo relacional resultarían costosas, y la extracción de información desde los sílabos es abordable mediante modelos de lenguaje con salidas estructuradas y verificables sobre un piloto acotado.

**Temporal**

El proyecto es viable en el tiempo disponible, distribuido en los dos semestres de tesis. La primera mitad, ya ejecutada, cubrió los fundamentos y el modelado del dominio, lo que reduce el riesgo del tramo restante; la segunda concentra la construcción del módulo y del mecanismo de navegación. El cronograma contempla un margen de reajuste: ante cualquier desviación, se recalcula y se acuerda con el asesor en las reuniones semanales, priorizando el cierre de los resultados centrales.

**Económica** 

El proyecto es de bajo costo. El desarrollo se sostiene casi por completo en herramientas de código abierto y en recursos propios o institucionales, de modo que el desembolso real es marginal. El único costo variable corresponde al uso de un modelo de lenguaje comercial para la ingesta automatizada, acotado al piloto y reducible mediante capas gratuitas, modelos más económicos o créditos académicos; su estimación se detalla en el costeo.

* **Alcance**

El proyecto comprende el modelado formal del dominio curricular, la construcción del módulo que gestiona el grafo de conocimiento (con su pipeline de ingesta y su interfaz de programación) y el desarrollo de un prototipo de navegación sobre ese grafo. El dominio se delimita al Modelo de Conocimiento del estándar CS2023, en su eje de Ciencias de la Computación e Ingeniería de Software, y se trabaja sobre un piloto de trece sílabos del plan de estudios, suficiente para validar la extracción.

Quedan fuera del alcance el modelado de competencias y el modelado del estudiante (su perfil, su progreso o la recomendación personalizada), por corresponder a marcos conceptuales distintos que abren líneas de trabajo posteriores; el procesamiento del catálogo completo de la carrera, acotado deliberadamente al eje piloto; y la evaluación empírica del impacto en el aprendizaje, ya que la validación se concentra en la corrección del artefacto y no en un estudio con usuarios.

* **Limitaciones** 

De tiempo: dos semestres de curso acotan la profundidad del piloto. 

De presupuesto: el consumo de LLM es el único costo variable y constituye un riesgo abierto. 

De herramientas: la extracción depende de la calidad y heterogeneidad de los sílabos en PDF y del comportamiento no determinista del LLM. 

De validación: la verificación es de consistencia (HermiT), de criterio de ingeniería (precisión mayor o igual a 75%) y de experto, no de efectividad pedagógica.

* **Identificación de los riesgos del proyecto**

Los riesgos fueron resumidos en la Tabla A.1.

**Tabla A.1. Matriz de riesgos del proyecto**

| Riesgo | Prob. | Impacto | Mitigación | Contingencia |
| :---- | :---- | :---- | :---- | :---- |
| Costo de créditos de LLM para la ingesta (R4) inasequibles para el tesista  | Media | Alta | Capas gratuitas, modelos más baratos o locales, gestión de créditos académicos; estimación acotada a 13 sílabos | Reducir el lote piloto o sustituir por modelo local/extracción semiautomática |
| Calidad y heterogeneidad de los sílabos condicionan a no obtener el indicador objetivo (precisión por debajo del 75%) | Media | Alta | Preproceso robusto, prompts tipados con reintentos, curación previa | Acotar las entidades a extraer |
| Carga académica y tiempo impiden cumplir con el cronograma | Media | Media | Priorización por resultado y avances parciales | Recalcular y comunicar el cronograma; diferir alcance no crítico |
| Complejidad de la transición OWL a LPG que resulta en retrasos o no cumplimiento. | Media | Media | Prototipar la transición temprano en R3 | Buscar asesoría de otros expertos con trabajos similares |
| Mantenimiento/obsolescencia del grafo (señalado por la dirección) | Alta | Media | Modelar semántica y no archivos; separar capa de referencia estable de la institucional | Registrar el modelo de mantenimiento como trabajo futuro; no comprometer actualización continua en el alcance |
| Disponibilidad del asesor para validaciones | Baja | Media | Reuniones semanales agendadas y validaciones planificadas | Validación asíncrona por correo; reprogramar hitos |

* **Estructura de descomposición del trabajo (EDT)**

* 1.0 KMS basado en grafos para el currículo de Ingeniería Informática (PUCP)  
* 1.1 Gestión del proyecto (transversal)  
  * 1.1.1 Planificación, plan, EDT y cronograma  
  * 1.1.2 Reuniones de asesoría (semanales, 30 min)  
  * 1.1.3 Entregables y observaciones del curso  
*  1.2 Fundamentos del proyecto   
  * 1.2.1 Problemática y formulación de objetivos  
  *  1.2.2 Marco conceptual  
  * 1.2.3 Estado del arte (revisión sistemática)  
*  1.3 O1 \- Modelado del dominio  
  * 1.3.1 R1 \- Modelo ontológico T-Box  
  * 1.3.2 R2 \- Capa de referencia curada desde CS2023  
* 1.4 O2 \- Módulo de gestión del grafo  
  * 1.4.1 R3 \- Documentación del módulo (C4, ADRs, casos de prueba)   
  * 1.4.2 R4 \- Módulo: pipeline de ingesta y API   
* 1.5 O3 \- Mecanismo de navegación  
  * 1.5.1 R5 \- Documentación del mecanismo (C4, ADRs)   
  * 1.5.2 R6 \- Prototipo funcional   
* 1.6 Cierre y documentación  
  * 1.6.1 Redacción de cierre  
  * 1.6.2 Revisión final y sustentación

* **Lista de tareas y cronograma**

Las tareas se derivan directamente de la estructura de descomposición del trabajo: cada resultado se descompone en las fases de su procedimiento, que son la unidad de estimación, y los paquetes menos complejos se colocan directamente como tareas. La lista incluye las actividades de verificación y validación, las reuniones de asesoría y los entregables del curso, e indica para cada tarea su duración, esfuerzo en horas-persona, costo, dependencias y periodo programado.

La Figura A.1. presenta el diagrama de Gantt del cronograma del proyecto y la Tabla A.2. presenta la lista de tareas con las dependencias, duración, esfuerzo, costo y periodo.

![][image5]

**Figura A.1. Diagrama de Gantt del cronograma del proyecto**

**Tabla A.2. Cronograma con lista de tareas**

| ID | Tarea | Dependencias | Duración | Esfuerzo (h) | Costo (S/.) | Periodo |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| T04 | Problemática y formulación de objetivos | \- | 12.7 sem | 50 | 1000 | T1: 23/03–20/06 |
| T07 | Estado del arte (SLR) | T4 | 0.6 sem | 24 | 480 | T1: 13/04–17/04 |
| T05 | Marco conceptual | \- | 3 sem | 35 | 700 | T1: 20/04–11/05 |
| T06 | Métodos y procedimientos | \- | 3 sem | 30 | 600 | T1: 20/04–11/05 |
| T08 | R1 · Especificación y conceptualización | T6 | 0.9 sem | 20 | 400 | T1: 18/05–24/05 |
| T09 | R1 · Formalización en OWL | T7 | 1.9 sem | 36 | 720 | T1: 25/05–07/06 |
| T10 | R1 · Validación de la T-Box (V\&V) | T8 | 1 sem | 6 | 120 | T1: 08/06–15/06 |
| T01 | Planificación, plan, EDT y cronograma | \- | 0.9 sem | 24 | 480 | T1: 15/06–21/06 |
| T11 | R2 · Curación de la taxonomía de ref. | T9 | 1.7 sem | 8 | 160 | T1: 29/06–11/07 |
| T12 | R2 · Carga y validación del backbone | T10 | 0.9 sem | 4 | 80 | T1: 12/07–18/07 |
| T13 | R3 · Definición de atributos de calidad | T11 | 0.9 sem | 10 | 200 | T2: 17/08–23/08 |
| T14 | R3 · Modelado C4 | T11 | 1.9 sem | 28 | 560 | T2: 17/08–30/08 |
| T15 | R3 · Especificación del esquema LPG | T12, T13 | 1.3 sem | 24 | 480 | T2: 31/08–09/09 |
| T16 | R3 · ADRs | T11 | 3.9 sem | 16 | 320 | T2: 17/08–13/09 |
| T17 | R3 · Casos de prueba de la ingesta | T14 | 0.9 sem | 16 | 320 | T2: 14/09–20/09 |
| T18 | R4 · Entorno y carga del backbone | T11, T15 | 0.9 sem | 80 | 1600 | T2: 21/09–27/09 |
| T19 | R4 · Pipeline de ingesta (LLM) | T11, T16, T17 | 3.9 sem | 40 | 800 | T2: 28/09–25/10 |
| T20 | R4 · API REST | T18 | 1.9 sem | 22 | 440 | T2: 19/10–01/11 |
| T22 | R5 · Diseño de flujos y wireframes | T14 | 1.4 sem | 24 | 480 | T2: 02/11–12/11 |
| T21 | R4 · Validación del pipeline (V\&V) | T18, T19 | 1.4 sem | 14 | 280 | T2: 02/11–12/11 |
| T23 | R5 · Documentación C4 y ADRs | T21 | 0.9 sem | 12 | 240 | T2: 13/11–19/11 |
| T24 | R6 · Implementación del prototipo | T20, T22 | 2.9 sem | 70 | 1400 | T2: 16/11–06/12 |
| T25 | R6 · Pruebas de aceptación (V\&V) | T24, T14 | 0.9 sem | 12 | 240 | T2: 30/11–06/12 |
| T26 | Redacción de cierre | \- | 1.7 sem | 35 | 700 | T2: 30/11–12/12 |
| T27 | Revisión final y sustentación | T25 | 0.7 sem | 30 | 600 | T2: 07/12–12/12 |
| T28 | Reuniones de asesoría (semanales, 30 min) | \- | 37.7 sem | 14 | 280 | T1 y T2: 23/03–12/12 |
| T29 | Entregables y observaciones del curso | \- | 37.7 sem | 26 | 520 | T1 y T2: 23/03–12/12 |
|  | Total tesista |  |  | 710 | 14200 |  |

Cabe resaltar que se está considerando un costo por hora del tesista de S/. 20 y del asesor de S/. 150\.

* **Lista de recursos**

**Personas y capacitación**

Tesista (1), responsable de diseño, implementación y validación, participa en todas las tareas; requiere profundización autodirigida en tecnologías de web semántica y frameworks de desarrollo (PydanticAI, web). 

Asesor de tesis, Andrés Melgar: orientación técnica y de ingeniería de conocimiento; validaciones (T10, T12, T21, T25). 

Docente del curso de tesis 1, Claudia Zapata: orientación metodológica y de rúbrica. 

Docente del curso de tesis 2: orientación metodológica y de rúbrica. 

No aplican necesidades de capacitación para los asesores.

**Estándares**

CS2023 (ACM/IEEE) como fuente de capa de referencia; OWL 2 y RDF/Turtle (W3C); Modelo C4 (Brown) y ADR (Nygard) para documentación de arquitectura; Kitchenham y Charters para la revisión sistemática; APA 7.ª para citas; Git con versionado para el repositorio.

**Herramientas**

Protégé, HermiT, OWL 2/Turtle (R1 y R2); Neo4j Community, Cypher (R3 y R4); Python, FastAPI, PydanticAI y LLM vía API de OpenAI (R4); Git y GitHub (R3–R6); Zotero y bases de datos académicas.

**Equipamiento**

Laptop propia (uso intensivo en T8 y T17–T24) y almacenamiento en la nube para respaldo (capa gratuita).

**Materiales**

No aplica; el proyecto es de naturaleza computacional.

* **Costeo del Proyecto**

Distingue equipo humano (por horas de esfuerzo), equipamiento (depreciación lineal) y software/servicios (TCO). Cifras referenciales; el desembolso real es mínimo porque los recursos son propios, institucionales o gratuitos, salvo el consumo de LLM. La información se visualiza en la Tabla A.3.

**Tabla A.3. Costeo del proyecto**

| Ítem | Descripción | Costo (S/.) |
| :---- | :---- | :---- |
| **0** | **Costo total del proyecto** | **18,725** |
| **1** | **Equipo humano** | **17,350** |
| 1.1 | Tesista: 710 h × S/.20/h | 14,200 |
| 1.2 | Asesores: 21h × S/.150/h  | 3,150 |
| **2** | **Equipamiento (depreciación lineal)** | **675** |
| 2.1 | Laptop propia: S/.3,600 aproximados a 48 meses, 9 meses de uso | 675 |
| **3** | **Software y servicios (TCO)** | **700** |
| 3.1 | API de LLM razonador para la ingesta de R4 (13 sílabos; desarrollo y corrida final, precio estándar OpenAI; reducible con capas gratuitas o créditos académicos) | 700 |
| 3.2 | Protégé, Neo4j Community, Python/FastAPI, Git | 0 |
| **4** | **Materiales e insumos** | **0** |

[^1]:  Recuperado el 18 de junio del 2026 a las 20:40 h (UTC-5) de [https://facultad-ciencias-ingenieria.pucp.edu.pe/wp-content/uploads/2026/03/ppee\_INFORMATICA-2026-1.pdf](https://facultad-ciencias-ingenieria.pucp.edu.pe/wp-content/uploads/2026/03/ppee_INFORMATICA-2026-1.pdf)y visible en el anexo F.

[^2]:  El umbral de al menos 5 clases y al menos 3 tipos de relación va de acuerdo a la aplicación de la metodología Ontology Development 101 de Noy y McGuinness

[^3]: Umbral definido con base en resultados recientes de construcción automática de grafos de conocimiento educativos [(S. Li et al., 2026; Xu & Che, 2025\)](https://www.zotero.org/google-docs/?XCU8kT)

[image1]: 

[image2]: 

[image3]: 

[image4]: 

[image5]: 