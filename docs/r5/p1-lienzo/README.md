# P1 · Constelación: el lienzo del grafo como protagonista

**Abrir:** doble clic en `index.html`. Necesita internet, porque D3 y las fuentes vienen de jsDelivr. Los datos salen de `../datos/datos.js`: respuestas reales de R4, capturadas el 2026-10-29.
**Recorrido sugerido:** en el inicio, el panel de la derecha lista los 6 pasos comunes a las tres propuestas. Al seguir uno queda una barra de un renglón sobre el mapa, con «Siguiente» y una × para salir. Cada paso se abre directo con `index.html#paso=N` (N de 1 a 6).
**Sin códigos en pantalla:** la interfaz no muestra códigos de caso de uso, pregunta de competencia ni requisito, y ya no tiene el interruptor «Ver trazabilidad». En su lugar, sobre el mapa hay siempre una frase que dice qué se está viendo y otra que dice cómo leerlo. Qué vista responde a qué caso de uso está en la sección 3; la pregunta de competencia y los requisitos de cada caso de uso, en [`../casos-de-uso.md`](../casos-de-uso.md).
**PDF de los sílabos:** los enlaces van a `http://localhost:8000/resources/<clave>` y solo abren con la API de R4 corriendo en el puerto por omisión (`uv run iekg-api`). Los de CS2023 van a la biblioteca digital de ACM.
**Maqueta sin framework:** JS sin compilación. R6 sería Svelte 5 (P1-0016). La función `api(ruta, params)` de `js/api.js` es la única puerta a los datos; en R6 se cambia su cuerpo por el `fetch` que ya está comentado ahí.
**Operador:** el enlace «Operador» de la barra superior lleva al panel común, `../panel-operador/index.html`.

---

## 1. La idea

Un mapa oscuro, tipo constelación, donde siempre hay **un elemento en foco**. El estudiante se mueve haciendo clic de punto en punto: el punto elegido pasa a ser el foco.

Sobre el mapa, una cabecera dice dónde se está: el nombre del foco, **lo que se puede preguntar sobre él** y, debajo, la respuesta en una frase y cómo leer el dibujo. Esas preguntas son las ocho **lentes** del diseño; en pantalla no llevan ese nombre y solo aparecen las que aplican al foco:
- «Lo que lo rodea»: los vecinos directos, en dos alas a los lados del foco, con el nombre de cada relación escrito sobre sus líneas;
- «Qué necesitas antes», en columnas de izquierda a derecha;
- «Camino hasta aquí», con el selector «Ver por: tema · curso · área»;
- «Cursos que conviene llevar antes»;
- «Dónde está en la carrera», como cadena del área al elemento;
- «Qué contiene», en pasos de aprendizaje (un tema) o en árbol (una unidad o un área);
- «Material de estudio» y «Tipos».

Tres reglas sostienen la legibilidad del mapa:
1. **Cada vista dibuja solo lo que responde su pregunta.** Los nodos y las relaciones que no son parte de la respuesta no se pintan, ni atenuados.
2. **Las etiquetas van en horizontal,** en una o dos líneas, y se colocan evitando encimarse.
3. **Lo que no cabe con nombre legible se resume** (un conteo, o un recuadro de puntos sin nombre) y el detalle queda a un clic: en la ficha o entrando al elemento.

A la derecha, un panel lee el foco como ficha, con las mismas secciones que la cabecera ofrece como vistas; la sección que se está viendo en el mapa queda marcada. El origen se ve por la **forma**: hexágono con contorno para CS2023, círculo relleno para lo que sale de los sílabos; una leyenda de un renglón, abajo, nombra solo las formas y los colores que hay en pantalla. Este enfoque de navegación contesta mejor «¿cómo se conecta esto con lo demás?».

## 2. Flujos

Los casos de uso son los del catálogo común, [`../casos-de-uso.md`](../casos-de-uso.md). Aquí va cómo los resuelve esta interfaz, un flujo por caso de uso. Las pantallas (A a F) se describen en la sección 3.

**Flujo CU-1 · Encontrar por dónde empezar**
1. Al entrar ve la pantalla A. La cabecera dice «Elige por dónde empezar» y explica el mapa: alrededor, las 17 áreas de CS2023; al centro, los 4 cursos con sílabo. Las 7 áreas que ya tienen temas de los sílabos brillan y dicen cuántos («Redes y Comunicación · 14 temas · 132 conceptos»); las demás se ven apagadas. El panel presenta el mapa y ofrece búsquedas de ejemplo y el recorrido sugerido.
2. O escribe en el buscador (Ctrl K): con «lógica», la lista (pantalla B) da 9 resultados, cada uno con su clase y su forma de origen.
3. Si nada coincide («árbol»), la lista lo dice («Ningún sílabo cargado trata «árbol»») y ofrece «Ver las áreas» y otras búsquedas.
4. Elige el tema «Lógica proposicional»: queda en foco en el centro del mapa (pantalla C) y el panel muestra su ficha (pantalla E).

**Flujo CU-2 · Explorar lo que rodea a un elemento**
1. Con «Lógica proposicional» en foco, la vista «Lo que lo rodea» muestra sus 12 vecinos directos en dos alas. Sobre cada grupo de líneas está escrito qué relación es: «Contiene» (sus 10 conceptos), «Es parte de» (la unidad «Matemática Discreta») y «Material de estudio» (su sílabo). Arriba, más pequeños y apagados, están algunos vecinos de esos vecinos, entre ellos el curso «Fundamentos de Programación», que enseña esos conceptos.
2. Al pasar el cursor sobre un punto ve su nombre, su clase y su origen, y se encienden sus líneas; sobre una línea, qué relación es («Contradicción necesita antes Tabla de verdad») y quién lo dice.
3. Hace clic en «Contradicción»: pasa a ser el foco y la lista «Visitado» de abajo suma un paso. Vuelve con esa lista, con «‹» o con Alt + ←.
4. Si un punto tiene **+**, lo pulsa: sus conexiones se agregan arriba o abajo, con su nombre, y el foco no cambia. «Quitar lo que trajiste con +» las retira. La lista «Conexiones» del panel da lo mismo en texto, agrupado por relación.
5. Un grupo con más de 14 elementos no cabe con nombre. Con «Técnicas de Programación» en foco, los 43 conceptos que enseña van en un recuadro de puntos rotulado «Lo que enseña · 43»: el nombre de cada uno sale al pasar el cursor y la lista completa está en «Conexiones».

**Flujo CU-3 · Saber qué conceptos necesito antes de aprender uno**
1. Con «Contradicción» en foco, elige «Qué necesitas antes» (pantalla D).
2. La cabecera responde: «Aquí ves lo que te falta saber antes de aprender Contradicción: 4 conceptos, el más lejano a 2 pasos». El mapa los ordena en columnas: «2 pasos antes» (Conjunción, Disyunción, Negación), «Justo antes» (Tabla de verdad) y, a la derecha, el foco. Las flechas van de lo que se aprende primero a lo que lo necesita.
3. En el panel, la sección «Qué necesitas antes» los lista igual, cada uno con su enlace «fuente».
4. Con un concepto que no necesita nada antes, como «Negación», la cabecera lo dice y añade «Se necesita para Tabla de verdad».

**Flujo CU-4 · Saber qué pide un curso y qué curso conviene llevar antes**
1. Con «Técnicas de Programación» en foco, elige «Cursos que conviene llevar antes».
2. El mapa se lee de izquierda a derecha: «Conviene llevar antes» (Fundamentos de Programación), «Lo que pide» (Algoritmia, Estructuras de control de flujo, Subprogramas), el curso y, en un recuadro, «Lo que enseña · 43 conceptos» como puntos sin nombre.
3. La cabecera lo resume: «Técnicas de Programación pide 3 conceptos que enseña Fundamentos de Programación: conviene llevarlo antes».
4. En el panel, «Cursos que conviene llevar antes» trae cada curso con los conceptos que lo justifican, más «Lo que pide» y «Lo que enseña»; esta última lista se abre sola en esta vista, porque es la que da nombre a los puntos del recuadro.

**Flujo CU-5 · Ubicar un concepto o tema dentro de la carrera**
1. Con «Contradicción» en foco, el panel muestra «Dónde está en la carrera» como migas: Fundamentos Matemáticos y Estadísticos › Matemática Discreta › Lógica proposicional › Contradicción.
2. La vista «Dónde está en la carrera» dibuja esa cadena de arriba abajo, con el nivel de cada eslabón escrito a la izquierda (Área, Unidad, Tema, Concepto).
3. Un clic en cualquier eslabón, en el mapa o en las migas, lo pone en foco.

**Flujo CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo**
1. Con «Lógica proposicional» en foco, elige «Qué contiene».
2. El mapa encierra sus 10 conceptos en un recuadro, en columnas: «Paso 1» (Conjunción, Disyunción, Negación y otros tres), «Paso 2» (Tabla de verdad) y «Paso 3» (Contingencia, Contradicción, Tautología). Cada paso usa lo del anterior, y las flechas dicen qué necesita qué.
3. En el panel, «Qué contiene» da las cifras y la lista «En qué orden aprenderlo».
4. Con un área, como «Redes y Comunicación», la vista es un árbol de izquierda a derecha: el área, sus 8 unidades de CS2023 y los 14 temas de los sílabos, cada tema con su número de conceptos. Las unidades que ningún sílabo trata todavía van al final, apagadas, con la nota «solo en CS2023»; si son más de 4 se resumen en una línea («+ 21 unidades de CS2023 que ningún sílabo cargado trata todavía»).
5. Los conceptos solo entran al árbol si son 24 o menos (por ejemplo, «Matemática Discreta» con sus 10). Con más, el mapa llega hasta los temas y la cabecera lo dice: para ver los conceptos de un tema y su orden, se entra al tema. El panel sigue listando el orden de los 17 conceptos que dependen entre sí en toda el área.

**Flujo CU-7 · Encontrar material de estudio sobre algo**
1. Con «Lógica proposicional» en foco, el panel muestra «Material de estudio»: «Abrir Sílabo 1INF01», de tipo sílabo.
2. La vista «Material de estudio» dibuja en columnas el elemento con sus partes, los sílabos que tratan sobre ellas y el tipo de recurso. Con «Redes y Comunicación», son los sílabos de 1INF35 e INF238, cada uno con los temas por los que llega.
3. Con un concepto en foco, el panel dice que un concepto no tiene material propio y ofrece «Ver el material de su tema».

**Flujo CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas**
1. Con «Entrada y salida de datos desde archivos» en foco, elige «Camino hasta aquí» y, en «Ver por», «curso».
2. La cabecera responde («…conviene pasar antes por 2 cursos: ahí se enseña lo que necesitas saber antes») y pone esos cursos en una línea de paradas: Administración de Sistemas Operativos y Técnicas de Programación. Las paradas a la misma distancia van juntas, sin flecha entre ellas, porque no tienen orden entre sí.
3. El mapa lo muestra en dos filas rotuladas: abajo, «Conceptos» (Archivos → la meta); arriba, «Cursos», unidos al concepto que enseñan. Lo que agrupa a la meta misma no se dibuja: no es parte del camino.
4. Con «Ver por: tema» las paradas son «Administración local» e «Ingreso y salida de datos»; con «Ver por: área», «Fundamentos del Desarrollo de Software» y «Sistemas Operativos», y el mapa baja de cada área a su unidad y su tema, en columnas. Una parada que también contiene a la meta lleva la marca «el mismo tema» (o «la misma área»), y la cabecera explica en una línea que cuenta porque lo que se necesita antes es el concepto.
5. Junto a cada parada hay un botón «¿Por qué?». Al pulsarlo, el panel muestra la tarjeta «¿Por qué pasar por…?» con cada relación que une esa parada con la meta («Administración de Sistemas Operativos enseña Archivos», «Entrada y salida de datos desde archivos necesita antes Archivos»), cada una con su fuente y «ver en el mapa»; la línea que llega a la meta queda marcada en el mapa. No depende del cursor.
6. Con un curso como meta, el camino sale vacío: la cabecera lo explica y ofrece «Cursos que conviene llevar antes».

**Flujo CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene**
1. Busca «ethernet» y abre «Ethernet IEEE 802.3».
2. La vista «Tipos» lo pone arriba y debajo sus tres tipos: FastEthernet, Gigabit Ethernet y 10GigabitEthernet. En el panel, la sección «Tipos» trae «Es un tipo de» y «Sus tipos».
3. Con un concepto sin tipos, la cabecera lo dice y sugiere probar con «ethernet».

**Flujo CU-10 · Comprobar de dónde sale un dato**
1. Con «Contradicción» en «Qué necesitas antes», pasa el cursor sobre la flecha que viene de «Tabla de verdad»: «Lo dice: Sílabo 1INF01».
2. Hace clic o toca la flecha (en pantalla táctil, el área de toque mide 24 px a cualquier zoom), o pulsa «fuente» junto a «Tabla de verdad» en el panel: la tarjeta «Relación seleccionada» (pantalla F) dice «Lo dice: Sílabo 1INF01», con el enlace que abre el PDF en una pestaña nueva.
3. Para el elemento en foco, la ficha del panel trae «Fuente» con el enlace a su sílabo. Para un elemento de CS2023, como «Matemática Discreta», enlaza la publicación de ACM.
4. El interruptor «Fuentes», abajo a la derecha, dibuja en el mapa la línea de cada elemento a su documento, en una fila aparte bajo la vista.

## 3. Cobertura

Pantallas:
- **A · Inicio:** las áreas y los cursos en el mapa, con la presentación, las búsquedas de ejemplo y el recorrido sugerido en el panel.
- **B · Resultados de búsqueda:** la lista desplegable del buscador.
- **C · Foco con lo que lo rodea:** los vecinos directos en dos alas, con el nombre de cada relación; abajo, lo visitado.
- **D · Vista activa:** el mapa dispuesto para una pregunta, con la cabecera que la responde en una frase («Ver por» y la línea de paradas en el camino).
- **E · Panel del foco:** la ficha (fuente, ubicación, contenido y orden, lo que necesitas antes, cursos, tipos, material de estudio y conexiones).
- **F · Relación seleccionada:** la tarjeta en el panel con la fuente de una línea.

| Caso de uso | Pantallas | Cómo |
|---|---|---|
| CU-1 · Encontrar por dónde empezar | A, B | Áreas y cursos sin buscar; buscador con estado vacío y «Ver las áreas» |
| CU-2 · Explorar lo que rodea a un elemento | C, E | Vista «Lo que lo rodea»: dos alas con el nombre de cada relación, clic de punto en punto, **+** para traer más, lista «Visitado»; «Conexiones» en el panel |
| CU-3 · Saber qué conceptos necesito antes de aprender uno | D, E | Vista «Qué necesitas antes» en columnas; sección del panel con «fuente» por relación |
| CU-4 · Saber qué pide un curso y qué curso conviene llevar antes | D, E | Vista «Cursos que conviene llevar antes»: el curso previo, lo que pide, el curso y el recuadro de lo que enseña |
| CU-5 · Ubicar un concepto o tema dentro de la carrera | D, E | Migas en el panel y cadena vertical en la vista «Dónde está en la carrera» |
| CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo | D, E | Vista «Qué contiene»: pasos para un tema; árbol para una unidad o un área, hasta los temas si hay más de 24 conceptos; lista «En qué orden aprenderlo» en el panel |
| CU-7 · Encontrar material de estudio sobre algo | D, E | Sección «Material de estudio» con enlace; vista en columnas; un concepto remite a su tema |
| CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas | D, E | Vista «Camino hasta aquí» con «Ver por: tema · curso · área»; línea de paradas con «¿Por qué?» por parada (relación y fuente en el panel) y marca «el mismo tema» cuando la parada contiene a la meta |
| CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene | D, E | Vista y sección «Tipos» |
| CU-10 · Comprobar de dónde sale un dato | C, D, E, F | Fuente al pasar el cursor sobre una línea o al tocarla (área de toque de 24 px), tarjeta «Relación seleccionada», «Fuente» en la ficha, «fuente» por relación, interruptor «Fuentes» |

**RF-22, en todas las pantallas:** CS2023 es un hexágono con contorno y lo de los sílabos, un círculo relleno, con su nombre escrito en el panel («CS2023», «Sílabo PUCP»), en la leyenda de un renglón que acompaña a cada vista, en la leyenda completa y en el texto accesible de cada punto. No depende del color.

## 4. Componentes de la aplicación web (esbozo de C4, nivel 3)

| Componente | Responsabilidad | Rutas que consume |
|---|---|---|
| Estado de la exploración | Foco, lente, «ver por», expansiones y rastro; los refleja en la URL (`?key=&lente=`) | — |
| Cliente de la API | Única puerta a R4: codifica las claves (IRI con `#`) y devuelve `{estado, cuerpo}` | todas las de abajo |
| Buscador | Combobox con teclado, resultados por clase y origen, estado vacío | `GET /api/search` |
| Inicio | Áreas y cursos sin buscar | `GET /api/overview` (**nueva**) |
| Lienzo del grafo (D3) | Dibuja, del subgrafo acumulado, lo que responde la lente activa: forma por origen, una disposición por lente, etiquetas colocadas sin encimarse, zoom y **+** | `GET /api/nodes` (al pulsar +) |
| Cabecera de contexto (selector de lentes) | Nombra el foco, ofrece las lentes que aplican a su clase, pide el subgrafo de la elegida y la responde en una frase, con cómo leer el dibujo | `/api/concepts/prerequisites`, `/api/courses/prerequisites`, `/api/elements/location` (dos lentes), `/api/elements/resources`, `/api/learning-path`, `/api/concepts/specializations` |
| Panel del foco | Ficha: fuente, ubicación, contenido y orden, lo que necesitas antes, cursos, tipos, material de estudio y conexiones; relación seleccionada | `/api/nodes` y las mismas seis; enlaces a `/resources/{key}` |
| Línea de paradas | Resume el camino en una línea, dentro de la cabecera, con «¿Por qué?» por parada | (respuesta de la lente) |
| Rastro, leyenda y recorrido | Historial de focos, leyenda de un renglón con lo que hay en pantalla, leyenda completa de formas, colores y líneas, y los 6 pasos comunes | — |
| Panel del operador | Común a las tres propuestas (`../panel-operador/`); aquí solo se enlaza | `/api/runs`, `/api/runs/{id}`, `/api/runs/{id}/discards`, `/api/audit-reports/latest` |

```likec4
// Borrador: se agregaría a docs/architecture/model.c4 y views.c4. Sin validar.
model {
  extend kms.web {
    exploracion = component 'Estado de la exploración' {
      technology 'Svelte 5 (runes)'
      summary 'Foco, lente, «ver por», expansiones y rastro; los refleja en la URL.'
    }
    cliente = component 'Cliente de la API' {
      technology 'fetch'
      summary 'Única puerta a R4: codifica las claves y devuelve el subgrafo {nodes, edges}.'
    }
    buscador = component 'Buscador' {
      summary 'Punto de entrada por nombre, con teclado.'
    }
    portada = component 'Portada' {
      summary 'Inicio: las 17 áreas y los cursos, sin buscar.'
    }
    lienzo = component 'Lienzo del grafo' {
      technology 'D3 7.9.0 (d3-force, d3-hierarchy, d3-zoom), SVG'
      summary 'Dibuja lo que responde la lente activa, con forma por origen y una disposición por lente.'
    }
    lentes = component 'Cabecera de contexto' {
      summary 'Ofrece las lentes que aplican al foco, pide el subgrafo de la elegida y la responde en una frase.'
    }
    panelFoco = component 'Panel del foco' {
      summary 'Ficha del foco: fuente, ubicación, contenido y orden, prerrequisitos, material y conexiones.'
    }
    franja = component 'Línea de paradas' {
      summary 'Resume el camino hasta la meta en una línea, con el porqué de cada parada.'
    }
    panelOperador = component 'Panel del operador' {
      summary 'Común a las propuestas: token tecleado, carga de documentos, corridas, descartes y reporte.'
    }
  }

  kms.web.buscador -> kms.web.exploracion 'Fija el foco'
  kms.web.portada -> kms.web.exploracion 'Fija el foco'
  kms.web.lienzo -> kms.web.exploracion 'Cambia el foco o agrega conexiones'
  kms.web.lentes -> kms.web.exploracion 'Cambia la lente y el «ver por»'
  kms.web.exploracion -> kms.web.lienzo 'Subgrafo y disposición'
  kms.web.exploracion -> kms.web.panelFoco 'Foco en curso'
  kms.web.exploracion -> kms.web.franja 'Respuesta de la lente'
  kms.web.exploracion -> kms.web.cliente 'Pide subgrafos'
  kms.web.buscador -> kms.web.cliente 'Busca por nombre'
  kms.web.panelFoco -> kms.web.cliente 'Pide fuente, ubicación, prerrequisitos y material'

  kms.web.cliente -> kms.api.navRoutes 'Búsqueda, detalle, siete patrones y portada' {
    technology 'HTTP/JSON'
  }
  kms.web.panelFoco -> kms.api.navRoutes 'Abre el documento del sílabo' {
    technology 'HTTP (PDF)'
  }
  kms.web.panelOperador -> kms.api.opsRoutes 'Alta de corrida, estado, descartes y reporte' {
    technology 'HTTP/JSON, Bearer'
  }
}

views {
  view webComponentes of kms.web {
    title 'Aplicación web: componentes (P1)'
    include *
  }
}
```

## 5. Rutas

**Las que usa, sin cambios:** `GET /api/search`, `GET /api/nodes`, las seis rutas de patrón (`/api/concepts/prerequisites`, `/api/courses/prerequisites`, `/api/elements/location`, `/api/elements/resources`, `/api/learning-path?grain=`, `/api/concepts/specializations`) y `GET /resources/{key}`. `/api/elements/location` sirve a dos lentes: «Dónde está en la carrera» lee la cadena hacia arriba y «Qué contiene», la composición hacia abajo. El panel del foco hace hasta cinco llamadas en paralelo, todas a rutas existentes.

**«En qué orden aprenderlo»** no pide ruta nueva. Los pasos salen de ordenar los conceptos que trae `/api/elements/location` según las aristas `HAS_PREREQUISITE` de la misma respuesta (paso 1 = no necesita nada de dentro). Es una disposición de lo que llegó: no deriva aristas ni nodos.

**Nueva necesaria: `GET /api/overview`** (portada). En la maqueta se simula con `IEKG_SIMULADO`, marcado «simulado» en pantalla.

```json
{
  "areas":   [{"key": "…#KA-NC", "name_es": "Redes y Comunicación", "name_en": "Networking and Communication",
               "units": 8, "topics": 14, "concepts": 132}],
  "courses": [{"key": "c5405343-…", "name_es": "Redes de Computadoras", "code": "INF238"}]
}
```

Los conteos son de la composición bajo cada área (solo nodos que existen, sin derivar aristas). La alternativa es devolverla como `{nodes, edges}` sin aristas, con los conteos como campos del nodo, para no salirse de la forma única (§1 del diseño de rutas); se decide al agregarla a R4.

**Simulado solo en la maqueta, no es ruta nueva:** la búsqueda de un texto que no se capturó se filtra en el cliente sobre los nombres reales y se marca «simulada». En R6 la resuelve `/api/search`.

## 6. Riesgos

- **Escala.** Es el riesgo principal, y con los 13 sílabos finales crece. La maqueta lo trata con una regla: lo que no cabe con nombre legible se resume y el detalle queda a un clic. Hoy aplica en tres sitios: «Qué contiene» de un área llega hasta los temas cuando hay más de 24 conceptos (Redes y Comunicación: 8 unidades y 14 temas en pantalla, no los 158 nodos de la respuesta); un grupo de más de 14 vecinos va como recuadro de puntos («Lo que enseña · 43»); y las unidades de CS2023 sin temas se resumen en una línea cuando son más de 4. Los umbrales (24, 14 y 4) salen de probar con los 4 sílabos: hay que revisarlos con los 13. Lo que queda sin resolver: un área con decenas de temas alarga el árbol y obliga a alejar el zoom, y dos vistas no tienen todavía regla de resumen, «Qué necesitas antes» y «Camino hasta aquí», porque las rutas de hoy no pasan de 2 pasos de profundidad.
- **Legibilidad.** Las etiquetas van en horizontal, en dos líneas de unos 21 caracteres, con un halo oscuro para leerse sobre las líneas, y se colocan evitando encimarse; lo que excede se corta con puntos suspensivos y se lee entero al pasar el cursor o en la ficha. El texto del panel cumple contraste AA o más sobre el fondo. En una pantalla de 1366 × 768 las vistas más altas se encuadran alrededor del 75 % y sus etiquetas quedan cerca de 9 px: se leen, pero es el límite. Los nombres repetidos (un tema y un concepto llamados «Lógica proposicional») se distinguen por el color y en el panel, no por el nombre.
- **Orientación.** Un mapa que cambia de disposición con cada pregunta puede desorientar. Por eso la cabecera nombra siempre el foco y la vista, responde en una frase y dice cómo leer el dibujo; el foco se marca con un halo; y la lista «Visitado» y el botón «Inicio» devuelven a terreno conocido. A cambio, al cambiar de vista los puntos que no responden la pregunta nueva desaparecen en lugar de quedarse atenuados.
- **Accesibilidad.** Cada punto es un botón con texto accesible (clase, nombre y origen), se recorre con Tab, Enter lo pone en foco y + trae más conexiones. El panel replica todo vecino y toda relación como lista con botones, que es la alternativa en texto; los puntos sin nombre de un recuadro dependen de esa lista. Se respeta `prefers-reduced-motion`. Falta un recorrido con un lector de pantalla real.
- **Datos pobres.** `description` casi no existe, así que la ficha no depende de ella. Solo hay 6 relaciones de tipo: la vista «Tipos» lo dice cuando no hay.

## 7. Costo documental si se elige

- **Fase 1 de R5 (tesis):** el catálogo común de casos de uso (`../casos-de-uso.md`), los 10 flujos de la sección 2 y las capturas de la maqueta como wireframes. Todavía no hay carpeta `capturas/`: se hacen al cerrar la propuesta.
- **Fase 2 de R5:** el bloque `likec4` de §4 pasa a `docs/architecture/model.c4` (componentes de `kms.web`) y a una vista de nivel 3 en `views.c4`, que se valida con `npm run arch:validate`.
- **ADR:** los 4 de `adr/` pasan a `docs/decisiones/` como 0015 a 0018: `P1-0015-enfoque-de-navegacion-lienzo.md`, `P1-0016-framework-svelte.md`, `P1-0017-visualizacion-d3-svg.md` y `P1-0018-capas-y-procedencia-en-el-lienzo.md`. Cada uno suma su fila en la Tabla 20 de la tesis (la línea «Fila para la Tabla 20» ya está escrita).
- **R4:** una ruta nueva, `GET /api/overview`, con su prueba y su línea en `docs/diseño-de-las-rutas-de-navegación.md` §5. El resto usa rutas existentes.
