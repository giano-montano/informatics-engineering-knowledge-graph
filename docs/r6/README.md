# R6 · InfoKnows: capturas y recorrido técnico

**Fecha:** 2026-11-15 · **Grafo:** desarrollo (backbone de CS2023 y los 4 sílabos de desarrollo, tras
`load` y `reapply`) · **Navegador:** Chromium 159 sin interfaz, con Playwright 1.65.1, a 1440 × 900.

La aplicación está en [`web/`](../../web/README.md). Aquí quedan las capturas de sus pantallas y el
resultado de recorrer los casos del
[plan de pruebas de aceptación](../../casos-de-prueba/plan-de-pruebas-de-aceptacion-r6.md).

> **Esto no es la prueba de aceptación.** Es un recorrido técnico previo, automático, sobre el grafo
> de desarrollo. La prueba de aceptación la hacen personas, el asesor y tres usuarios, sobre el grafo
> final, y es la única que cuenta para el indicador de R6. Este recorrido solo dice que cada paso del
> plan se puede dar y que la interfaz muestra lo que responde la API.

## 1. Capturas

Con el nombre de la captura equivalente de R5 (`docs/r5/p1-lienzo/capturas/`) donde la hay.

| Captura | Qué muestra | Caso de uso |
|---|---|---|
| [`A-inicio`](capturas/A-inicio.png) | Las 17 áreas y los 4 cursos, sin buscar; en el panel, lo mismo como lista | CU-1 |
| [`B1-busqueda-logica`](capturas/B1-busqueda-logica.png) | «lógica»: 7 resultados, con su clase y su capa en texto | CU-1 |
| [`B2-busqueda-sin-resultados`](capturas/B2-busqueda-sin-resultados.png) | «árbol»: el estado vacío, con «Ver las áreas» | CU-1 |
| [`C-foco-lo-que-lo-rodea`](capturas/C-foco-lo-que-lo-rodea.png) | «Lógica proposicional» con sus 12 vecinos en dos alas | CU-2 |
| [`C2-conexiones-traidas-con-mas`](capturas/C2-conexiones-traidas-con-mas.png) | Lo que trae el **+** de un vecino, abajo, sin cambiar el foco (sin equivalente en R5) | CU-2 |
| [`D1-que-contiene-tema`](capturas/D1-que-contiene-tema.png) | Sus 10 conceptos en 3 pasos | CU-6 |
| [`D2-que-necesitas-antes`](capturas/D2-que-necesitas-antes.png) | «Contradicción»: 4 conceptos en 2 columnas | CU-3 |
| [`D3-donde-esta-en-la-carrera`](capturas/D3-donde-esta-en-la-carrera.png) | La cadena área › unidad › tema › concepto | CU-5 |
| [`D4-camino-hasta-aqui-por-curso`](capturas/D4-camino-hasta-aqui-por-curso.png) | «Entrada y salida de datos desde archivos», por curso, con la línea de paradas | CU-8 |
| [`D5-cursos-que-conviene-llevar-antes`](capturas/D5-cursos-que-conviene-llevar-antes.png) | «Técnicas de Programación»: el curso previo, lo que pide y lo que enseña | CU-4 |
| [`D6-que-contiene-area`](capturas/D6-que-contiene-area.png) | «Redes y Comunicación» como árbol hasta los temas | CU-6 |
| [`D7-material-de-estudio`](capturas/D7-material-de-estudio.png) | Los sílabos que tratan sobre el área y por qué tema llega cada uno | CU-7 |
| [`D8-tipos`](capturas/D8-tipos.png) | «Ethernet IEEE 802.3» y sus 3 tipos | CU-9 |
| [`E-panel-del-foco`](capturas/E-panel-del-foco.png) | La ficha de «Lógica proposicional» | CU-5 a CU-7, CU-10 |
| [`E-panel-del-foco-cs2023`](capturas/E-panel-del-foco-cs2023.png) | La ficha de un elemento de CS2023, con el enlace a la publicación de ACM (sin equivalente) | CU-10 |
| [`F1-relacion-seleccionada`](capturas/F1-relacion-seleccionada.png) | «Contradicción necesita antes Tabla de verdad», con su sílabo | CU-10 |
| [`F2-por-que-de-una-parada`](capturas/F2-por-que-de-una-parada.png) | El «¿Por qué?» de una parada del camino, con sus relaciones y fuentes | CU-8, CU-10 |
| [`F3-fuentes-en-el-mapa`](capturas/F3-fuentes-en-el-mapa.png) | El interruptor «Fuentes»: cada elemento unido a su documento (sin equivalente) | CU-10 |
| [`O1-acceso-rechazado`](capturas/O1-acceso-rechazado.png) | El acceso del operador rechaza un token inválido | CU-11 |
| [`O2-panel-del-operador`](capturas/O2-panel-del-operador.png) | El panel: compuerta de auditoría, carga y corridas | CU-11 |
| [`O3-corrida-registrada`](capturas/O3-corrida-registrada.png) | Una corrida recién registrada, pendiente | CU-11 |
| [`O4-detalle-de-la-corrida`](capturas/O4-detalle-de-la-corrida.png) | El resumen de una corrida que terminó como fallida | CU-11 |
| [`O5-auditoria-de-cierre`](capturas/O5-auditoria-de-cierre.png), [`O6-descartes`](capturas/O6-descartes.png) | Sus pestañas de auditoría de cierre y de descartes, vacías | CU-11 |

## 2. Recorrido técnico de CA-01 a CA-10

`web/tests/walkthrough.mjs` da cada paso del plan dos veces: con el puntero y **solo con el teclado**
(Tab, flechas, Enter, `+`, `Ctrl K` y `Alt ←`; sin ratón). Donde el plan pide un dato, lo compara con
lo que responde la API en ese momento. Se corrió contra el servidor de desarrollo y contra el
despliegue con Docker Compose, detrás de nginx (`http://localhost:8080`), con el mismo resultado:
**66 de 66 comprobaciones cumplen**.

El paso 4 de CA-10 no está en el plan: comprueba el interruptor «Fuentes» del flujo de CU-10.

| Caso | Paso | Resultado esperado | Con puntero | Solo teclado | Lo que se vio |
|---|---|---|---|---|---|
| CA-01 | 1 | El inicio muestra las 17 áreas y los cursos con sílabo; las áreas con temas se distinguen, con sus cifras | cumple | cumple | 17 áreas, 4 cursos, 7 áreas con temas; 1 tema · 10 conceptos |
| CA-01 | 2 | Buscar «lógica» lista hasta 20 coincidencias, cada una con su clase y su origen en texto | cumple | cumple | 7 resultados: Proposición lógica (Concepto, Sílabo PUCP); Lógica proposicional (Concepto, Sílabo PUCP); Lógica proposicional (Tema, Sílabo PUCP); Proposiciones lógicas simples y compuestas (Concepto, Sílabo PUCP); Representació… |
| CA-01 | 3 | Elegir el tema «Lógica proposicional» lo pone en foco, en el mapa y en la ficha | cumple | cumple | Tema Lógica proposicional, de un sílabo. En foco |
| CA-01 | 4 | Buscar «árbol» dice que ningún sílabo cargado lo trata y ofrece ver las áreas | cumple | cumple | Ningún sílabo cargado trata «árbol»  Tampoco hay un área o una unidad de CS2023 con ese nombre. Prueba con otra palabra o recorre las áreas.  Ver las áreas lógica redes programación archivos |
| CA-02 | 1 | Vecinos directos con el nombre de cada relación, y algunos vecinos de esos vecinos, apagados; cada vecino del mapa está en «Conexiones» | cumple | cumple | Aquí ves con qué se relaciona Lógica proposicional: 12 elementos conectados directamente, agrupados por tipo de relación. Rótulos: Es parte de, Material de estudio, Contiene · 10. Apagados: 7. Fuera de «Conexiones»: ninguno |
| CA-02 | 2 | Pasar a «Contradicción» lo pone en foco y lo visitado suma un paso | cumple | cumple | Visitado: Lógica proposicional › Contradicción |
| CA-02 | 3 | Volver al tema lo pone otra vez en foco, con sus vecinos | cumple | cumple | Lógica proposicional |
| CA-02 | 4 | El + de un vecino agrega sus conexiones al mapa, con nombre, y el foco no cambia | cumple | cumple | + en «Sílabo 1INF01»: de 20 a 26 puntos; Conexiones de «Sílabo 1INF01» · 12 |
| CA-03 | 1 | Prerrequisitos ordenados por distancia, sin uno de más ni de menos frente a la API | cumple | cumple | Ficha: 1:Tabla de verdad, 2:Conjunción, 2:Disyunción, 2:Negación. API: 1:Tabla de verdad, 2:Conjunción, 2:Disyunción, 2:Negación. Columnas: Justo antes, 2 pasos antes, Lo que quieres aprender |
| CA-03 | 2 | Por qué «Tabla de verdad» va antes: la relación con su fuente | cumple | cumple | Relación seleccionada Contradicción necesita antes Tabla de verdad Lo dice Sílabo 1INF01 |
| CA-03 | 3 | «Negación» no necesita nada antes, y se muestra qué depende de él | cumple | cumple | Negación no necesita nada antes, según los sílabos cargados: puedes empezar por aquí. Se necesita para Tabla de verdad. |
| CA-04 | 1 | Lo que el curso pide y lo que enseña, con su nombre en la ficha | cumple | cumple | Pide: Algoritmia, Estructuras de control de flujo, Subprogramas. Enseña: 43, todos con nombre en la ficha |
| CA-04 | 2 | El curso que conviene llevar antes, con los conceptos que lo justifican y la fuente de cada uno | cumple | cumple | Fundamentos de Programación 1INF01 porque enseña lo que este curso pide Algoritmia fuente Estructuras de control de flujo fuente Subprogramas fuente · tarjeta: Relación seleccionada Fundamentos de Programación 1INF01 enseña Alg… |
| CA-05 | 1 | La cadena área › unidad › tema, y cada eslabón con su capa | cumple | cumple | Contradicción está en Fundamentos Matemáticos y Estadísticos › Matemática Discreta › Lógica proposicional. Mapa: Concepto Contradicción, de un sílabo / Área Fundamentos Matemáticos y Estadísticos, de CS2023 / Unidad Matemática… |
| CA-06 | 1 | Los conceptos del tema | cumple | cumple | Lógica proposicional tiene 10 conceptos, y conviene aprenderlos en 3 pasos. |
| CA-06 | 2 | Los conceptos en pasos según sus prerrequisitos internos; ninguno antes que uno de sus prerrequisitos | cumple | cumple | Paso 1: Conjunción, Disyunción, Lógica proposicional, Negación, Proposición lógica, Proposiciones lógicas simples y compuestas · Paso 2: Tabla de verdad · Paso 3: Contingencia, Contradicción, Tautología |
| CA-06 | 3 | El área, nivel por nivel, con sus cifras; si no cabe, el mapa llega hasta los temas y lo dice | cumple | cumple | Redes y Comunicación contiene 8 unidades, 14 temas y 132 conceptos. Con más de 24 conceptos, el mapa llega hasta los temas para que se pueda leer. Entra a un tema para ver sus conceptos y en qué orden aprenderlos. |
| CA-07 | 1 | El material del tema, con su tipo | cumple | cumple | Material de estudio Ver en el mapa Abrir Sílabo 1INF01 Sílabo |
| CA-07 | 2 | El PDF del sílabo abre en una pestaña nueva, y es el del curso indicado | cumple | cumple | /resources/5a791a78-36df-4f95-9eba-c2aed325c871 → 200 application/pdf; pestaña nueva: sí |
| CA-07 | 3 | Un concepto no tiene material propio: se ofrece el de su tema | cumple | cumple | Material de estudio Ver en el mapa Un concepto no tiene material propio: los sílabos describen temas. Ver el material de su tema, «Lógica proposicional» |
| CA-07 | 4 | El área: los sílabos que tratan sobre sus partes, cada uno con el tema por el que llega | cumple | cumple | Abrir Sílabo 1INF35, por 2 temas · Abrir Sílabo INF238, por 12 temas |
| CA-08 | 1 | Por cursos: los cursos por los que conviene pasar y, abajo, el concepto que se necesita antes | cumple | cumple | Paradas: Administración de Sistemas Operativos 1INF35 · Técnicas de Programación INF144 (misma distancia: sí). Abajo: Archivos |
| CA-08 | 2 | Por temas y por áreas; una parada que contiene a la meta lo dice; el concepto no cambia | cumple | cumple | Temas: Administración local · Ingreso y salida de datos el mismo tema. Áreas: Fundamentos del Desarrollo de Software la misma área · Sistemas Operativos. Concepto en las tres: Archivos / Archivos / Archivos |
| CA-08 | 3 | Por qué pasar por un curso: las relaciones que lo justifican, cada una con su fuente | cumple | cumple | Administración de Sistemas Operativos 1INF35 enseña Archivos Lo dice Sílabo 1INF35 · Entrada y salida de datos desde archivos necesita antes Archivos Lo dice Sílabo INF144 |
| CA-08 | 4 | Con un curso como meta, el camino sale vacío: se explica y se remite a «Cursos que conviene llevar antes» | cumple | cumple | Lo que Técnicas de Programación pide se aprende dentro del mismo curso, así que no hay camino previo por cursos. Ver «Cursos que conviene llevar antes» |
| CA-09 | 1 | Buscar «ethernet» y abrir «Ethernet IEEE 802.3» lo pone en foco | cumple | cumple | Ethernet IEEE 802.3 |
| CA-09 | 2 | Sus tipos | cumple | cumple | Ethernet IEEE 802.3 tiene 3 tipos. Mapa: 10GigabitEthernet, FastEthernet, Gigabit Ethernet |
| CA-09 | 3 | Pasar a «FastEthernet»: es un tipo de «Ethernet IEEE 802.3» | cumple | cumple | FastEthernet es un tipo de Ethernet IEEE 802.3. |
| CA-09 | 4 | Un concepto sin tipos: el sistema dice que no tiene tipos registrados | cumple | cumple | Contradicción no es un tipo de otro concepto ni tiene tipos registrados en los sílabos cargados. |
| CA-10 | 1 | De dónde sale la relación: nombra el documento que la afirma | cumple | cumple | Relación seleccionada Contradicción necesita antes Tabla de verdad Lo dice Sílabo 1INF01 |
| CA-10 | 2 | Abre el PDF de ese sílabo en una pestaña nueva | cumple | cumple | /resources/5a791a78-36df-4f95-9eba-c2aed325c871 → 200 application/pdf; pestaña nueva: sí |
| CA-10 | 3 | Un elemento de CS2023, como la unidad: nombra CS2023 y enlaza su publicación de ACM | cumple | cumple | Unidad CS2023 Matemática Discreta Discrete Mathematics Fuente Currículo de Ciencias de la Computación 2023 Viene de CS2023, el estándar internacional del currículo de computación (ACM/IEEE). → https://dl.acm.org/doi/book/10.114… |
| CA-10 | 4 | El interruptor «Fuentes» dibuja la línea de cada elemento a su documento | cumple | cumple | 5 líneas de fuente hacia Sílabo 1INF01 |

Lo que este recorrido no comprueba: que un PDF se dibuje en la pestaña nueva (el navegador sin
interfaz no dibuja PDF; se comprueba que la pestaña se abre y que el servidor entrega un PDF en esa
dirección), la lectura con un lector de pantalla real y si una persona encuentra sola cada paso, que
es justo lo que mide la prueba de aceptación.

## 3. Ejemplos del plan que no coinciden con el grafo

El plan marca con [SFG] los valores que se fijan con el grafo final. Contra el grafo de desarrollo,
uno no coincide:

- **CA-01, paso 2.** El plan dice que «lógica» da 9 resultados. Da **7**. La respuesta de
  `/api/search` trae 9 nodos, pero 2 son los documentos de procedencia de los resultados (el sílabo de
  1INF01 y CS2023), que no coinciden con el texto: la maqueta de R5 los contaba y la aplicación no.
  El plan no se editó.

Todos los demás valores [SFG] coinciden: 17 áreas, 4 cursos y 7 áreas con temas; 12 vecinos del tema;
los 4 prerrequisitos de «Contradicción»; los 3 conceptos que pide y los 43 que enseña «Técnicas de
Programación»; 8 unidades, 14 temas y 132 conceptos en «Redes y Comunicación»; las paradas del camino
por curso, tema y área, y los 3 tipos de «Ethernet IEEE 802.3».

Una diferencia que no es del plan: en «Lo que lo rodea», un curso muestra hasta 25 vecinos, que es
la cota de `/api/nodes`. De los 43 conceptos que enseña «Técnicas de Programación» ahí se ven 25; los
43 están en «Cursos que conviene llevar antes», que es la vista que pide CA-04.

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

