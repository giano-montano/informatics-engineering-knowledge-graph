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
- **El mismo plan con el asesor y con los 3 usuarios.** La tarea se lee tal cual, sin nombrar
  botones ni vistas. El evaluador sigue los pasos esperados para observar, no para dictarlos.
- **Criterio global:** el 100 % de los casos aprobados, en cada sesión.

## Ejemplos: se fijan con el grafo final

Los ejemplos de hoy salen del grafo de desarrollo: el backbone de CS2023 y los 4 sílabos de
desarrollo (1INF01, 1INF35, INF144 e INF238). Cada valor marcado con **[SFG]** (*se fija con el
grafo final*) se revisa contra el grafo cargado con la corrida final de los 13 sílabos, antes de
la primera sesión: se confirma, o se cambia por un ejemplo equivalente de ese grafo. Lo que no
lleva la marca no depende de los datos.

Al fijarlos se anota aquí la fecha y la corrida del grafo final, y desde entonces el plan no
cambia entre sesiones.

| Grafo de los ejemplos | Corrida | Fecha |
|---|---|---|
| Desarrollo (4 sílabos), capturado de la API | — | 2026-10-29 |
| Final (13 sílabos) | *pendiente* | *pendiente* |

## Condiciones de la sesión

- R6 desplegado contra la API de R4, con el grafo de la corrida final cargado y reaplicado.
- La API sirve los PDF de los sílabos (`/resources/{clave}`): CA-07 y CA-10 abren uno.
- Navegador de escritorio, con la ventana de al menos 1366 × 768.
- Cada sesión empieza en el inicio de la aplicación, sin historial.
- Para CA-11, el token del operador y un sílabo en PDF para subir (ver ese caso).

## Qué cuenta como aprobado

Un caso se aprueba cuando el sistema muestra el resultado esperado de cada paso del caso, también
el de los pasos alternativos. Se registra aparte si el participante llegó solo o necesitó una
indicación del evaluador. La indicación no reprueba el caso, pero queda en el registro como
observación de uso.

Un caso se reprueba si el sistema muestra algo distinto de lo esperado (un dato que falta, uno de
más, una fuente equivocada, un enlace que no abre) o si falla (un error, una pantalla en blanco).

## Cobertura

La tesis pide al menos un caso de exploración por nodo y uno de acceso a recursos asociados
(§1.3.1.6). Cada clase de nodo es el foco de al menos un caso; el acceso a recursos son CA-07 y
CA-10.

| Clase | Casos en que es el foco |
|---|---|
| Área | CA-01, CA-06, CA-07 |
| Unidad | CA-05 |
| Tema | CA-01, CA-02, CA-06, CA-07 |
| Concepto | CA-02, CA-03, CA-05, CA-08, CA-09, CA-10 |
| Curso | CA-04, CA-08 |
| Recurso (sílabo, CS2023) | CA-07, CA-10 |

---

## CA-01 · Encontrar por dónde empezar (CU-1)

**Tarea.** «Quieres repasar lógica. Encuentra el tema de lógica proposicional y ábrelo.»

**Entrada.** Texto de búsqueda «lógica» [SFG]; texto sin coincidencias «árbol» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Entra a la aplicación sin escribir nada. | El inicio muestra las 17 áreas de CS2023 y los cursos con sílabo (4 [SFG]). Las áreas con temas de los sílabos se distinguen de las demás (7 [SFG]), con su número de temas y conceptos. |
| 2 | Busca «lógica». | Una lista de hasta 20 elementos cuyo nombre coincide (9 [SFG]), cada uno con su clase y su origen (CS2023 o sílabo). |
| 3 | Elige el tema «Lógica proposicional» [SFG]. | Queda en foco, en el centro del mapa, y el panel muestra su ficha. |
| 4 | *Alternativo:* busca «árbol». | El sistema dice que ningún sílabo cargado lo trata y ofrece ver las áreas. |

**Criterio.** Los cuatro resultados se cumplen; en el paso 2 la clase y el origen de cada
resultado se leen sin depender del color.

## CA-02 · Explorar lo que rodea a un elemento (CU-2)

**Tarea.** «Mira con qué se relaciona el tema de lógica proposicional, pasa a uno de sus conceptos
y vuelve al tema.»

**Entrada.** Tema «Lógica proposicional» [SFG]; concepto «Contradicción» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con el tema en foco, mira lo que lo rodea. | Sus vecinos directos (12 [SFG]), con el nombre de cada relación: «Contiene» (10 conceptos [SFG]), «Es parte de» (la unidad «Matemática Discreta» [SFG]) y «Material de estudio» (su sílabo [SFG]). Algunos vecinos de esos vecinos, apagados. |
| 2 | Pasa a «Contradicción». | «Contradicción» queda en foco, y lo visitado suma un paso. |
| 3 | Vuelve al tema. | El tema vuelve a estar en foco, con sus vecinos. |
| 4 | Pide más conexiones de un vecino que las tenga (marcado con +). | Sus conexiones se agregan al mapa con su nombre, y el foco no cambia. |

**Criterio.** Los cuatro resultados se cumplen, y cada vecino del mapa aparece también en la lista
«Conexiones» del panel.

## CA-03 · Saber qué conceptos necesito antes de aprender uno (CU-3)

**Tarea.** «Antes de estudiar Contradicción, averigua qué deberías saber, y por qué una de esas
cosas va antes.»

**Entrada.** Concepto «Contradicción» [SFG]; concepto sin prerrequisitos «Negación» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con «Contradicción» en foco, pregunta qué necesita antes. | Sus prerrequisitos ordenados por distancia: justo antes, «Tabla de verdad»; dos pasos antes, «Conjunción», «Disyunción» y «Negación» [SFG]. |
| 2 | Pregunta por qué «Tabla de verdad» va antes. | La relación «Contradicción necesita antes Tabla de verdad» con su fuente, el sílabo de 1INF01 [SFG]. |
| 3 | *Alternativo:* hace lo mismo con «Negación». | El sistema dice que no necesita nada antes y muestra qué depende de él («Tabla de verdad» [SFG]). |

**Criterio.** Los tres resultados se cumplen, sin prerrequisitos de más ni de menos frente a lo que
responde la API.

## CA-04 · Saber qué pide un curso y qué curso conviene llevar antes (CU-4)

**Tarea.** «Vas a llevar Técnicas de Programación. Averigua qué conocimientos asume y qué curso te
conviene llevar antes.»

**Entrada.** Curso «Técnicas de Programación» (INF144) [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con el curso en foco, pregunta qué pide y qué enseña. | Los conceptos que pide («Algoritmia», «Estructuras de control de flujo» y «Subprogramas» [SFG]) y los que enseña (43 [SFG]), con su nombre en el panel. |
| 2 | Pregunta qué curso conviene llevar antes. | «Fundamentos de Programación» (1INF01) [SFG], con los conceptos que lo justifican como evidencia, cada uno con su fuente. |

**Criterio.** Los dos resultados se cumplen, y cada curso previo viene con al menos un concepto
como evidencia.

## CA-05 · Ubicar un concepto o tema dentro de la carrera (CU-5)

**Tarea.** «Averigua en qué parte de la carrera está Contradicción, y abre la unidad a la que
pertenece.»

**Entrada.** Concepto «Contradicción» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con «Contradicción» en foco, pregunta dónde está. | La cadena área › unidad › tema: «Fundamentos Matemáticos y Estadísticos › Matemática Discreta › Lógica proposicional» [SFG]. |
| 2 | Elige la unidad. | «Matemática Discreta» [SFG] queda en foco, con su ficha. |

**Criterio.** Los dos resultados se cumplen, y cada eslabón muestra su capa: el área y la unidad
como CS2023, el tema y el concepto como sílabo.

## CA-06 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo (CU-6)

**Tarea.** «Mira qué conceptos tiene el tema de lógica proposicional y en qué orden conviene
aprenderlos. Después, mira qué contiene el área de redes.»

**Entrada.** Tema «Lógica proposicional» [SFG]; área «Redes y Comunicación» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con el tema en foco, pregunta qué contiene. | Sus conceptos (10 [SFG]). |
| 2 | Pregunta en qué orden aprenderlos. | Los conceptos agrupados en pasos según sus prerrequisitos internos (3 [SFG]): «Tabla de verdad» en el paso 2 y «Contradicción», «Contingencia» y «Tautología» en el paso 3 [SFG]. |
| 3 | Pone en foco el área y pregunta qué contiene. | Sus partes nivel por nivel: unidades y temas, con sus cifras (8 unidades, 14 temas y 132 conceptos [SFG]). Si son demasiados para leerse, el mapa llega hasta los temas y lo dice. |

**Criterio.** Los tres resultados se cumplen. En el paso 2, ningún concepto aparece en un paso
anterior a uno de sus prerrequisitos.

## CA-07 · Encontrar material de estudio sobre algo (CU-7)

**Tarea.** «Busca material para estudiar lógica proposicional y ábrelo. Luego intenta lo mismo con
Contradicción.»

**Entrada.** Tema «Lógica proposicional» [SFG]; concepto «Contradicción» [SFG]; área «Redes y
Comunicación» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con el tema en foco, pide material de estudio. | El sílabo de 1INF01 [SFG], con su tipo («Sílabo»). |
| 2 | Lo abre. | El PDF del sílabo abre en una pestaña nueva. |
| 3 | *Alternativo:* hace lo mismo con «Contradicción». | El sistema dice que un concepto no tiene material propio y ofrece el de su tema. |
| 4 | *Alternativo:* hace lo mismo con el área. | Los sílabos que tratan sobre sus partes (los de 1INF35 e INF238 [SFG]), cada uno con el tema por el que llega. |

**Criterio.** Los cuatro resultados se cumplen, y el PDF del paso 2 es el del curso indicado.

## CA-08 · Ver el camino hasta una meta, por temas, cursos o áreas (CU-8)

**Tarea.** «Quieres llegar a entender la entrada y salida de datos desde archivos. Averigua por qué
cursos te conviene pasar antes, y por qué.»

**Entrada.** Concepto «Entrada y salida de datos desde archivos» [SFG]; curso «Técnicas de
Programación» como meta [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Con el concepto en foco, pide el camino, por cursos. | Los cursos por los que conviene pasar, ordenados por distancia: «Administración de Sistemas Operativos» (1INF35) y «Técnicas de Programación» (INF144), a la misma distancia [SFG]; abajo, el concepto que se necesita antes («Archivos» [SFG]). |
| 2 | Lo cambia a temas y a áreas. | Por temas, «Administración local» e «Ingreso y salida de datos»; por áreas, «Fundamentos del Desarrollo de Software» y «Sistemas Operativos» [SFG]. Una parada que contiene a la meta lo dice. |
| 3 | Pregunta por qué pasar por un curso del camino. | Las relaciones que lo justifican, cada una con su fuente: el curso enseña «Archivos» (sílabo de 1INF35) y la meta lo necesita antes (sílabo de INF144) [SFG]. |
| 4 | *Alternativo:* pide el camino con un curso como meta. | El sistema explica que sale vacío y remite a «Cursos que conviene llevar antes» (CA-04). |

**Criterio.** Los cuatro resultados se cumplen, y el cambio de agrupación no cambia el concepto
que se necesita antes.

## CA-09 · Ver de qué es un tipo un concepto y qué tipos tiene (CU-9)

**Tarea.** «Averigua qué tipos de Ethernet hay, y de qué es un tipo uno de ellos.»

**Entrada.** Concepto «Ethernet IEEE 802.3» [SFG]; uno de sus tipos, «FastEthernet» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Busca «ethernet» y abre «Ethernet IEEE 802.3». | Queda en foco. |
| 2 | Pregunta por sus tipos. | «FastEthernet», «Gigabit Ethernet» y «10GigabitEthernet» [SFG]. |
| 3 | Pasa a «FastEthernet» y pregunta de qué es un tipo. | «Ethernet IEEE 802.3». |
| 4 | *Alternativo:* pregunta por los tipos de un concepto que no tiene. | El sistema dice que no tiene tipos registrados. |

**Criterio.** Los cuatro resultados se cumplen.

## CA-10 · Comprobar de dónde sale un dato (CU-10)

**Tarea.** «El sistema dice que Contradicción necesita antes Tabla de verdad. Comprueba en qué
documento se dice eso y ábrelo.»

**Entrada.** Relación «Contradicción necesita antes Tabla de verdad» [SFG]; unidad «Matemática
Discreta» [SFG].

| # | Paso | Resultado esperado |
|---|---|---|
| 1 | Pregunta de dónde sale la relación. | Nombra el documento que la afirma: el sílabo de 1INF01 [SFG]. |
| 2 | Lo abre. | Abre el PDF de ese sílabo en una pestaña nueva. |
| 3 | Pregunta de dónde sale un elemento de CS2023, como la unidad. | Nombra CS2023 y enlaza su publicación de ACM. |

**Criterio.** Los tres resultados se cumplen. El paso 2 es la prueba de aceptación que cierra AC-03
en R6 (Tabla 23 de la tesis).

---

## CA-11 · Cargar un documento y revisar su ingesta (CU-11)

**RF-23 está hoy fuera de la prueba de aceptación de R6:** lo dicen
`docs/requisitos-funcionales-de-referencia.md` §5 y la descripción de `kms.web` en
`docs/architecture/model.c4`. Este caso se incluye en el plan; falta decidir si cuenta para el
100 % y con quién se ejecuta.

**Condición propia.** Una carga escribe en el grafo. Se ejecuta en un entorno de ensayo, no sobre
el grafo de la corrida final que usan los demás casos.

**Tarea.** «Eres el operador. Entra con tu token, sube este sílabo y comprueba cómo terminó su
ingesta.»

**Entrada.** Un token inválido; el token del operador; un sílabo en PDF con su tipo («Sílabo»), su
código y su nombre de curso [SFG].

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

## Registro de una sesión

Se llena uno por sesión, con el asesor o con cada usuario.

```markdown
# Sesión de aceptación de R6 · <asesor | usuario N>

**Fecha:** AAAA-MM-DD · **Evaluador:** … · **Participante:** <rol; ciclo, si es estudiante>
**R6:** commit … · **Grafo:** corrida … · **Navegador y pantalla:** …

| Caso | Resultado | Ayuda | Observaciones |
|---|---|---|---|
| CA-01 | aprobado / reprobado | ninguna / indicación | |
| … | | | |

**Aprobados:** n de N (…%)
```
