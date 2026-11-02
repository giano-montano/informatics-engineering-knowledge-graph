# P1 · Constelación: el lienzo del grafo como protagonista

**Abrir:** doble clic en `index.html`. Necesita internet, porque D3 y las fuentes vienen de jsDelivr. Los datos salen de `../datos/datos.js`: respuestas reales de R4, capturadas el 2026-10-29.
**Recorrido sugerido:** la tarjeta de abajo a la izquierda tiene los 6 pasos comunes a las tres propuestas; se cierra con × y se reabre con su botón. Cada paso se abre directo con `index.html#paso=N` (N de 1 a 6).
**Ver trazabilidad:** el interruptor de la barra superior está apagado por omisión. Encendido, cada lente, sección del panel y paso del recorrido muestra su caso de uso y sus códigos (p. ej. `CU-3 · PC1 · RF-11 · RF-20`); apagado, la interfaz no muestra ningún código. `index.html#traza` lo abre encendido.
**PDF de los sílabos:** los enlaces van a `http://localhost:8000/resources/<clave>` y solo abren con la API de R4 corriendo en el puerto por omisión (`uv run iekg-api`). Los de CS2023 van a la biblioteca digital de ACM.
**Maqueta sin framework:** JS sin compilación. R6 sería Svelte 5 (P1-0016). La función `api(ruta, params)` de `js/api.js` es la única puerta a los datos; en R6 se cambia su cuerpo por el `fetch` que ya está comentado ahí.
**Operador:** el enlace «Operador» del riel lleva al panel común, `../panel-operador/index.html`.

---

## 1. La idea

Un mapa oscuro, tipo constelación, donde siempre hay **un elemento en foco** con su vecindario alrededor, en anillos. El estudiante se mueve haciendo clic de punto en punto: el vecino elegido pasa a ser el foco, y lo que sigue en pantalla conserva su lugar. Con **+** agrega las conexiones de un vecino sin perder lo anterior. A la izquierda, ocho **lentes** reordenan el mismo mapa desde una pregunta y atenúan el resto:
- «Qué necesitas antes», en columnas de izquierda a derecha;
- «Camino hasta aquí», con el selector «Ver por: tema · curso · área»;
- «Cursos que conviene llevar antes»;
- «Dónde está en la carrera», como cadena hacia el área;
- «Qué contiene», en pasos de aprendizaje o en anillos;
- «Material de estudio» y «Tipos».

A la derecha, un panel lee el foco como ficha. El origen se ve por la **forma**: hexágono con contorno para CS2023, círculo relleno para lo que sale de los sílabos. Este enfoque de navegación contesta mejor «¿cómo se conecta esto con lo demás?».

## 2. Flujos

Los casos de uso son los del catálogo común, [`../casos-de-uso.md`](../casos-de-uso.md). Aquí va cómo los resuelve esta interfaz, un flujo por caso de uso. Las pantallas (A a F) se describen en la sección 3.

**Flujo CU-1 · Encontrar por dónde empezar**
1. Al entrar ve la pantalla A: la frase de bienvenida en el panel y, en el mapa, las 17 áreas de CS2023 en anillo y los 4 cursos al centro. Las áreas que ya tienen temas de los sílabos brillan y dicen cuántos («Redes y Comunicación · 14 temas · 132 conceptos»); las demás dicen «solo en CS2023».
2. O escribe en el buscador (Ctrl K): con «lógica», la lista (pantalla B) da 9 resultados, cada uno con su clase y su forma de origen.
3. Si nada coincide («árbol»), la lista lo dice («Ningún sílabo cargado trata «árbol»») y ofrece «Ver las áreas» y otras búsquedas.
4. Elige el tema «Lógica proposicional»: queda en foco en el centro del mapa (pantalla C) y el panel muestra su ficha (pantalla E).

**Flujo CU-2 · Explorar lo que rodea a un elemento**
1. Con «Lógica proposicional» en foco, la lente «Vecindario» muestra en el primer anillo sus 10 conceptos, su unidad «Matemática Discreta» y su sílabo. En el segundo anillo están algunos vecinos de esos vecinos, entre ellos el curso «Fundamentos de Programación», que enseña esos conceptos.
2. Al pasar el cursor sobre un punto ve su nombre, su clase y su origen; sobre una línea, qué relación es («Contradicción necesita antes Tabla de verdad»).
3. Hace clic en «Contradicción»: pasa a ser el foco y el rastro de abajo suma un paso. Vuelve con el rastro, con «‹» o con Alt + ←.
4. Si un punto tiene **+**, lo pulsa: sus conexiones se agregan al mapa y el foco no cambia. La lista «Conexiones» del panel da lo mismo en texto, agrupado por relación.

**Flujo CU-3 · Saber qué conceptos necesito antes de aprender uno**
1. Con «Contradicción» en foco, elige la lente «Qué necesitas antes» (pantalla D).
2. El mapa ordena los conceptos en columnas: «A 2 pasos» (Conjunción, Disyunción, Negación), «Directo» (Tabla de verdad) y «En foco». Las líneas fluyen hacia lo que los necesita.
3. En el panel, la sección «Qué necesitas antes» los lista igual, cada uno con su botón «Ver fuente».
4. Con un concepto que no necesita nada antes, como «Negación», la barra de la lente lo dice y añade «Se necesita para: Tabla de verdad».

**Flujo CU-4 · Saber qué pide un curso y qué curso conviene llevar antes**
1. Con «Técnicas de Programación» en foco, elige la lente «Cursos que conviene llevar antes».
2. A la izquierda del mapa aparecen «Lo que pide» (Algoritmia, Estructuras de control de flujo, Subprogramas) y, más a la izquierda, «Fundamentos de Programación», el curso que lo enseña. Alrededor, en arco, están los 43 conceptos que enseña el curso.
3. La franja superior lo resume: «Fundamentos de Programación 1INF01 → Técnicas de Programación INF144».
4. En el panel, «Cursos que conviene llevar antes» trae cada curso con los conceptos que lo justifican, más «Lo que pide» y «Lo que enseña» (esta última, desplegable).

**Flujo CU-5 · Ubicar un concepto o tema dentro de la carrera**
1. Con «Contradicción» en foco, el panel muestra «Dónde está en la carrera» como migas: Fundamentos Matemáticos y Estadísticos › Matemática Discreta › Lógica proposicional › Contradicción.
2. La lente «Dónde está en la carrera» dibuja esa cadena en vertical en el mapa, con el área arriba.
3. Un clic en cualquier eslabón, en el mapa o en las migas, lo pone en foco.

**Flujo CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo**
1. Con «Lógica proposicional» en foco, elige la lente «Qué contiene».
2. El mapa pone sus 10 conceptos en columnas: «Paso 1» (Conjunción, Disyunción, Negación y otros tres), «Paso 2» (Tabla de verdad) y «Paso 3» (Contingencia, Contradicción, Tautología). Cada paso usa lo del anterior.
3. En el panel, «Qué contiene» da las cifras y la lista «En qué orden aprenderlo».
4. Con un área, como «Redes y Comunicación», la lente dibuja unidades, temas y conceptos en anillos (8, 14 y 132). Para leer el anillo exterior se acerca el zoom. El panel lista el orden solo de los 17 conceptos que dependen entre sí.

**Flujo CU-7 · Encontrar material de estudio sobre algo**
1. Con «Lógica proposicional» en foco, el panel muestra «Material de estudio»: «Abrir Sílabo 1INF01», de tipo sílabo.
2. La lente «Material de estudio» dibuja en columnas el elemento, sus partes y los sílabos que tratan sobre ellas. Con «Redes y Comunicación», son los sílabos de 1INF35 e INF238, cada uno con los temas por los que llega.
3. Con un concepto en foco, el panel dice que un concepto no tiene material propio y ofrece «Ver el material de su tema».

**Flujo CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas**
1. Con «Entrada y salida de datos desde archivos» en foco, elige la lente «Camino hasta aquí» y, en «Ver por:», «curso».
2. El mapa pone arriba los cursos por los que conviene pasar antes (Administración de Sistemas Operativos, Técnicas de Programación) y abajo el concepto que lo justifica (Archivos). La franja superior los muestra como estaciones hacia la meta.
3. Con «Ver por: tema» las estaciones son «Administración local» e «Ingreso y salida de datos»; con «Ver por: área», «Fundamentos del Desarrollo de Software» y «Sistemas Operativos».
4. Al pasar el cursor o hacer clic en una línea del camino, ve qué relación la justifica y su fuente.
5. Con un curso como meta, el camino sale vacío: la barra lo explica y ofrece «Cursos que conviene llevar antes».

**Flujo CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene**
1. Busca «ethernet» y abre «Ethernet IEEE 802.3».
2. La lente «Tipos» lo pone arriba y debajo sus tres tipos: FastEthernet, Gigabit Ethernet y 10GigabitEthernet. En el panel, la sección «Tipos» trae «Es un tipo de» y «Tipos».
3. Con un concepto sin tipos, la barra lo dice y sugiere probar con «ethernet».

**Flujo CU-10 · Comprobar de dónde sale un dato**
1. Con «Contradicción» en «Qué necesitas antes», pasa el cursor sobre la línea hacia «Tabla de verdad»: «Fuente: Sílabo 1INF01».
2. Hace clic en la línea, o en «Ver fuente» junto a «Tabla de verdad» en el panel: la tarjeta «Relación seleccionada» (pantalla F) dice «Lo dice: Ver fuente · Sílabo 1INF01». El botón abre el PDF en una pestaña nueva.
3. Para el elemento en foco, la sección «Fuente» del panel enlaza su sílabo. Para un elemento de CS2023, como «Matemática Discreta», enlaza la publicación de ACM.
4. El interruptor «Mostrar fuentes» dibuja en el mapa la línea de cada elemento a su fuente.

## 3. Cobertura

Pantallas:
- **A · Entrada:** las áreas y los cursos en el mapa, con la bienvenida en el panel.
- **B · Resultados de búsqueda:** la lista desplegable del buscador.
- **C · Foco con vecindario:** el mapa en anillos alrededor del elemento en foco, con el rastro abajo.
- **D · Lente activa:** el mapa reordenado por una lente, con su barra («Ver por» en el camino) y, si aplica, la franja de estaciones.
- **E · Panel del foco:** la ficha (fuente, ubicación, contenido y orden, lo que necesitas antes, cursos, tipos, material de estudio y conexiones).
- **F · Relación seleccionada:** la tarjeta en el panel con la fuente de una línea.

| Caso de uso | Pantallas | Cómo |
|---|---|---|
| CU-1 · Encontrar por dónde empezar | A, B | Áreas y cursos sin buscar; buscador con estado vacío y «Ver las áreas» |
| CU-2 · Explorar lo que rodea a un elemento | C, E | Anillos alrededor del foco, clic de punto en punto, **+** para ver más, rastro; «Conexiones» en el panel |
| CU-3 · Saber qué conceptos necesito antes de aprender uno | D, E | Lente «Qué necesitas antes» en columnas; sección del panel con «Ver fuente» por relación |
| CU-4 · Saber qué pide un curso y qué curso conviene llevar antes | D, E | Lente «Cursos que conviene llevar antes»: lo que pide, el curso que lo enseña y lo que enseña; franja de estaciones |
| CU-5 · Ubicar un concepto o tema dentro de la carrera | D, E | Migas en el panel y cadena vertical en la lente «Dónde está en la carrera» |
| CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo | D, E | Lente «Qué contiene»: pasos para un tema, anillos para una unidad o un área; lista «En qué orden aprenderlo» |
| CU-7 · Encontrar material de estudio sobre algo | D, E | Sección «Material de estudio» con enlace; lente en columnas; un concepto remite a su tema |
| CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas | D | Lente «Camino hasta aquí» con «Ver por: tema · curso · área» y franja de estaciones |
| CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene | D, E | Lente y sección «Tipos» |
| CU-10 · Comprobar de dónde sale un dato | C, D, E, F | Fuente al pasar el cursor sobre una línea, tarjeta «Relación seleccionada», sección «Fuente», «Ver fuente» por relación, interruptor «Mostrar fuentes» |

**RF-22, en todas las pantallas:** CS2023 es un hexágono con contorno y lo de los sílabos, un círculo relleno, con su nombre escrito en el panel («CS2023», «Sílabo PUCP»), en la leyenda y en el texto accesible de cada punto. No depende del color.

## 4. Componentes de la aplicación web (esbozo de C4, nivel 3)

| Componente | Responsabilidad | Rutas que consume |
|---|---|---|
| Estado de la exploración | Foco, lente, «ver por», expansiones, rastro y trazabilidad; los refleja en la URL (`?key=&lente=`) | — |
| Cliente de la API | Única puerta a R4: codifica las claves (IRI con `#`) y devuelve `{estado, cuerpo}` | todas las de abajo |
| Buscador | Combobox con teclado, resultados por clase y origen, estado vacío | `GET /api/search` |
| Portada | Áreas y cursos sin buscar | `GET /api/overview` (**nueva**) |
| Lienzo del grafo (D3) | Dibuja el subgrafo acumulado con forma por origen, zoom, **+** y una disposición por lente | `GET /api/nodes` (al pulsar +) |
| Selector de lentes | Habilita la lente según la clase del foco y pide su subgrafo | `/api/concepts/prerequisites`, `/api/courses/prerequisites`, `/api/elements/location` (dos lentes), `/api/elements/resources`, `/api/learning-path`, `/api/concepts/specializations` |
| Panel del foco | Ficha: fuente, ubicación, contenido y orden, lo que necesitas antes, cursos, tipos, material de estudio y conexiones; relación seleccionada | `/api/nodes` y las mismas seis; enlaces a `/resources/{key}` |
| Franja de estaciones | Resume el camino o los cursos que conviene llevar antes | (respuesta de la lente) |
| Rastro, leyenda, recorrido y trazabilidad | Historial de focos, leyenda de orígenes, clases y líneas, los 6 pasos comunes y las insignias de casos de uso | — |
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
      summary 'Las 17 áreas y los cursos, sin buscar.'
    }
    lienzo = component 'Lienzo del grafo' {
      technology 'D3 7.9.0 (d3-force, d3-hierarchy, d3-zoom), SVG'
      summary 'Dibuja el subgrafo acumulado con forma por origen y una disposición por lente.'
    }
    lentes = component 'Selector de lentes' {
      summary 'Habilita la lente según la clase del foco y pide el subgrafo de su ruta.'
    }
    panelFoco = component 'Panel del foco' {
      summary 'Ficha del foco: fuente, ubicación, contenido y orden, prerrequisitos, material y conexiones.'
    }
    franja = component 'Franja de estaciones' {
      summary 'Resume el camino o los cursos que conviene llevar antes.'
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

- **Escala.** «Qué contiene» sobre un área grande (Redes y Comunicación: 158 nodos) y «Cursos que conviene llevar antes» sobre INF238 (142) cargan el lienzo. Mitigación: los conceptos se dibujan pequeños, en el anillo exterior o en arco, con etiquetas radiales. Con poco zoom se ocultan las secundarias, y al pasar el cursor se ven. Si un sílabo futuro triplica eso, el SVG llega a su límite (ver P1-0017).
- **Legibilidad.** Las etiquetas se cortan a unos 32 caracteres y llevan un halo oscuro para leerse sobre las líneas. El texto del panel cumple contraste AA o más sobre el fondo. Los nombres repetidos (un tema y un concepto llamados «Lógica proposicional») se distinguen por la forma y en el panel, no siempre en el lienzo.
- **Orientación.** Un lienzo que se reordena por lente puede desorientar. Por eso el foco siempre se marca con un halo, los puntos que siguen en pantalla conservan su lugar, y el rastro y «Limpiar el mapa» devuelven a terreno conocido.
- **Accesibilidad.** Cada punto es un botón con texto accesible (clase, nombre y origen), se recorre con Tab, Enter lo pone en foco y + muestra más conexiones. El panel replica todo vecino y toda relación como lista con botones, que es la alternativa en texto. Se respeta `prefers-reduced-motion`. Falta un recorrido con un lector de pantalla real.
- **Datos pobres.** `description` casi no existe, así que la ficha no depende de ella. Solo hay 6 relaciones de tipo: la lente «Tipos» lo dice cuando no hay.

## 7. Costo documental si se elige

- **Fase 1 de R5 (tesis):** el catálogo común de casos de uso (`../casos-de-uso.md`), los 10 flujos de la sección 2 y las capturas de la maqueta como wireframes. Están en `capturas/` y se rehacen al cerrar la propuesta.
- **Fase 2 de R5:** el bloque `likec4` de §4 pasa a `docs/architecture/model.c4` (componentes de `kms.web`) y a una vista de nivel 3 en `views.c4`, que se valida con `npm run arch:validate`.
- **ADR:** los 4 de `adr/` pasan a `docs/decisiones/` como 0015 a 0018: `P1-0015-enfoque-de-navegacion-lienzo.md`, `P1-0016-framework-svelte.md`, `P1-0017-visualizacion-d3-svg.md` y `P1-0018-capas-y-procedencia-en-el-lienzo.md`. Cada uno suma su fila en la Tabla 20 de la tesis (la línea «Fila para la Tabla 20» ya está escrita).
- **R4:** una ruta nueva, `GET /api/overview`, con su prueba y su línea en `docs/diseño-de-las-rutas-de-navegación.md` §5. El resto usa rutas existentes.
