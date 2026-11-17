# R6 · InfoKnows: capturas y recorrido técnico

**Fecha:** 2026-11-17 · **Grafo:** corrida final de R4 (CS2023 y los 13 sílabos; hoja de datos 2 del
plan) · **Navegador:** Chromium sin interfaz, con Playwright 1.65.1, a 1440 × 900. Las capturas O1 a
O6 y la sección 4 son del 2026-11-15, sobre el grafo de desarrollo y con el aspecto anterior.

La aplicación está en [`web/`](../../web/README.md). Aquí quedan las capturas de sus pantallas y el
resultado de recorrer los casos del
[plan de pruebas de aceptación](../../casos-de-prueba/plan-de-pruebas-de-aceptacion-r6.md).

> **Esto no es la prueba de aceptación.** Es un recorrido técnico previo y automático. La prueba de
> aceptación la hacen personas, el asesor y tres usuarios, y es la única que cuenta para el indicador
> de R6. Este recorrido solo dice que cada paso del plan se puede dar y que la interfaz muestra lo que
> responde la API.

## 1. Capturas

Con el nombre de la captura equivalente de R5 (`docs/r5/p1-lienzo/capturas/`) donde la hay.

| Captura | Qué muestra | Caso de uso |
|---|---|---|
| [`A-inicio`](capturas/A-inicio.png) | Las 17 áreas y los 13 cursos, sin buscar; en el panel, lo mismo como lista | CU-1 |
| [`B1-busqueda`](capturas/B1-busqueda.png) | «memoria»: 11 resultados, con su clase y su capa en texto | CU-1 |
| [`B2-busqueda-sin-resultados`](capturas/B2-busqueda-sin-resultados.png) | «compiladores»: el estado vacío, con «Ver las áreas» | CU-1 |
| [`C-foco-lo-que-lo-rodea`](capturas/C-foco-lo-que-lo-rodea.png) | «ADMINISTRACIÓN DE MEMORIA» con sus 9 vecinos en dos alas | CU-2 |
| [`C2-conexiones-traidas-con-mas`](capturas/C2-conexiones-traidas-con-mas.png) | Lo que trae el **+** de un vecino, abajo, sin cambiar el foco (sin equivalente en R5) | CU-2 |
| [`D1-que-contiene-tema`](capturas/D1-que-contiene-tema.png) | Sus 7 conceptos en 6 pasos | CU-6 |
| [`D2-que-necesitas-antes`](capturas/D2-que-necesitas-antes.png) | «Memoria virtual»: 4 conceptos, el más lejano a 4 pasos | CU-3 |
| [`D3-donde-esta-en-la-carrera`](capturas/D3-donde-esta-en-la-carrera.png) | La cadena área › unidad › tema › concepto | CU-5 |
| [`D4-camino-hasta-aqui-por-curso`](capturas/D4-camino-hasta-aqui-por-curso.png) | «Memoria virtual», por curso, con la línea de paradas | CU-8 |
| [`D5-cursos-que-conviene-llevar-antes`](capturas/D5-cursos-que-conviene-llevar-antes.png) | «Sistemas Operativos»: los cursos previos, lo que pide y lo que enseña | CU-4 |
| [`D6-que-contiene-area`](capturas/D6-que-contiene-area.png) | El área «Sistemas Operativos» como árbol hasta los temas | CU-6 |
| [`D7-material-de-estudio`](capturas/D7-material-de-estudio.png) | Los sílabos que tratan sobre «Fundamentos Algorítmicos» y por qué tema llega cada uno | CU-7 |
| [`D8-tipos`](capturas/D8-tipos.png) | «Llamadas al sistema» y sus 3 tipos | CU-9 |
| [`E-panel-del-foco`](capturas/E-panel-del-foco.png) | La ficha de «ADMINISTRACIÓN DE MEMORIA» | CU-5 a CU-7, CU-10 |
| [`E-panel-del-foco-cs2023`](capturas/E-panel-del-foco-cs2023.png) | La ficha de un elemento de CS2023, con el enlace a la publicación de ACM (sin equivalente) | CU-10 |
| [`F1-relacion-seleccionada`](capturas/F1-relacion-seleccionada.png) | «Memoria virtual necesita antes Paginación», con su sílabo | CU-10 |
| [`F2-por-que-de-una-parada`](capturas/F2-por-que-de-una-parada.png) | El «¿Por qué?» de una parada del camino, con sus relaciones y fuentes | CU-8, CU-10 |
| [`F3-fuentes-en-el-mapa`](capturas/F3-fuentes-en-el-mapa.png) | El interruptor «Fuentes»: cada elemento unido a su documento (sin equivalente) | CU-10 |
| [`O1-acceso-rechazado`](capturas/O1-acceso-rechazado.png) | El acceso del operador rechaza un token inválido | CU-11 |
| [`O2-panel-del-operador`](capturas/O2-panel-del-operador.png) | El panel: compuerta de auditoría, carga y corridas | CU-11 |
| [`O3-corrida-registrada`](capturas/O3-corrida-registrada.png) | Una corrida recién registrada, pendiente | CU-11 |
| [`O4-detalle-de-la-corrida`](capturas/O4-detalle-de-la-corrida.png) | El resumen de una corrida que terminó como fallida | CU-11 |
| [`O5-auditoria-de-cierre`](capturas/O5-auditoria-de-cierre.png), [`O6-descartes`](capturas/O6-descartes.png) | Sus pestañas de auditoría de cierre y de descartes, vacías | CU-11 |

## 2. Recorrido técnico de CA-01 a CA-10

`web/tests/walkthrough.mjs` da cada paso del plan dos veces: con el puntero y **solo con el teclado**
(Tab, flechas, Enter, `+`, `Ctrl K` y `Alt ←`; sin ratón). Usa los casos genéricos del plan con su
hoja de datos 2, y donde el plan pide un dato lo compara con lo que responde la API en ese momento.
Se corrió contra el despliegue con Docker Compose, detrás de nginx: **66 de 66 comprobaciones
cumplen**.

El paso 4 de CA-10 no está en el plan: comprueba el interruptor «Fuentes» del flujo de CU-10.

| Caso | Paso | Resultado esperado | Con puntero | Solo teclado | Lo que se vio |
|---|---|---|---|---|---|
| CA-01 | 1 | El inicio muestra las 17 áreas y los cursos con sílabo; las áreas con temas se distinguen, con sus cifras | cumple | cumple | 17 áreas, 13 cursos, 10 áreas con temas; 2 temas · 17 conceptos |
| CA-01 | 2 | La búsqueda lista hasta 20 coincidencias, cada una con su clase y su origen en texto | cumple | cumple | 11 resultados para «memoria»: Memoria virtual (Concepto, Sílabo PUCP); Hardware de manejo de memoria (Concepto, Sílabo PUCP); ADMINISTRACIÓN DE MEMORIA (Tema, Sílabo PUCP); Archivos mapeados a memoria (Concepto, Sílabo PUCP); Memoria (Concepto, Sílabo PUCP); Memoria dinámica (Concepto, Sílabo PUCP); Memoria física (Con |
| CA-01 | 3 | Elegir el tema lo pone en foco, en el mapa y en la ficha | cumple | cumple | Tema ADMINISTRACIÓN DE MEMORIA, de un sílabo. En foco |
| CA-01 | 4 | Un texto sin coincidencias: el sistema lo dice y ofrece ver las áreas | cumple | cumple | Ningún sílabo cargado trata «compiladores»  Tampoco hay un área o una unidad de CS2023 con ese nombre. Prueba con otra palabra o recorre las áreas.  Ver las áreas PRESENTACIÓN DEL CURSO Y CONCEPTOS BÁSICOS HTML Clases Plan de riesgo |
| CA-02 | 1 | Vecinos directos con el nombre de cada relación, y algunos vecinos de esos vecinos, apagados; cada vecino del mapa está en «Conexiones» | cumple | cumple | Aquí ves con qué se relaciona ADMINISTRACIÓN DE MEMORIA: 9 elementos conectados directamente, agrupados por tipo de relación. Rótulos: Es parte de, Material de estudio, Contiene · 7. Apagados: 9. Fuera de «Conexiones»: ninguno |
| CA-02 | 2 | Pasar a uno de sus conceptos lo pone en foco y lo visitado suma un paso | cumple | cumple | Visitado: ADMINISTRACIÓN DE MEMORIA › Memoria virtual |
| CA-02 | 3 | Volver al tema lo pone otra vez en foco, con sus vecinos | cumple | cumple | ADMINISTRACIÓN DE MEMORIA |
| CA-02 | 4 | El + de un vecino agrega sus conexiones al mapa, con nombre, y el foco no cambia | cumple | cumple | + en «Sílabo 1INF29»: de 19 a 20 puntos; Conexiones de «Sílabo 1INF29» · 7 |
| CA-03 | 1 | Prerrequisitos ordenados por distancia, sin uno de más ni de menos frente a la API | cumple | cumple | Ficha: 1:Paginación, 2:Hardware de manejo de memoria, 3:Memoria física, 4:Memoria. API: 1:Paginación, 2:Hardware de manejo de memoria, 3:Memoria física, 4:Memoria. Columnas: Justo antes, 2 pasos antes, 3 pasos antes, 4 pasos antes, Lo que quieres aprender |
| CA-03 | 2 | Por qué su prerrequisito directo va antes: la relación con su fuente | cumple | cumple | Relación seleccionada Memoria virtual necesita antes Paginación Lo dice Sílabo 1INF29 (abre el documento en una pestaña nueva) |
| CA-03 | 3 | Un concepto sin prerrequisitos: no necesita nada antes, y se muestra qué depende de él | cumple | cumple | Memoria no necesita nada antes, según los sílabos cargados: puedes empezar por aquí. Se necesita para Buferización, Caching, Memoria dinámica y Memoria física. Dependen de él: Buferización, Caching, Memoria dinámica, Memoria física |
| CA-04 | 1 | Lo que el curso pide y lo que enseña, con su nombre en la ficha | cumple | cumple | Pide: Memoria, Programación. Enseña: 63, todos con nombre en la ficha |
| CA-04 | 2 | Los cursos que conviene llevar antes, cada uno con los conceptos que lo justifican y la fuente de cada uno | cumple | cumple | Algoritmia y Estructura de Datos 1INF27 porque enseña lo que este curso pide Programación fuente · Programación 2 1INF25 porque enseña lo que este curso pide Memoria fuente · tarjeta: Relación seleccionada Algoritmia y Estructura de Datos 1INF27 enseña Programación Lo dice Sílabo 1INF27 (abre el documento en una pestañ |
| CA-05 | 1 | La cadena área › unidad › tema, y cada eslabón con su capa | cumple | cumple | Memoria virtual está en Sistemas Operativos › Gestión de Memoria › ADMINISTRACIÓN DE MEMORIA. Mapa: Concepto Memoria virtual, de un sílabo / Área Sistemas Operativos, de CS2023 / Unidad Gestión de Memoria, de CS2023 / Tema ADMINISTRACIÓN DE MEMORIA, de un sílabo |
| CA-06 | 1 | Los conceptos del tema | cumple | cumple | ADMINISTRACIÓN DE MEMORIA tiene 7 conceptos, y conviene aprenderlos en 6 pasos. |
| CA-06 | 2 | Los conceptos en pasos según sus prerrequisitos internos; ninguno antes que uno de sus prerrequisitos | cumple | cumple | Paso 1: Caching, Memoria física · Paso 2: Hardware de manejo de memoria · Paso 3: Paginación · Paso 4: Memoria virtual · Paso 5: Conjuntos de trabajo (working sets ) · Paso 6: Hiperpaginación (thrashing ) |
| CA-06 | 3 | El área, nivel por nivel, con sus cifras; si no cabe, el mapa llega hasta los temas y lo dice | cumple | cumple | Sistemas Operativos contiene 14 unidades, 6 temas y 63 conceptos. Con más de 24 conceptos, el mapa llega hasta los temas para que se pueda leer. Entra a un tema para ver sus conceptos y en qué orden aprenderlos. Las unidades sin temas están en «Conexiones», en la ficha. |
| CA-07 | 1 | El material del tema, con su tipo | cumple | cumple | Material de estudio Ver en el mapa Abrir Sílabo 1INF29 (abre el documento en una pestaña nueva) Sílabo |
| CA-07 | 2 | El PDF del sílabo abre en una pestaña nueva, y es el del curso indicado | cumple | cumple | /resources/0473349f-1344-4e98-b6a7-75c36ca223a9 → 200 application/pdf; pestaña nueva: sí |
| CA-07 | 3 | Un concepto no tiene material propio: se ofrece el de su tema | cumple | cumple | Material de estudio Ver en el mapa Un concepto no tiene material propio: los sílabos describen temas. Ver el material de su tema, «ADMINISTRACIÓN DE MEMORIA» |
| CA-07 | 4 | Un área: los sílabos que tratan sobre sus partes, cada uno con el tema por el que llega | cumple | cumple | Abrir Sílabo 1INF24, por 1 temas · Abrir Sílabo 1INF27, por 4 temas · Abrir Sílabo 1INF32, por 5 temas |
| CA-08 | 1 | Por cursos: los cursos por los que conviene pasar, por distancia, y los conceptos que se necesitan antes | cumple | cumple | Paradas: Programación 2 1INF25 · Sistemas Operativos 1INF29 (2 distancias). Abajo: Hardware de manejo de memoria, Memoria, Memoria física, Paginación |
| CA-08 | 2 | Por temas y por áreas; una parada que contiene a la meta lo dice; los conceptos no cambian | cumple | cumple | Temas: ARREGLOS Y PUNTEROS · ADMINISTRACIÓN DE MEMORIA el mismo tema. Áreas: Fundamentos de los Lenguajes de Programación · Sistemas Operativos la misma área. Conceptos en las tres: Hardware de manejo de memoria, Memoria, Memoria física, Paginación |
| CA-08 | 3 | Por qué pasar por un curso: las relaciones que lo justifican, cada una con su fuente | cumple | cumple | Programación 2 1INF25 enseña Memoria Lo dice Sílabo 1INF25 (abre el documento en una pestaña nueva) · Memoria física necesita antes Memoria Lo dice Sílabo 1INF29 (abre el documento en una pestaña nueva) · Hardware de manejo de memoria necesita antes Memoria física Lo dice Sílabo 1INF29 (abre el documento en una pestaña |
| CA-08 | 4 | Con un curso como meta: el camino, o el aviso de que sale vacío, y la remisión a «Cursos que conviene llevar antes» | cumple | cumple | Para llegar a Sistemas Operativos conviene pasar antes por 3 cursos: ahí se enseña lo que necesitas saber antes (3 conceptos). Sale de lo que necesitan antes los conceptos que el curso enseña; lo que el curso pide de entrada es otra pregunta. Ver «Cursos que conviene llevar antes» |
| CA-09 | 1 | Buscar el concepto general y abrirlo lo pone en foco | cumple | cumple | Llamadas al sistema |
| CA-09 | 2 | Sus tipos | cumple | cumple | Llamadas al sistema tiene 3 tipos. Mapa: Llamadas al sistema para manejo de archivos, Llamadas al sistema para manejo de directorios, Llamadas al sistema para manejo de procesos |
| CA-09 | 3 | Pasar a uno de sus tipos: es un tipo del concepto general | cumple | cumple | Llamadas al sistema para manejo de archivos es un tipo de Llamadas al sistema. |
| CA-09 | 4 | Un concepto sin tipos: el sistema dice que no tiene tipos registrados | cumple | cumple | Memoria virtual no es un tipo de otro concepto ni tiene tipos registrados en los sílabos cargados. |
| CA-10 | 1 | De dónde sale la relación: nombra el documento que la afirma | cumple | cumple | Relación seleccionada Memoria virtual necesita antes Paginación Lo dice Sílabo 1INF29 (abre el documento en una pestaña nueva) |
| CA-10 | 2 | Abre el PDF de ese sílabo en una pestaña nueva | cumple | cumple | /resources/0473349f-1344-4e98-b6a7-75c36ca223a9 → 200 application/pdf; pestaña nueva: sí |
| CA-10 | 3 | Un elemento de CS2023, como la unidad: nombra CS2023 y enlaza su publicación de ACM | cumple | cumple | Unidad CS2023 Gestión de Memoria Memory Management Fuente Currículo de Ciencias de la Computación 2023 (abre el documento en una pestaña nueva) Viene de CS2023, el estándar internacional del currículo de computación (ACM/IEEE). → https://dl.acm.org/doi/book/10.1145/3664191 |
| CA-10 | 4 | El interruptor «Fuentes» dibuja la línea de cada elemento a su documento | cumple | cumple | 5 líneas de fuente hacia Sílabo 1INF25, Sílabo 1INF29 |

Lo que este recorrido no comprueba: que un PDF se dibuje en la pestaña nueva (el navegador sin
interfaz no dibuja PDF; se comprueba que la pestaña se abre y que el servidor entrega un PDF en esa
dirección), la lectura con un lector de pantalla real y si una persona encuentra sola cada paso, que
es justo lo que mide la prueba de aceptación.

## 3. Lo que el grafo final cambió respecto al de desarrollo

- **Los ejemplos.** El plan se partió en casos genéricos y una hoja de datos; la hoja 1 (grafo de
  desarrollo) se retiró y la 2 es la del grafo final. En la hoja 1, «lógica» daba 7 resultados y no
  los 9 que decía el plan de entonces: la maqueta de R5 contaba los 2 documentos de procedencia.
- **El camino con un curso como meta ya no sale vacío** (CA-08, paso 4). Para un curso hay dos
  respuestas que pueden diferir: «Cursos que conviene llevar antes» parte de lo que el curso pide, y
  «Camino hasta aquí», de lo que necesitan antes los conceptos que enseña. La cabecera lo dice y
  enlaza una con la otra.
- **La cota de `/api/nodes`.** En «Lo que lo rodea», un curso muestra hasta 25 vecinos. De los 63
  conceptos que enseña «Sistemas Operativos» ahí se ven 25; los 63 están en «Cursos que conviene
  llevar antes», que es la vista que pide CA-04.

## 4. Recorrido técnico de CA-11 (panel del operador)

`web/tests/operator-walkthrough.mjs`, contra la API local, con el sílabo de 1INF33 y el servidor
local de pruebas como proveedor del modelo de lenguaje. **El recorrido no llegó a ver una ingesta
terminada**, por dos causas ajenas a la aplicación:

- En el primer intento (corrida 5) el worker murió al cargar los modelos de lectura de PDF, por falta
  de memoria en la máquina (`memory allocation of 2359296 bytes failed`). La corrida quedó «en
  curso» en el almacén operacional y el panel la siguió mostrando así: es la limitación que declara
  ADR-007, una corrida interrumpida no se recupera sola.
- En el segundo (corrida 6) el servidor local de pruebas ya no respondía, y la corrida terminó como
  fallida (`provider: Connection error.`).

| Paso | Resultado esperado | Resultado | Lo que se vio |
|---|---|---|---|
| 1 | Un token inválido se rechaza y no da acceso | cumple | «El sistema rechazó ese token. Revísalo y vuelve a intentarlo.» |
| 2 | El token del operador da acceso y muestra el estado de la compuerta de auditoría | cumple | «Compuerta de auditoría: abierta», con el último reporte, de la reaplicación, sin violaciones |
| 3 | Subir el sílabo con su tipo, código y nombre de curso registra una corrida nueva, pendiente | cumple | «Corrida 6 registrada como pendiente. Se lanzó el worker.» |
| 4 | La corrida avanza hasta un estado final, con su duración | cumple, con un estado final de fallo | Estados vistos, sin tocar nada: pendiente → en curso → fallida; duración 40 s |
| 5 | Sus descartes, o el aviso de que no hubo, y su reporte de auditoría regla por regla; el estado es el del almacén operacional | cumple en parte | Estado «fallida», igual que en el almacén; aviso de que no hubo descartes; sin reporte de cierre, porque una corrida fallida no escribe |

Lo que queda por ver en CA-11: una corrida que termine bien, con su reporte de cierre regla por regla.
Ese reporte sí se vio en el panel para las cuatro corridas terminadas que ya estaban en el almacén
(15 reglas cada una), pero no para una corrida subida en este recorrido. Hay que repetirlo con el
servidor de pruebas levantado y memoria libre.

Ninguna de las dos corridas escribió en el grafo. Después se ejecutaron `load` y `reapply`, desde el
contenedor de construcción, y el recorrido de CA-01 a CA-10 se repitió con el mismo resultado.

