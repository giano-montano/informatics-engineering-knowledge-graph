# Plan de pruebas de aceptación de R6

## Propósito

Verifica que el prototipo de navegación (R6) responde correctamente a cada caso de uso del
mecanismo de navegación. Es el medio de verificación de R6 («casos de prueba documentados y sus
resultados», Tabla 4 de la tesis) y aplica la Fase 2 del procedimiento de R6 (§1.3.1.6): cada caso
especifica la entrada, la acción esperada y el criterio de aceptación.

- **Un caso por flujo.** Cada caso es una tarea, y cada tarea es el flujo de un caso de uso de
  `docs/r5/casos-de-uso.md`: CA-01 a CA-10 para el estudiante (CU-1 a CU-10) y CA-11 para el
  operador (CU-11). Los flujos que se recorren son los de la propuesta elegida,
  `docs/r5/p1-lienzo/README.md` §2.
- **El mismo plan con el asesor y con los 3 usuarios.** La tarea se lee tal cual, con los datos de
  la hoja vigente, sin nombrar botones ni vistas. El evaluador sigue los pasos esperados para
  observar, no para dictarlos.
- **Criterio global:** el 100 % de los casos CA-01 a CA-10 aprobados, en cada sesión. CA-11 no
  cuenta para ese 100 %.

## Casos y datos

El plan tiene dos partes, y cada una cambia por un motivo distinto.

- **Los casos** dicen qué se hace y qué debe responder el sistema, sin nombrar ningún elemento del
  grafo. Donde hace falta un elemento, el caso lo nombra por su papel, entre ángulos: ⟨tema⟩,
  ⟨concepto⟩, ⟨curso⟩. Cambian solo si cambia un caso de uso.
- **La hoja de datos** dice qué elemento ocupa cada papel y qué resultado concreto se espera de
  cada paso. Depende del grafo cargado: si el grafo cambia, se reemplaza la hoja y los casos no se
  tocan.

Un caso se ejecuta siempre con una hoja: la tarea que oye el participante es la del caso con los
nombres de la hoja. La hoja se fija antes de la primera sesión y no cambia entre sesiones.

## Condiciones de la sesión

- R6 desplegado contra la API de R4, con el grafo de la hoja de datos cargado y reaplicado.
- La API sirve los PDF de los sílabos (`/resources/{clave}`): CA-07 y CA-10 abren uno.
- Navegador de escritorio, con la ventana de al menos 1366 × 768.
- Cada sesión empieza en el inicio de la aplicación, sin historial.

## Qué cuenta como aprobado

Un caso se aprueba cuando el sistema muestra el resultado esperado de cada paso del caso, también
el de los pasos alternativos. Se registra aparte si el participante llegó solo o necesitó una
indicación del evaluador. La indicación no reprueba el caso, pero queda en el registro como
observación de uso.

Un caso se reprueba si el sistema muestra algo distinto de lo esperado (un dato que falta, uno de
más, una fuente equivocada, un enlace que no abre) o si falla (un error, una pantalla en blanco).

## Cobertura

La tesis pide al menos un caso de exploración por nodo y uno de acceso a recursos asociados
(§1.3.1.6). La exploración de nodo en nodo es CA-02; el acceso a recursos, CA-07 y CA-10.

---

## CA-01 · Encontrar por dónde empezar (CU-1)

**Tarea.** «Quieres repasar ⟨asunto⟩. Encuentra el tema ⟨tema⟩ y ábrelo.»

**Entrada.** Un ⟨texto de búsqueda⟩ que coincide con el nombre de ⟨tema⟩; un ⟨texto sin
coincidencias⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Entra a la aplicación sin escribir nada. | El inicio muestra las 17 áreas de CS2023 y los cursos con sílabo. Las áreas con temas de los sílabos se distinguen de las demás, con su número de temas y conceptos. |
| 2 | Busca ⟨texto de búsqueda⟩. | Una lista de hasta 20 elementos cuyo nombre coincide, cada uno con su clase y su origen (CS2023 o sílabo). |
| 3 | Elige ⟨tema⟩. | Queda en foco, en el centro del mapa, y el panel muestra su ficha. |
| 4 | *Alternativo:* busca ⟨texto sin coincidencias⟩. | El sistema dice que nada coincide y ofrece ver las áreas. |

**Criterio.** Los cuatro resultados se cumplen; en el paso 2 la clase y el origen de cada
resultado se leen sin depender del color.

## CA-02 · Explorar lo que rodea a un elemento (CU-2)

**Tarea.** «Mira con qué se relaciona el tema ⟨tema⟩, pasa a uno de sus conceptos y vuelve al
tema.»

**Entrada.** ⟨tema⟩; uno de sus conceptos, ⟨concepto⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨tema⟩ en foco, mira lo que lo rodea. | Sus vecinos directos, con el nombre de cada relación: lo que contiene, de qué es parte y su material de estudio. Algunos vecinos de esos vecinos, apagados. |
| 2 | Pasa a ⟨concepto⟩. | ⟨concepto⟩ queda en foco, y lo visitado suma un paso. |
| 3 | Vuelve al tema. | El tema vuelve a estar en foco, con sus vecinos. |
| 4 | Pide más conexiones de un vecino que las tenga (marcado con +). | Sus conexiones se agregan al mapa con su nombre, y el foco no cambia. |

**Criterio.** Los cuatro resultados se cumplen, y cada vecino del mapa aparece también en la lista
«Conexiones» del panel.

## CA-03 · Saber qué conceptos necesito antes de aprender uno (CU-3)

**Tarea.** «Antes de estudiar ⟨concepto⟩, averigua qué deberías saber, y por qué una de esas
cosas va antes.»

**Entrada.** ⟨concepto⟩, con prerrequisitos a más de un paso; ⟨concepto sin prerrequisitos⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨concepto⟩ en foco, pregunta qué necesita antes. | Sus prerrequisitos ordenados por distancia: los directos y los que están más pasos atrás. |
| 2 | Pregunta por qué su prerrequisito directo va antes. | La relación entre los dos, con su fuente. |
| 3 | *Alternativo:* hace lo mismo con ⟨concepto sin prerrequisitos⟩. | El sistema dice que no necesita nada antes y muestra qué depende de él. |

**Criterio.** Los tres resultados se cumplen, sin prerrequisitos de más ni de menos frente a lo que
responde la API.

## CA-04 · Saber qué pide un curso y qué curso conviene llevar antes (CU-4)

**Tarea.** «Vas a llevar ⟨curso⟩. Averigua qué conocimientos asume y qué curso te conviene llevar
antes.»

**Entrada.** ⟨curso⟩, que pide al menos un concepto que otro curso enseña.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨curso⟩ en foco, pregunta qué pide y qué enseña. | Los conceptos que pide y los que enseña, con su nombre en el panel. |
| 2 | Pregunta qué curso conviene llevar antes. | Los cursos que enseñan lo que este pide, cada uno con esos conceptos como evidencia, y cada concepto con su fuente. |

**Criterio.** Los dos resultados se cumplen, y cada curso previo viene con al menos un concepto
como evidencia.

## CA-05 · Ubicar un concepto o tema dentro de la carrera (CU-5)

**Tarea.** «Averigua en qué parte de la carrera está ⟨concepto⟩.»

**Entrada.** ⟨concepto⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨concepto⟩ en foco, pregunta dónde está. | La cadena área › unidad › tema a la que pertenece. |

**Criterio.** El resultado se cumple, y cada eslabón muestra su capa: el área y la unidad
como CS2023, el tema y el concepto como sílabo.

## CA-06 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo (CU-6)

**Tarea.** «Mira qué conceptos tiene el tema ⟨tema⟩ y en qué orden conviene aprenderlos. Después,
mira qué contiene el área ⟨área⟩.»

**Entrada.** ⟨tema⟩, con prerrequisitos entre sus conceptos; ⟨área⟩, con temas de los sílabos.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨tema⟩ en foco, pregunta qué contiene. | Sus conceptos. |
| 2 | Pregunta en qué orden aprenderlos. | Los conceptos agrupados en pasos según los prerrequisitos que hay entre ellos. |
| 3 | Pone en foco ⟨área⟩ y pregunta qué contiene. | Sus partes nivel por nivel: unidades y temas, con sus cifras. Si son demasiados para leerse, el mapa llega hasta los temas y lo dice. |

**Criterio.** Los tres resultados se cumplen. En el paso 2, ningún concepto aparece en un paso
anterior a uno de sus prerrequisitos.

## CA-07 · Encontrar material de estudio sobre algo (CU-7)

**Tarea.** «Busca material para estudiar ⟨tema⟩ y ábrelo. Luego intenta lo mismo con ⟨concepto⟩.»

**Entrada.** ⟨tema⟩; ⟨concepto⟩; ⟨área con varios sílabos⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨tema⟩ en foco, pide material de estudio. | El sílabo que trata sobre él, con su tipo («Sílabo»). |
| 2 | Lo abre. | El PDF del sílabo abre en una pestaña nueva. |
| 3 | *Alternativo:* hace lo mismo con ⟨concepto⟩. | El sistema dice que un concepto no tiene material propio y ofrece el de su tema. |
| 4 | *Alternativo:* hace lo mismo con ⟨área con varios sílabos⟩. | Los sílabos que tratan sobre sus partes, cada uno con el tema por el que llega. |

**Criterio.** Los cuatro resultados se cumplen, y el PDF del paso 2 es el del curso indicado.

## CA-08 · Ver el camino hasta una meta, por temas, cursos o áreas (CU-8)

**Tarea.** «Quieres llegar a entender ⟨concepto⟩. Averigua por qué cursos te conviene pasar antes,
y por qué.»

**Entrada.** ⟨concepto⟩ como meta, con prerrequisitos que se enseñan en más de un curso; ⟨curso⟩
como meta.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con ⟨concepto⟩ en foco, pide el camino, por cursos. | Los cursos por los que conviene pasar, ordenados por distancia, y los conceptos que se necesitan antes. |
| 2 | Lo cambia a temas y a áreas. | El mismo camino agrupado en temas y en áreas. Una parada que contiene a la meta lo dice. |
| 3 | Pregunta por qué pasar por un curso del camino. | Las relaciones que lo justifican, cada una con su fuente: el curso enseña un concepto y la meta lo necesita antes. |
| 4 | *Alternativo:* pide el camino con ⟨curso⟩ como meta. | El camino que sale de lo que necesitan antes los conceptos que el curso enseña, o el aviso de que sale vacío. En los dos casos, el sistema remite a «Cursos que conviene llevar antes» (CA-04). |

**Criterio.** Los cuatro resultados se cumplen, y el cambio de agrupación no cambia los conceptos
que se necesitan antes.

**Nota al paso 4.** Para un curso hay dos respuestas, y pueden no coincidir. «Cursos que conviene
llevar antes» parte de lo que el curso pide (PC2). «Camino hasta aquí» parte de lo que necesitan
antes los conceptos que el curso enseña (PC6). El sistema dice cuál es cuál; que difieran no
reprueba el caso.

## CA-09 · Ver de qué es un tipo un concepto y qué tipos tiene (CU-9)

**Tarea.** «Averigua qué tipos de ⟨concepto general⟩ hay, y de qué es un tipo uno de ellos.»

**Entrada.** ⟨concepto general⟩, con al menos dos tipos; ⟨concepto sin tipos⟩.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Busca ⟨concepto general⟩ y lo abre. | Queda en foco. |
| 2 | Pregunta por sus tipos. | Los conceptos que son tipos de él. |
| 3 | Pasa a uno de ellos y pregunta de qué es un tipo. | ⟨concepto general⟩. |
| 4 | *Alternativo:* pregunta por los tipos de ⟨concepto sin tipos⟩. | El sistema dice que no tiene tipos registrados. |

**Criterio.** Los cuatro resultados se cumplen.

## CA-10 · Comprobar de dónde sale un dato (CU-10)

**Tarea.** «El sistema dice que ⟨concepto⟩ necesita antes ⟨prerrequisito⟩. Comprueba en qué
documento se dice eso y ábrelo.»

**Entrada.** La relación entre ⟨concepto⟩ y su prerrequisito directo; ⟨unidad⟩, de CS2023.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Pregunta de dónde sale la relación. | Nombra el documento que la afirma: el sílabo de un curso. |
| 2 | Lo abre. | Abre el PDF de ese sílabo en una pestaña nueva. |
| 3 | Pregunta de dónde sale ⟨unidad⟩. | Nombra CS2023 y enlaza su publicación de ACM. |

**Criterio.** Los tres resultados se cumplen. El paso 2 es la prueba de aceptación que cierra AC-03
en R6 (Tabla 23 de la tesis).

---

## CA-11 · Cargar un documento y revisar su ingesta (CU-11)

**Fuera del 100 %.** La prueba de aceptación de R6 evalúa la exploración y el acceso a recursos
del estudiante. Este caso se ejecuta solo con el asesor, como demostración del panel del operador,
y se registra aparte.

**Condiciones propias.** Una carga escribe en el grafo: se ejecuta en un entorno de ensayo, no
sobre el grafo de la hoja de datos que usan los demás casos. El caso verifica el panel, no la
extracción, así que el proveedor del modelo de lenguaje puede ir simulado. Hacen falta el token
del operador y un sílabo en PDF para subir.

**Tarea.** «Eres el operador. Entra con tu token, sube este sílabo y comprueba cómo terminó su
ingesta.»

**Entrada.** Un token inválido; el token del operador; un sílabo en PDF con su tipo («Sílabo»), su
código y su nombre de curso.

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Entra con un token inválido. | El sistema lo rechaza y no da acceso. |
| 2 | Entra con el token del operador. | Da acceso a la operación y muestra el estado de la compuerta de auditoría. |
| 3 | Sube el sílabo con su tipo, código y nombre de curso. | Registra una corrida nueva, pendiente. |
| 4 | Sigue el estado de sus corridas. | La corrida avanza hasta un estado final, con su duración. |
| 5 | Revisa la corrida. | Sus descartes, o el aviso de que no hubo, y su reporte de auditoría regla por regla. |

**Criterio.** Los cinco resultados se cumplen, y el estado final que muestra el panel es el que
registra el almacén operacional para esa corrida.

---

## Hoja de datos

| Hoja | Grafo | Capturada de la API | Estado |
|---|---|---|---|
| 1 | Desarrollo: CS2023 y 4 sílabos (1INF01, 1INF35, INF144 e INF238) | 2026-10-29 | Retirada. Está en el historial de este archivo. |
| 2 | Corrida final de R4: CS2023 y los 13 sílabos (2026-11-16) | 2026-11-17 | **Vigente** |

### Hoja 2 · Grafo de la corrida final

Los nombres van como están en el grafo, que los toma del sílabo: un tema puede venir en mayúsculas
y un concepto, con un espacio de más («Hiperpaginación (thrashing )»). No se corrigen, porque es el
grafo sobre el que se midió R4.

**Papeles**

| Papel | Elemento | Casos |
|---|---|---|
| ⟨asunto⟩ | cómo administra la memoria un sistema operativo | CA-01 |
| ⟨texto de búsqueda⟩ | «memoria» | CA-01 |
| ⟨texto sin coincidencias⟩ | «compiladores» | CA-01 |
| ⟨tema⟩ | «ADMINISTRACIÓN DE MEMORIA», del sílabo de 1INF29 | CA-01, 02, 06, 07 |
| ⟨concepto⟩ | «Memoria virtual», de ese tema | CA-02, 03, 05, 07, 08, 10 |
| ⟨prerrequisito⟩ | «Paginación» | CA-03, 10 |
| ⟨concepto sin prerrequisitos⟩ | «Memoria», del sílabo de 1INF25 | CA-03 |
| ⟨curso⟩ | «Sistemas Operativos» (1INF29) | CA-04, 08 |
| ⟨área⟩ | «Sistemas Operativos» | CA-06 |
| ⟨área con varios sílabos⟩ | «Fundamentos Algorítmicos» | CA-07 |
| ⟨concepto general⟩ | «Llamadas al sistema» | CA-09 |
| ⟨concepto sin tipos⟩ | «Memoria virtual» | CA-09 |
| ⟨unidad⟩ | «Gestión de Memoria» | CA-10 |

**Resultados esperados**

| Caso · paso | Resultado con esta hoja |
|---|---|
| CA-01 · 1 | 13 cursos con sílabo; 10 de las 17 áreas tienen temas de los sílabos. |
| CA-01 · 2 | 11 resultados: 7 conceptos y 1 tema de los sílabos, y 3 unidades de CS2023. |
| CA-01 · 4 | Ningún resultado para «compiladores». |
| CA-02 · 1 | 9 vecinos directos: «Contiene», 7 conceptos; «Es parte de», la unidad «Gestión de Memoria»; «Material de estudio», «Sílabo 1INF29». |
| CA-03 · 1 | Justo antes, «Paginación»; a dos pasos, «Hardware de manejo de memoria»; a tres, «Memoria física»; a cuatro, «Memoria». |
| CA-03 · 2 | «Memoria virtual necesita antes Paginación», con fuente «Sílabo 1INF29». |
| CA-03 · 3 | «Memoria» no necesita nada antes; dependen de él «Memoria dinámica», «Memoria física», «Caching» y «Buferización». |
| CA-04 · 1 | Pide «Memoria» y «Programación»; enseña 63 conceptos. |
| CA-04 · 2 | «Programación 2» (1INF25), que enseña «Memoria», y «Algoritmia y Estructura de Datos» (1INF27), que enseña «Programación». |
| CA-05 · 1 | «Sistemas Operativos › Gestión de Memoria › ADMINISTRACIÓN DE MEMORIA». |
| CA-06 · 1 | 7 conceptos. |
| CA-06 · 2 | 6 pasos: «Memoria física» y «Caching»; «Hardware de manejo de memoria»; «Paginación»; «Memoria virtual»; «Conjuntos de trabajo (working sets )»; «Hiperpaginación (thrashing )». |
| CA-06 · 3 | 14 unidades, 6 temas y 63 conceptos. |
| CA-07 · 1 | «Sílabo 1INF29», de tipo «Sílabo». |
| CA-07 · 4 | Los sílabos de 1INF24, 1INF27 y 1INF32. |
| CA-08 · 1 | «Sistemas Operativos» (1INF29), a un paso, y «Programación 2» (1INF25), a cuatro. Se necesitan antes «Paginación», «Hardware de manejo de memoria», «Memoria física» y «Memoria». |
| CA-08 · 2 | Por temas, «ADMINISTRACIÓN DE MEMORIA» y «ARREGLOS Y PUNTEROS»; por áreas, «Sistemas Operativos» y «Fundamentos de los Lenguajes de Programación». El curso, el tema y el área de 1INF29 contienen a la meta. |
| CA-08 · 3 | Para «Programación 2»: el curso enseña «Memoria» (sílabo de 1INF25) y «Memoria física» lo necesita antes (sílabo de 1INF29). |
| CA-08 · 4 | El camino no sale vacío: pasa por «Programación 2» (1INF25), «Algoritmia y Estructura de Datos» (1INF27) y «Programación 3» (1INF30). «Cursos que conviene llevar antes» da los dos primeros. |
| CA-09 · 2 | «Llamadas al sistema para manejo de procesos», «… de archivos» y «… de directorios». |
| CA-10 · 1 | «Sílabo 1INF29». |

---

## Registro de una sesión

Se llena uno por sesión, con el asesor o con cada usuario.

```markdown
# Sesión de aceptación de R6 · <asesor | usuario N>

**Fecha:** AAAA-MM-DD · **Evaluador:** … · **Participante:** <rol; ciclo, si es estudiante>
**R6:** commit … · **Hoja de datos:** … · **Navegador y pantalla:** …

| Caso | Resultado | Ayuda | Observaciones |
|---|---|---|---|
| CA-01 | aprobado / reprobado | ninguna / indicación | |
| … | | | |

**Aprobados:** n de 10 (…%), sin contar CA-11
```
