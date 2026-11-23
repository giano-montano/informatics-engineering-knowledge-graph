# Reporte CP-15 · Enlace con CS2023

**Fecha:** 2026-11-22 · **Evaluador:** el autor · **Grafo:** corrida de medición del 2026-11-16 (`var/medicion-r4/`, tag `codigo-congelado-2026-11-16`)
**Guía aplicada:** `casos-de-prueba/guia-de-evaluacion-de-relaciones.md`, commit `998ff57` · **Planilla:** `casos-de-prueba/relaciones/juicio-de-relaciones-semilla-20261116.xlsx`

Medida descriptiva, sin umbral: no cambia el indicador de R4.

## Alcance

Todas las aristas `PART_OF` de un tema a una unidad de CS2023 del grafo final: 78, una por tema.

## Resumen

| Juicio | Cantidad | % |
|---|---|---|
| Correcta | 52 | 66,7 % |
| Aceptable | 15 | 19,2 % |
| Incorrecta | 11 | 14,1 % |
| **Total** | **78** | 100 % |

Por curso:

| Curso | Correctas | Aceptables | Incorrectas |
|---|---|---|---|
| 1INF24 | 9 | 1 | 1 |
| 1INF25 | 5 | 3 | 0 |
| 1INF27 | 4 | 0 | 0 |
| 1INF29 | 6 | 0 | 0 |
| 1INF30 | 4 | 3 | 0 |
| 1INF31 | 5 | 0 | 0 |
| 1INF32 | 4 | 1 | 0 |
| 1INF33 | 4 | 3 | 1 |
| 1INF37 | 3 | 0 | 7 |
| 1INF47 | 1 | 0 | 1 |
| 1INF49 | 3 | 3 | 0 |
| 1INF50 | 2 | 0 | 0 |
| 1INF54 | 2 | 1 | 1 |

## Observaciones

- Las seis aristas hacia KU-SDF-Practices son incorrectas: cinco son temas de proceso y gestión de software de 1INF37 (estimación, gestión del proyecto, ciclo de vida, calidad de proceso, desarrollo ágil) y una de 1INF54 (formulación del proyecto). Los cuatro tópicos de esa unidad tratan pruebas básicas, entornos de desarrollo, legibilidad y especificación de módulos.
- En tres de las once incorrectas no se identificó una unidad de CS2023 que cubra el tema.
- Siete de las once incorrectas son de 1INF37, un sílabo retenido del ajuste del prompt.
- Las aceptables se concentran en temas que una unidad cubre en parte y otra con más precisión, sobre todo en Ingeniería de Software y en Fundamentos de Lenguajes de Programación.

## Juicios

| # | Curso | Tema | Unidad asignada | Juicio | Unidad mejor | Motivo |
|---|---|---|---|---|---|---|
| 0 | 1INF29 | SISTEMAS OPERATIVOS | KU-OS-Purpose | correcta |  | El núcleo son el papel, las funciones y los servicios del SO. OS-Principles precisa llamadas y estructuras, pero OS-Purpose cubre el saber principal. Se juzga por los conceptos, dado el título genérico. |
| 1 | 1INF33 | SQL DML | KU-DM-Querying | correcta |  | Consultas SQL, subconsultas y agrupaciones son construcción de consultas. |
| 2 | 1INF24 | Algoritmos heurísticos, metaheurísticos y bioinspirados | KU-AL-Strategies | correcta |  | Las estrategias voraces y estocásticas cubren el saber principal del tema; la inteligencia colectiva es una aplicación de esas estrategias. |
| 3 | 1INF24 | Aprendizaje automático | KU-AI-ML | correcta |  | Los tipos y el proceso de aprendizaje supervisado corresponden a ML. |
| 4 | 1INF33 | LENGUAJE DE PROGRAMACIÓN DE BASE DE DATOS (PL/SQL) | KU-SE-Construction | aceptable | KU-FPL-Constructs | SE-Construction cubre el manejo de excepciones, pero no la mayor parte de PL/SQL. FPL-Constructs 11 nombra lenguajes de bases de datos; DM-Querying 8 añade procedimientos almacenados. |
| 5 | 1INF37 | DESPLIEGUE DEL SOFTWARE | KU-SE-Construction | correcta |  | Despliegue continuo, DevOps y gestión de entregas cubren el núcleo del tema. |
| 6 | 1INF25 | FUNCIONES | KU-FPL-Constructs | aceptable | KU-FPL-Types | La metaprogramación de FPL-Constructs cubre las plantillas de funciones. El núcleo de sobrecarga y funciones genéricas encaja con mayor precisión en FPL-Types 6 y 14; los parámetros y el ámbito se complementan con SDF-Fundamentals 4. |
| 7 | 1INF29 | PROCESOS Y COMUNICACIÓN ENTRE PROCESOS | KU-OS-Process | correcta |  | OS-Process cubre el modelo/estado de procesos, hilos y comunicación. OS-Concurrency precisa semáforos, carreras y monitores, pero no sustituye el componente de procesos e IPC. |
| 8 | 1INF24 | Redes neuronales artificiales | KU-AI-ML | correcta |  | La unidad incluye perceptrones multicapa, entrenamiento de redes y ética de ML. |
| 9 | 1INF33 | NORMALIZACIÓN | KU-DM-Relational | correcta |  | Las formas normales y la desnormalización se cubren directamente. |
| 10 | 1INF30 | DISEÑO Y GENERACIÓN DE REPORTES | KU-SE-Construction | correcta |  | El núcleo es construir e integrar reportes utilizando una librería/framework, cubierto por SE-Construction 7. |
| 11 | 1INF32 | ALGORITMOS RECURSIVOS AVANZADOS: BACKTRACKING | KU-AL-Strategies | correcta |  | El nombre delimita backtracking; los arreglos, matrices y TAD son las estructuras utilizadas, no una técnica alternativa. |
| 12 | 1INF49 | INGENIERÍA DE REQUISITOS | KU-SE-Requirements | correcta |  | Obtención, tipos y especificación de requisitos son el contenido principal. |
| 13 | 1INF33 | TRANSACCIONES | KU-DM-Internals | correcta |  | Serializabilidad, concurrencia y bloqueos están expresamente incluidos. |
| 14 | 1INF25 | PROGRAMACIÓN ORIENTADA A OBJETOS | KU-FPL-OOP | correcta |  | Predominan clases, métodos, encapsulamiento, herencia y polimorfismo. |
| 15 | 1INF49 | MODELOS CONCEPTUALES CON DIAGRAMAS DE CLASES | KU-SE-Requirements | aceptable | KU-DM-Modeling | SE-Requirements 6 cubre formalizar especificaciones, pero los modelos conceptuales con UML se nombran explícitamente en DM-Modeling 3. SE-Design 10 cubre su conexión con los diagramas de diseño. |
| 16 | 1INF29 | SISTEMAS DE ARCHIVO (FILE SYSTEMS ) | KU-OS-Files | correcta |  | Archivos, metadatos, montaje, directorios y su implementación forman el núcleo. |
| 17 | 1INF32 | META HEURÍSTICAS | KU-AL-Strategies | correcta |  | GRASP combina una construcción voraz aleatorizada con mejoría iterativa; esos paradigmas están en AL-Strategies. AI-Search añade búsqueda local, sin desplazar el foco en estrategias algorítmicas. |
| 18 | 1INF27 | COMPLEJIDAD Y EFICIENCIA ALGORÍTMICA | KU-AL-Complexity | correcta |  | Tiempo de ejecución, eficiencia y medidas asintóticas son cobertura directa. |
| 19 | 1INF27 | TÉCNICAS ALGORÍTMICAS BÁSICAS PARA LA RESOLUCIÓN DE PROBLEMAS | KU-AL-Strategies | correcta |  | Fuerza bruta, divide y vencerás y recursión son paradigmas explícitos de la unidad. |
| 20 | 1INF24 | Algoritmos básicos para regresión | KU-AI-ML | correcta |  | Incluye regresión lineal, árboles, KNN y evaluación de regresores. |
| 21 | 1INF27 | HASHING | KU-AL-Foundational | correcta |  | Las tablas hash y el tratamiento de colisiones son explícitos. |
| 22 | 1INF37 | VERIFICACIÓN, VALIDACIÓN Y PRUEBAS DE SOFTWARE | KU-SE-Validation | correcta |  | El título y el sílabo 1INF37, cap. 5, p. 3, incluyen verificación, validación y pruebas; la lista extraída solo conserva calidad/aseguramiento/control. El juicio usa ese contenido del capítulo. |
| 23 | 1INF25 | OPERADORES SOBRECARGADOS | KU-FPL-OOP | aceptable | KU-FPL-Types | FPL-OOP aporta clases y métodos, pero no nombra sobrecarga de operadores. FPL-Types distingue explícitamente el polimorfismo por sobrecarga, que es el saber específico del capítulo. |
| 24 | 1INF49 | DISEÑO DE INTERFACES DE USUARIO | KU-HCI-Design | correcta |  | Prototipado, interfaces gráficas, diseño visual y guías de diseño son explícitos. |
| 25 | 1INF37 | ESTIMACIÓN Y CRONOGRAMA DE SOFTWARE | KU-SDF-Practices | incorrecta | KU-SE-Requirements | SDF-Practices 1–4 trata pruebas básicas, IDE, legibilidad y especificación de módulos. No cubre estimación ni cronogramas. SE-Requirements 9 cubre estimación de esfuerzo y SE-Teamwork 5 incluye estimación y calendario. |
| 26 | 1INF24 | Preprocesamiento y reducción dimensional | KU-AI-ML | correcta |  | La mayoría de conceptos son preprocesamiento: faltantes, codificación, normalización y estandarización. La reducción dimensional del título no desplaza ese núcleo. |
| 27 | 1INF50 | PRUEBAS DE SOFTWARE | KU-SE-Validation | correcta |  | Tipos, diseño y generación de pruebas, casos y TDD son cobertura directa. |
| 28 | 1INF24 | Búsqueda dentro de la Inteligencia Artificial | KU-AI-Search | correcta |  | Espacios de estados y búsquedas no informadas y heurísticas se enumeran. |
| 29 | 1INF24 | Lógica difusa | KU-AI-KRR | aceptable | KU-AI-LRR | AI-KRR aporta cobertura general de representación; el contenido de sistemas expertos/lógica no clásica se cubre mejor en la unidad alternativa indicada. |
| 30 | 1INF30 | PROGRAMACIÓN DISTRIBUIDA | KU-PDC-Programs | aceptable | KU-SPD-Web | PDC-Programs 5 cubre un servicio que atiende clientes, pero no desarrolla las tecnologías web/cloud del tema. SPD-Web nombra servicios cloud, API, hosting y arquitectura REST. |
| 31 | 1INF54 | DESPLIEGUE Y ENTREGA | KU-SE-Construction | correcta |  | El tema no tiene conceptos en el grafo. El sílabo 1INF54, cap. 4, p. 3, pide empaquetar el producto para distribuirlo: corresponde a release management. |
| 32 | 1INF49 | DISEÑO DE LA EXPERIENCIA USUARIO | KU-HCI-Design | aceptable | KU-HCI-User | HCI-Design cubre procesos de diseño. HCI-User nombra personas, empathy maps, journey maps y diversidad, que concentran la mayoría de conceptos del tema. |
| 33 | 1INF54 | FORMULACIÓN DEL PROYECTO Y DEFINICIÓN DE LA SOLUCIÓN | KU-SDF-Practices | incorrecta | KU-SE-Requirements | SDF-Practices 1–4 no incluye gestión del proyecto, riesgos, configuración ni prototipado de solución. SE-Requirements cubre riesgos/prototipos y SE-Tools cubre configuración; no se afirma que una única KU cubra todo el tema. |
| 34 | 1INF31 | REFINANDO LA ARQUITECTURA | KU-SE-Design | correcta |  | Los estilos y arquitecturas estándar están directamente cubiertos. |
| 35 | 1INF31 | PRESENTANDO LA ARQUITECTURA | KU-SE-Design | correcta |  | Presentar/documentar la arquitectura mediante vistas y notaciones es modelar diseños de software. SE-Tools 5 se centra en las herramientas, no desplaza el contenido arquitectónico. |
| 36 | 1INF47 | ASPECTOS TECNOLOGICOS DEL PROCESO DE CONSTRUCCIÓN DEL PRODUCTO SOFTWARE | KU-SE-Construction | correcta |  | Las prácticas de construcción y calidad de programas son el saber principal del capítulo, aunque se revisen requisitos y modelos. |
| 37 | 1INF24 | Reglas difusas y métodos de inferencia | KU-AI-KRR | incorrecta | KU-AI-LRR | La inferencia bayesiana/probabilística de AI-KRR no cubre fusificación, defusificación ni el método Mamdani; la afinidad general no alcanza el núcleo. |
| 38 | 1INF54 | SELECCIÓN DE SOLUCION Y DISEÑO | KU-SE-Design | aceptable | KU-AL-Strategies | SE-Design cubre arquitectura, pero predominan el diseño y la selección experimental de algoritmos, mejor representados por la unidad alternativa indicada. |
| 39 | 1INF29 | PLANIFICACIÓN Y DESPACHO DE PROCESOS (SCHEDULING AND DISPATCH) | KU-OS-Scheduling | correcta |  | Planificación apropiativa/no apropiativa, políticas y tiempo real son explícitos. |
| 40 | 1INF37 | GESTIÓN DEL PROYECTO DE DESARROLLO DE SOFTWARE | KU-SDF-Practices | incorrecta | KU-SE-Teamwork | SDF-Practices 1–4 no trata el ciclo de gestión de un proyecto. SE-Teamwork 5 cubre organización, esfuerzo y calendario y SE-Construction 9 cubre dependencias/hitos/riesgos. Son alternativas parciales, no cobertura completa de inicio a cierre. |
| 41 | 1INF29 | ADMINISTRACIÓN DE MEMORIA | KU-OS-Memory | correcta |  | Memoria física/virtual, caché, paginación y thrashing son explícitos. |
| 42 | 1INF37 | METODOLOGÍAS Y MODELOS DE CICLO DE VIDA | KU-SDF-Practices | incorrecta |  | Los cuatro tópicos de SDF-Practices no cubren ISO 12207, cascada, modelos evolutivos/incrementales ni procesos del ciclo de vida. No se identificó en las KU proporcionadas una unidad que cubra de forma explícita el conjunto de este tema. |
| 43 | 1INF24 | Inteligencia Artificial | KU-AI-Introduction | correcta |  | Los agentes, entornos, características de problemas e historia de IA son explícitos. |
| 44 | 1INF31 | ARQUITECTURA DE SOFTWARE | KU-SE-Design | correcta |  | Pensamiento y negociación arquitectónica se apoyan en arquitectura y evaluación de compromisos de diseño. |
| 45 | 1INF25 | HERENCIA | KU-FPL-OOP | correcta |  | Herencia simple/múltiple, sobrescritura y visibilidad son explícitos. |
| 46 | 1INF30 | ACCESO A BASE DE DATOS | KU-SE-Construction | aceptable | KU-DM-Querying | SE-Construction cubre drivers/librerías, pero el acceso programático y la persistencia encajan mejor en la unidad alternativa indicada. |
| 47 | 1INF37 | CALIDAD DE PROCESO SOFTWARE | KU-SDF-Practices | incorrecta |  | SDF-Practices solo enumera pruebas básicas, IDE, legibilidad y especificación de módulos. No cubre modelos de madurez o mejora de procesos (CMMI, MPS, MoProSoft, ISO 29110). No se identificó una KU que cubra explícitamente este conjunto. |
| 48 | 1INF47 | FUNCIONALIDADES DE LOS DIFERENTES MÓDULOS DEL SISTEMA | KU-SE-Construction | incorrecta | KU-SE-Design | Predominan captura de requisitos, modelos de análisis/diseño y evaluación de UI; no hay cobertura sustantiva de ese núcleo en los tópicos de construcción. |
| 49 | 1INF32 | HEURÍSTICAS | KU-AL-Strategies | correcta |  | Algoritmos voraces, aproximación y estrategias para problemas difíciles cubren el núcleo. |
| 50 | 1INF33 | METODOLOGÍAS DE MODELAMIENTO | KU-DM-Modeling | correcta |  | El núcleo son modelos conceptuales/relacionales y técnicas para representarlos; los tipos SQL son secundarios. |
| 51 | 1INF27 | ESTRUCTURAS DE DATOS (TAD) Y SUS IMPLEMENTACIONES | KU-AL-Foundational | correcta |  | TAD, listas, pilas, colas, árboles, grafos y algoritmos de búsqueda/recorrido son cobertura directa. |
| 52 | 1INF33 | TRIGGERS | KU-DM-Relational | incorrecta | KU-FPL-Constructs | El tema trata programación y tipos de triggers; integridad es solo una aplicación posible no declarada y DM-Relational no cubre sustantivamente ese núcleo. |
| 53 | 1INF24 | Algoritmos básicos para clasificación | KU-AI-ML | correcta |  | Clasificación, KNN, árboles, regresión logística y métricas son explícitos. |
| 54 | 1INF33 | PRESENTACIÓN DEL CURSO Y CONCEPTOS BÁSICOS | KU-DM-Core | aceptable | KU-DM-Modeling | Se juzgan los conceptos, no el rótulo administrativo. DM-Core cubre propósito/componentes del SGBD; predominan modelos de datos, modelo relacional y entidad-relación, mejor cubiertos por DM-Modeling. |
| 55 | 1INF37 | CALIDAD DE PRODUCTO SOFTWARE | KU-SE-Reliability | incorrecta | KU-SE-Validation | El capítulo enseña modelos de calidad general e ISO 25000; no acredita confiabilidad como contenido enseñado y esa especialización no cubre el núcleo. |
| 56 | 1INF49 | VALIDACIÓN Y GESTIÓN DE REQUISITOS | KU-SE-Requirements | aceptable | KU-SE-Validation | SE-Requirements cubre validez y evolución de requisitos. SE-Validation cubre de forma directa verificación, validación y casos de prueba (3 de los 5 conceptos); la trazabilidad se precisa en SE-Design 9 y las heurísticas en HCI-Evaluation 2.f. |
| 57 | 1INF30 | PROGRAMACIÓN CONCURRENTE | KU-PDC-Programs | aceptable | KU-PDC-Coordination | PDC-Programs 5 cubre crear hilos, pero la sincronización mediante monitores/semáforos domina el tema. PDC-Coordination nombra suspensión/señalización, exclusión mutua y semáforos/variables de condición. |
| 58 | 1INF25 | LENGUAJE DE PROGRAMACIÓN JAVA | KU-FPL-OOP | correcta |  | El sílabo 1INF25, cap. 8, p. 2, incluye clases/objetos, constructores, acceso, herencia y polimorfismo además de interfaces/ArrayList. Son el núcleo aplicado de POO en Java, aunque varios no figuran en los conceptos extraídos. FPL-Translation complementa bytecode/VM. |
| 59 | 1INF30 | LIBRERÍAS Y COMPONENTES REUTILIZABLES | KU-SE-Construction | correcta |  | El núcleo es generación/uso de componentes y frameworks reutilizables. Namespaces y paquetes son mecanismos de organización complementarios. |
| 60 | 1INF33 | SQL DDL | KU-DM-Relational | aceptable | KU-DM-Querying | DM-Relational cubre diseño e integridad, pero la definición y alteración de esquemas SQL se nombran expresamente en DM-Querying 3.a. |
| 61 | 1INF37 | DESARROLLO DE SOFTWARE AGIL | KU-SDF-Practices | incorrecta |  | SDF-Practices 1–4 no incluye manifiesto ágil, Scrum, Kanban, Lean, XP ni enfoques predictivo/adaptativo. SE-Teamwork cubre colaboración, pero no sustituye este conjunto metodológico. No se identificó una KU que lo cubra explícitamente. |
| 62 | 1INF24 | Algoritmos de búsqueda con información adicional | KU-AI-Search | correcta |  | Heurísticas, greedy best-first y A* están enumerados explícitamente. |
| 63 | 1INF37 | GESTIÓN DE CONFIGURACIÓN | KU-SE-Tools | correcta |  | Gestión de configuración e integración continua son tópicos explícitos. |
| 64 | 1INF50 | DISEÑO DE SOFTWARE | KU-SE-Design | correcta |  | Modelos, principios, patrones y notaciones de diseño son cobertura directa. |
| 65 | 1INF30 | PROGRAMACIÓN CON INTERFACES GRÁFICAS DE USUARIO | KU-SPD-Web | correcta |  | El sílabo especifica formularios e interfaces web. Tecnologías, componentes y DOM de la plataforma web cubren esa implementación; HCI-Design se centra en el diseño de la interacción. |
| 66 | 1INF37 | MANTENIMIENTO DE SOFTWARE | KU-SE-Refactoring | incorrecta | KU-SE-Construction | El núcleo es el proceso/metodologías/estándares de mantenimiento; no se acredita cobertura sustantiva por compatibilidad, versionado o refactorización. |
| 67 | 1INF32 | ALGORITMOS EVOLUTIVOS | KU-AL-Strategies | aceptable | KU-AI-Search | AL-Strategies cubre algoritmos aleatorios/estocásticos de forma general. AI-Search 17.b nombra exactamente algoritmos genéticos, que agrupan todos los conceptos del tema. |
| 68 | 1INF25 | ARREGLOS Y PUNTEROS | KU-FPL-Systems | correcta |  | Predominan representación/acceso mediante punteros y asignación dinámica de memoria. |
| 69 | 1INF31 | DISEÑANDO LA ARQUITECTURA | KU-SE-Design | correcta |  | Arquitectura, fronteras de componentes, trazabilidad y compromisos entre atributos de calidad cubren el núcleo. |
| 70 | 1INF29 | SEGURIDAD Y PROTECCIÓN | KU-OS-Protection | correcta |  | Backups, separación política/mecanismo, seguridad, acceso y autenticación son explícitos. |
| 71 | 1INF25 | PLANTILLAS Y BIBLIOTECA ESTÁNDAR DE PLANTILLAS | KU-FPL-Constructs | aceptable | KU-FPL-Types | FPL-Constructs cubre metaprogramación, aplicable a plantillas. FPL-Types 6 precisa tipos genéricos, parámetros genéricos y bibliotecas de colecciones; FPL-OOP 11 complementa contenedores/iteradores. |
| 72 | 1INF25 | PUNTEROS A OBJETOS | KU-FPL-OOP | correcta |  | Los punteros son el mecanismo; predominan polimorfismo, métodos virtuales, herencia y clases abstractas/autorreferenciadas. |
| 73 | 1INF31 | EVALUANDO LA ARQUITECTURA | KU-SE-Design | correcta |  | El título arquitectónico delimita qué se evalúa; la unidad incluye medir y analizar calidad de diseño y sus compromisos. |
| 74 | 1INF49 | CASOS DE USO, ESTÁNDARES Y AGILIDAD | KU-SE-Requirements | correcta |  | Casos de uso y comunicación/formalización de especificaciones son explícitos; estándares y agilidad son el contexto. |
| 75 | 1INF30 | PROGRAMACIÓN WEB | KU-SPD-Web | correcta |  | HTML, CSS y JavaScript están expresamente nombrados. |
| 76 | 1INF32 | ALGORITMOS BASADOS EN PROGRAMACIÓN BUTTON UP: PROGRAMACIÓN DINÁMICA | KU-AL-Strategies | correcta |  | Aunque no hay conceptos extraídos, el título identifica programación dinámica, nombrada expresamente. |
| 77 | 1INF54 | CONSTRUCCIÓN Y PRUEBA | KU-SE-Construction | correcta |  | El sílabo 1INF54, cap. 3, p. 3, combina construcción e integración con pruebas de aceptación. La construcción sigue siendo el saber principal, y SE-Construction incluye prácticas de código y pruebas a mayor escala. SE-Validation complementa aceptación. |
