# Reporte CP-16 · Relaciones entre conceptos

**Fecha:** 2026-11-22 · **Evaluador:** el autor · **Grafo:** corrida de medición del 2026-11-16 (`var/medicion-r4/`, tag `codigo-congelado-2026-11-16`)
**Guía aplicada:** `casos-de-prueba/guia-de-evaluacion-de-relaciones.md`, commit `998ff57` · **Planilla:** `casos-de-prueba/relaciones/juicio-de-relaciones-semilla-20261116.xlsx`

Medida descriptiva, sin umbral: no cambia el indicador de R4.

## Alcance

Muestra aleatoria de 30 aristas por tipo, con `random.Random(20261116).sample(range(N), 30)` sobre las aristas ordenadas por la clave de sus extremos (guía, «Qué se juzga»). Los índices están en la hoja «Muestra» de la planilla.

| Tipo | En el grafo | Juzgadas | Correctas | Incorrectas |
|---|---|---|---|---|
| Prerrequisito (`HAS_PREREQUISITE`) | 499 | 30 | 23 | 7 |
| Especialización (`SPECIALIZES`) | 94 | 30 | 30 | 0 |
| Concepto requerido (`REQUIRES_CONCEPT`) | 38 | 30 | 19 | 11 |

## Observaciones

- Especialización: las 30 aristas de la muestra son correctas.
- Prerrequisito: las siete incorrectas unen conceptos relacionados en los que uno no exige conocer el otro (por ejemplo, Bytecode y la compilación desde la línea de comandos); ninguna tiene la dirección invertida.
- Concepto requerido: en ocho de las once incorrectas el curso enseña el concepto, con otras palabras o dentro de otro tema; en las otras tres no lo necesita. En las 30 aristas, la columna «el curso también lo enseña» decía «no».

## Prerrequisito (`HAS_PREREQUISITE`)

| # | Origen | Destino | Juicio | Motivo |
|---|---|---|---|---|
| 3 | Árboles binarios de búsqueda | Árboles binarios | correcta | Para entender un árbol binario de búsqueda hay que conocer la estructura de un árbol binario y añadir su regla de orden. |
| 6 | Persistencia de objetos | Bases de datos | correcta | Aquí la persistencia es en una base de datos: sin conocerla no se entiende cómo guardar y recuperar los objetos. |
| 96 | Herramientas de Gestión de Configuración | Procesos de la gestión de configuración | correcta | El sentido y el mayor entendimiento de las herramientas depende de conocer el propósito de la gestión de configuración. |
| 107 | Estilo arquitectónico de microservicios | Estilos arquitectónicos | correcta | Para entender microservicios como estilo arquitectónico hay que conocer qué es un estilo y qué decisiones organiza. |
| 109 | Buferización | Memoria | correcta | La buferización guarda temporalmente datos en memoria; esa idea se necesita para entender qué hace un búfer. |
| 125 | Sistemas expertos | Motor de inferencia | correcta | El motor de inferencia es el componente que obtiene conclusiones a partir de la base de conocimiento; su función es necesaria para entender cómo trabaja un sistema experto. |
| 131 | Wireframes | Prototipado (UI Design) | incorrecta | Son conceptos amplios que se superponen y pueden entender por sí solos. |
| 164 | Modularidad | Construcción del software | incorrecta | La modularidad se puede entender al diseñar un sistema, antes de construirlo. Construcción y modularidad están relacionadas, pero una no exige conocer la otra. |
| 172 | Estilo arquitectónico de tuberías y filtros | Estilos arquitectónicos | correcta | Tuberías y filtros es un estilo arquitectónico concreto; presupone la idea general de estilo arquitectónico. |
| 182 | Hardware de manejo de memoria | Memoria física | correcta | Para entender el hardware que administra memoria hay que saber qué es la memoria física que gestiona. |
| 186 | Norma ISO 12207 | Procesos del ciclo de vida de software | correcta | ISO 12207 organiza procesos del ciclo de vida del software; conocer qué son esos procesos es necesario para entender la norma. |
| 207 | Despliegue de componentes en la nube | Despliegue | correcta | Desplegar en la nube es un caso de despliegue: primero hay que entender qué significa poner un componente en su entorno de ejecución. |
| 223 | Conexión a base de datos | Bases de datos | correcta | Una conexión permite acceder a una base de datos; no se entiende su propósito sin conocer qué es esa base de datos. |
| 257 | Estándares para el diseño de interfaces gráficas de usuario | Diseño de interfaz gráfica | correcta | Los estándares establecen reglas para diseñar interfaces; hay que conocer el objeto y la actividad a los que se aplican. |
| 258 | Parámetros | Variables | correcta | En el contexto de PL/SQL, los parámetros son variables de entrada o salida de una rutina; hace falta conocer variables para entenderlos. |
| 259 | Estrategias de búsqueda sobre tablas | Búsqueda | correcta | Buscar sobre tablas es un caso concreto del problema general de búsqueda. |
| 266 | Bytecode | Compilación de un programa desde la línea de comandos | incorrecta | Se puede entender el bytecode como código intermedio sin saber compilar desde la línea de comandos. Compilar así es una forma de producirlo, no un requisito conceptual. |
| 285 | Técnicas para el proceso de diseño de la Experiencia de Usuario | Proceso de diseño de la Experiencia Usuario (UX Design) | incorrecta | Se puede entender una persona o un empathy map sin conocerlo entero. |
| 287 | Herencia | Clases | correcta | La herencia relaciona clases y permite derivar unas de otras; no se entiende sin conocer clases. |
| 288 | Técnicas para el diseño de algoritmos | Algoritmos | correcta | Las técnicas de diseño explican cómo construir algoritmos; hay que saber qué es un algoritmo para entenderlas. |
| 294 | Método de inferencia Mandani | Defusificación | correcta | El método Mamdani obtiene una salida difusa y la convierte en una salida concreta mediante defusificación; esa etapa forma parte de su funcionamiento completo. |
| 321 | Tipos de requisitos | Requisitos de software | correcta | Para distinguir tipos de requisitos hay que conocer primero qué es un requisito de software. |
| 325 | Separación de política y mecanismo | Seguridad de sistema | incorrecta | Se puede entender la separación entre la política ("el qué se decide") y el mecanismo ("cómo se ejecuta") sin estudiar seguridad de sistemas. También se aplica, por ejemplo, a la planificación de procesos. |
| 331 | Algoritmo KNearest Neighbors (KNN) para regresión | Pipeline de aprendizaje automático supervisado | incorrecta | KNN para regresión puede entenderse como predecir a partir de vecinos cercanos sin conocer un pipeline completo de entrenamiento y evaluación. El pipeline ayuda a aplicarlo, pero no es requisito del algoritmo. |
| 352 | Formularios Web | HTML | correcta | En este curso son formularios web implementados con tecnologías web; su estructura y elementos se apoyan en HTML. Sílabo 1INF30 |
| 389 | Sobre escritura de métodos | Métodos | correcta | Sobrescribir consiste en redefinir un método heredado; no se entiende sin saber qué es un método. |
| 438 | Modelo Relacional | Modelos de base de datos | correcta | El modelo relacional es un modelo de base de datos concreto; se necesita la idea general para entender qué representa y organiza. |
| 476 | Herencia Múltiple | Clases | correcta | La herencia múltiple deriva una clase de varias clases base; exige conocer clases. |
| 480 | Estrategias de recorrido sobre grafos | Grafos | correcta | Recorrer un grafo supone conocer sus vértices y aristas; no se puede entender el recorrido sin esa estructura. |
| 484 | JavaScript | Funciones | incorrecta | Las funciones de PL/SQL del tema de destino no son necesarias para entender JavaScript. Un lenguaje puede enseñarse antes de introducir el mecanismo de las funciones. |

## Especialización (`SPECIALIZES`)

| # | Origen | Destino | Juicio | Motivo |
|---|---|---|---|---|
| 0 | Árboles binarios de búsqueda | Árboles binarios | correcta | Todo árbol binario de búsqueda es un árbol binario; añade una condición de orden. |
| 1 | Algoritmos Genéticos | Algoritmos | correcta | Los algoritmos genéticos son una familia de algoritmos. |
| 4 | Lean | Metodologías ágiles | correcta | En este contexto se refiere a Lean aplicado al desarrollo de software. El propio sílabo lo incluye entre las metodologías ágiles. 1INF37, p. 3, cap. 2. |
| 24 | Especificador de acceso a miembros protegido | Especificadores de acceso a miembros | correcta | "Protegido" es una clase de especificador de acceso a miembros. |
| 26 | Requerimientos de calidad | Requisitos de software | correcta | Un requerimiento de calidad es un requisito de software no funcional. |
| 27 | Requerimientos de modelamiento | Requisitos de software | correcta | Son requisitos que debe cumplir el modelo del software. |
| 28 | Estilo arquitectónico de tuberías y filtros | Estilos arquitectónicos | correcta | Tuberías y filtros es un tipo de estilo arquitectónico. |
| 31 | Interoperabilidad | Atributos de calidad | correcta | La interoperabilidad es un atributo de calidad del software en el contexto de arquitectura. |
| 32 | Eficiencia | Atributos de calidad | correcta | La eficiencia es un atributo de calidad del software. |
| 41 | Atributos estáticos | Atributos | correcta | Un atributo estático sigue siendo un atributo; se comparte a nivel de clase. |
| 43 | Clases anidadas | Clases | correcta | Una clase anidada es una clase declarada dentro de otra. |
| 45 | Reglas de inferencia difusa | Reglas | correcta | Una regla de inferencia difusa es un tipo de regla. |
| 46 | A* | Búsquedas heurísticas | correcta | Búsquedas heurísticas tiene en su familia de algoritmos a A*. |
| 51 | Archivos mapeados a memoria | Archivos | correcta | Un archivo mapeado a memoria sigue siendo un archivo; cambia cómo se accede a su contenido. |
| 55 | Llamadas al sistema para manejo de directorios | Llamadas al sistema | correcta | Las llamadas para manejar directorios son un tipo de llamada al sistema. |
| 58 | Clases abstractas | Clases | correcta | Una clase abstracta es un tipo de clase. |
| 64 | Diagramas de Clases de Diseño | Diagramas de clase de UML | correcta | Un diagrama de clases de diseño es un diagrama de clases UML usado para describir la solución, en vez del modelo conceptual. |
| 66 | Subconsultas escalares | Subconsultas | correcta | Una subconsulta escalar es una subconsulta cuyo resultado es un solo valor. |
| 71 | Algoritmo ABC | Algoritmos de inteligencia colectiva | correcta | ABC (Artificial Bee Colony) es un algoritmo de inteligencia colectiva inspirado en colonias de abejas. |
| 72 | Tablas hash | Tablas | correcta | Aquí "tablas" se refiere al TAD de Algoritmia, no a tablas relacionales. Una tabla hash es una tabla organizada mediante una función hash. |
| 73 | Requisitos en entornos ágiles | Requisitos de software | correcta | Los requisitos en entornos ágiles siguen siendo requisitos de software; cambia cómo se expresan y gestionan. |
| 74 | Modelos de madurez | Modelos de calidad de proceso software | correcta | En el contexto del tema, los modelos de madurez evalúan la capacidad/madurez del proceso software y forman parte de sus modelos de calidad. Sílabo 1INF37 |
| 79 | Clases auto referenciadas | Clases | correcta | Una clase autorreferenciada es una clase que contiene referencias a objetos de su propio tipo. |
| 80 | Cursores explícitos | Cursores | correcta | Un cursor explícito es un tipo de cursor declarado y gestionado por el programador. |
| 81 | Llamadas al sistema para manejo de procesos | Llamadas al sistema | correcta | Las llamadas para manejar procesos son un tipo de llamada al sistema. |
| 82 | Modelo Relacional | Modelos de base de datos | correcta | El modelo relacional es un tipo de modelo de base de datos. |
| 83 | Calidad en uso | Calidad | correcta | La calidad en uso es una forma de considerar la calidad del producto en su contexto de uso. |
| 85 | Memoria física | Memoria | correcta | La memoria física es un tipo de memoria, frente a abstracciones como la memoria virtual. |
| 88 | Sobrecarga de funciones no ligados a objetos | Sobrecarga de funciones | correcta | La sobrecarga de funciones no ligadas a objetos es un caso de sobrecarga de funciones. |
| 90 | Estilo arquitectónico basado en espacio | Estilos arquitectónicos | correcta | El estilo basado en espacio es un tipo de estilo arquitectónico. |

## Concepto requerido (`REQUIRES_CONCEPT`)

| # | Curso | Concepto | Juicio | Motivo |
|---|---|---|---|---|
| 0 | 1INF24 | Algoritmos | correcta | A nivel de concepto general, que es lo que se enseña en anteriores cursos, no este, es un concepto requerido. |
| 3 | 1INF27 | Clases auto referenciadas | incorrecta | Se enseña dentro. |
| 4 | 1INF27 | Memoria dinámica | correcta | Se asume sabido. |
| 6 | 1INF29 | Memoria | incorrecta | El curso lo enseña: el capítulo 6 desarrolla memoria física, paginación, memoria virtual y caché. No es solo conocimiento de entrada. Sílabo 1INF29 |
| 7 | 1INF30 | Métodos virtuales | correcta | No se enseña ni repasa. |
| 8 | 1INF30 | Punteros en herencia | incorrecta | No se acredita que lo necesite: el curso trabaja con Java y C#, cuyas referencias a objetos no exigen dominar punteros en herencia de C++. No aparece ese manejo como entrada. Sílabo 1INF30, unidades 1 y 2. |
| 9 | 1INF30 | Funciones | incorrecta | El curso usa Java/C#/JavaScript y no exige PL/SQL. Sílabo 1INF30: el destino está vinculado a 1INF33. |
| 11 | 1INF30 | Métodos | incorrecta | El curso también los desarrolla dentro de POO: clases, objetos, interfaces y sobrecarga de operaciones. No quedan solo como entrada. Sílabo 1INF30, unidad 2 |
| 13 | 1INF30 | Bases de datos | correcta | Necesita conocer bases de datos para programar persistencia, drivers y patrones de acceso. Esa unidad enseña el acceso desde una aplicación, no los fundamentos de modelos, SQL o diseño de BD. Sílabo 1INF30 |
| 15 | 1INF31 | Construcción del software | correcta | Necesita nociones de construcción para elegir frameworks/librerías que permitan implementar la arquitectura; el programa se centra en diseñar, documentar y evaluar esa arquitectura, no en enseñar su construcción. Sílabo 1INF31 |
| 16 | 1INF32 | Algoritmos | correcta | Como concepto general, lo asume, no lo vuelve a enseñar. |
| 18 | 1INF33 | Programación | correcta | Como concepto general, lo asume, no lo vuelve a enseñar. |
| 20 | 1INF37 | Atributos de calidad | correcta | Asume conocimiento. |
| 21 | 1INF37 | Requisitos de software | correcta | Asume conocimiento. |
| 22 | 1INF37 | Construcción del software | correcta | Asume conocimiento. |
| 23 | 1INF47 | Programación | correcta | Necesita saber programar para implementar e integrar módulos. El programa enseña herramientas y revisa avances, pero no introduce variables, control de flujo o funciones. Sílabo 1INF47 |
| 24 | 1INF47 | Diseño de interfaz gráfica | correcta | Necesita ese conocimiento para evaluar el diseño de las interfaces del proyecto; el programa no incluye enseñar técnicas de diseño de UI, sino revisar su aplicación. Sílabo 1INF47 |
| 25 | 1INF47 | Requisitos de software | correcta | Asume conocimiento. |
| 26 | 1INF49 | Programación | incorrecta | No se acredita que lo necesite: el curso trabaja con requisitos, modelos conceptuales y prototipos, sin exigir implementar programas. |
| 27 | 1INF49 | Clases | incorrecta | El curso también trabaja el concepto dentro del modelado con UML: diagramas de clases, relaciones y representación de conceptos. No queda solo como entrada. Sílabo 1INF49 |
| 28 | 1INF50 | Persistencia de objetos | incorrecta | El curso lo desarrolla con otros términos: RA2 selecciona patrones de persistencia y el cap. 3 enseña patrones de persistencia y de interacción con BD. Sílabo 1INF50, p. 2. |
| 29 | 1INF50 | Conexión a base de datos | correcta | Conectarse a una BD se da por conocido al estudiar patrones de interacción. |
| 30 | 1INF50 | Requisitos de software | correcta | Los requisitos son la entrada para seleccionar patrones y diseñar/pruebar los componentes; el programa no enseña a obtenerlos ni especificarlos. Sílabo 1INF50 |
| 31 | 1INF50 | Clases | incorrecta | El curso también desarrolla clases como elementos del diseño: enseña diagramas de clases de diseño, principios y patrones. Sílabo 1INF50 |
| 32 | 1INF50 | Relaciones entre clases | incorrecta | El curso también trabaja las relaciones al enseñar diagramas de clases de diseño y modelos de software. Quedan dentro del contenido desarrollado. Sílabo 1INF50 |
| 33 | 1INF50 | Construcción del software | incorrecta | El curso lo explica. |
| 34 | 1INF54 | Componentes | correcta | Se usan componentes al diseñar la arquitectura e integrar la solución. El programa los da por conocidos: no incluye una introducción al concepto de componente. Sílabo 1INF54, pp. 2–3, RA4 y caps. 2–3. |
| 35 | 1INF54 | Requisitos de software | correcta | Asume conocimiento. |
| 36 | 1INF54 | Construcción del software | correcta | Asume conocimiento. |
| 37 | 1INF54 | Procesos de la gestión de configuración | correcta | Se aplica como conocimiento previo. |
