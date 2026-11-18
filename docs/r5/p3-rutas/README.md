# P3 · Itinerario: navegación centrada en rutas

Maqueta: `index.html`, se abre con doble clic. Usa los datos reales de `../datos/datos.js` y, desde CDN, Vue 3.5.44 (la variante sin compilación) y D3 7.9.0. En R6 el mismo código pasa a componentes de Vue compilados con Vite (P3-0016). Los PDF de los sílabos abren solo con la API corriendo en `localhost:8000` (`uv run iekg-api`); el enlace a CS2023 abre en ACM.

- **Recorrido sugerido:** seis pasos comunes a las tres propuestas, en una tarjeta que se cierra con × y se reabre desde la barra. «Siguiente» deja la pantalla en el estado de cada paso, y `index.html#paso=N` abre el paso N directamente.
- **Ver trazabilidad:** un interruptor de la barra, apagado por omisión. Encendido, cada pestaña, sección, diálogo y paso del recorrido muestra su caso de uso y sus códigos (`CU-3 · PC1 · RF-11`), según `../casos-de-uso.md`. Apagado, la interfaz no muestra ningún código.
- **Otros enlaces directos:**
  - `#destino=<clave>&grano=course&pestana=pc4` abre una meta (los identificadores de la URL son internos).
  - `#traza=si` enciende la trazabilidad.
  - `#buscar=lógica` deja hecha una búsqueda.
- **Capturas:** las de `capturas/` sirven de wireframes y se rehacen al cerrar la propuesta.

## 1. La idea

El estudiante elige una meta («¿Qué quieres aprender?») y ve qué conviene saber antes, dibujado como un **mapa de metro**.

- **Estaciones:** son los conceptos, en columnas según su distancia a la meta: «a 2 pasos», «directo», «meta».
- **Líneas:** son los temas, cursos o áreas a los que pertenecen esos conceptos. El control **«Ver por: tema · curso · área»** cambia qué representan.
- **Transbordo:** un concepto que está en dos líneas. Por ejemplo, *Archivos* se enseña en INF144 y en 1INF35.
- **«?» de cada tramo:** muestra las relaciones que lo justifican, con su fuente («Ver fuente» abre el sílabo).
- **«Indicaciones»:** el mismo camino como lista ordenada, en el panel lateral, sin progreso ni marcas.

Contesta lo más valorado en E16: «¿qué necesito antes?» (83,1 %).

## 2. Flujos

Los casos de uso son comunes a las tres propuestas y están en [`../casos-de-uso.md`](../casos-de-uso.md). Aquí va un flujo por caso de uso: los pasos con que esta interfaz lo resuelve. Las pantallas se nombran con letra (ver §3).

**Flujo CU-1 · Encontrar por dónde empezar**
1. En la entrada (A), el estudiante escribe «lógica» en «¿Qué quieres aprender?».
2. La lista muestra 9 resultados. Cada uno lleva su clase (Concepto, Tema, Unidad), su origen («Sílabo PUCP» con un círculo, «CS2023» con un cuadrado) y, si tiene camino, la marca «con camino».
3. Elige el tema «Lógica proposicional»: se abre como meta en la pantalla B.
4. Si no escribe nada, recorre la entrada: «Metas con camino» (35), «Caminos que cruzan cursos o áreas», «Cursos» (4) y «Áreas de la carrera» (17; las 7 con temas de los sílabos van resaltadas y primero).
5. Si nada coincide, por ejemplo con «árbol», la lista lo dice y ofrece «Recorrer las áreas de la carrera».

**Flujo CU-2 · Explorar lo que rodea a un elemento**
1. En el camino (B), toca una estación, por ejemplo «Tabla de verdad»: se abre su ficha (C).
2. La sección «Alrededor» agrupa sus vecinos directos por relación: «Requiere» (Negación, Conjunción, Disyunción), «Lo necesitan antes» (Tautología, Contradicción, Contingencia), «Es parte de» y «Lo enseña». Cada vecino lleva la fuente de su relación y el número de relaciones que tiene más allá.
3. El «▸» de un vecino despliega, dentro de la misma ficha, su segundo nivel: «Alrededor de «Negación»: Es parte de Lógica proposicional · Lo enseña Fundamentos de Programación», cada relación con su fuente. «Desplegar todo» abre el segundo nivel de un grupo entero.
4. Si un vecino tiene más relaciones de las que trajo la ficha (un «+» tras su número), «Ver más relaciones de «Fundamentos de Programación»» las agrega en el mismo despliegue (16 más), sin cambiar de ficha.
5. Tocar un nombre, de primer o de segundo nivel, abre su ficha; «← Atrás» vuelve.

**Flujo CU-3 · Saber qué conceptos necesito antes de aprender uno**
1. Abre la meta «Contradicción» (desde la entrada o con «Ver el camino hasta aquí» en una ficha).
2. El mapa (B) muestra tres columnas. «A 2 pasos» tiene Negación, Conjunción y Disyunción. «Directo» tiene Tabla de verdad. «Meta» tiene Contradicción.
3. «Indicaciones», a la derecha, repite el camino como lista.
4. La ficha de cualquier concepto (C) tiene la sección «Qué necesitas antes», con «directo» o «a 2 pasos» en cada uno.
5. Si un concepto no necesita nada antes, por ejemplo «Negación», la pantalla G lo dice. Debajo lista los «Conceptos que lo necesitan antes» (Tabla de verdad).

**Flujo CU-4 · Saber qué pide un curso y qué curso conviene llevar antes**
1. Abre el curso «Técnicas de Programación» (INF144), desde «Cursos» en la entrada o con el buscador.
2. Se abre la pantalla F, pestaña «Cursos que conviene llevar antes». La columna «Lo que pide» muestra Algoritmia, Estructuras de control de flujo y Subprogramas, sobre la línea roja 1INF01, con transbordo a la meta INF144.
3. Toca un «?»: la evidencia dice «Técnicas de Programación pide Algoritmia» y «Fundamentos de Programación enseña Algoritmia», cada afirmación con su sílabo.
4. La ficha del curso tiene la sección «Lo que pide y lo que enseña» (43 conceptos).
5. Con 1INF01, que no pide nada de otros cursos, la pantalla G lo dice.

**Flujo CU-5 · Ubicar un concepto o tema dentro de la carrera**
1. En la ficha (C) de «Archivos», abre la sección «Dónde está en la carrera».
2. Muestra dos cadenas, porque *Archivos* pertenece a dos temas:
   - Fundamentos del Desarrollo de Software › Conceptos y Prácticas Fundamentales de Programación › Ingreso y salida de datos › Archivos.
   - Sistemas Operativos › Principios de los Sistemas Operativos › Administración local › Archivos.
3. Cada eslabón lleva su clase y su origen. Al tocar uno, se abre su ficha.

**Flujo CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo**
1. Con la meta «Lógica proposicional», toca la pestaña «Qué contiene y en qué orden» (pantalla E).
2. El mapa agrupa en pasos los 7 conceptos que tienen un orden. «Primero»: Negación, Conjunción y Disyunción. «Paso 2»: Tabla de verdad. «Paso 3»: Tautología, Contradicción y Contingencia.
3. En el panel, «Qué contiene» anida nivel por nivel: unidad › tema › conceptos. Dentro de cada tema, los conceptos con orden van en pasos numerados (en «Lógica proposicional»: 1 Conjunción, Disyunción, Negación; 2 Tabla de verdad; 3 Contingencia, Contradicción, Tautología) y debajo, los que no tienen un orden registrado.
4. Un área, por ejemplo «Redes y Comunicación» desde «Áreas de la carrera», se abre directamente en esta pestaña: 6 unidades con 14 temas, cada uno con sus pasos (en «Subredes y enrutamiento»: 1 Direccionamiento de subredes, 2 VLSM, 3 CIDR); las 2 unidades sin temas de los sílabos se cuentan aparte.

**Flujo CU-7 · Encontrar material de estudio sobre algo**
1. En la ficha (C) de un tema, por ejemplo «Lógica proposicional», la sección «Material de estudio» muestra el «Sílabo 1INF01», de tipo Sílabo, «trata sobre Lógica proposicional».
2. Al tocarlo, se abre el PDF en otra pestaña.
3. En la ficha de un concepto, la sección dice que un concepto no tiene material propio y muestra el de su tema.

**Flujo CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas**
1. Abre la meta «Entrada y salida de datos desde archivos» (está en «Caminos que cruzan cursos o áreas»).
2. En la pantalla B, pulsa «Ver por: curso». Las líneas pasan a ser INF144 (azul) y 1INF35 (naranja), y «Archivos» aparece como transbordo.
3. Con «área», las líneas son SDF y OS, de CS2023, dibujadas como vía doble con insignia cuadrada.
4. La barra «Líneas del camino» explica cada línea al tocarla. Si una línea contiene también a la meta, lleva la marca «también la meta» y una línea lo explica: «El prerrequisito está en el mismo tema que la meta» (con «tema», «Ingreso y salida de datos»).
5. Si la meta no tiene camino, la pantalla G explica por qué. Si la meta es un curso, remite a sus cursos previos (CU-4).

**Flujo CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene**
1. Busca «ethernet» y abre «Ethernet IEEE 802.3».
2. En su ficha (C), la sección «Es un tipo de y tipos» lista FastEthernet, Gigabit Ethernet y 10GigabitEthernet como «Tipos». Al abrir uno de ellos, la misma sección muestra «Es un tipo de: Ethernet IEEE 802.3».

**Flujo CU-10 · Comprobar de dónde sale un dato**
1. En el camino hasta «Contradicción» (B), toca el «?» del tramo «Tabla de verdad → Contradicción»: se abre el diálogo D.
2. Lee «Contradicción requiere Tabla de verdad» y «… es parte de Lógica proposicional», cada una con su fuente, «Sílabo 1INF01 ↗».
3. Al tocar la fuente, se abre el PDF.
4. Cada ficha muestra «Fuente» bajo el nombre, y cada vecino de «Alrededor» lleva la fuente de su relación.
5. Lo que viene de CS2023 enlaza a la página de la ACM.

## 3. Cobertura

**Pantallas.**
- **A · Entrada:** bienvenida, buscador, metas con camino, caminos que cruzan cursos o áreas, cursos y áreas.
- **B · Camino hasta la meta:** el mapa de metro con «Ver por» y la lista «Indicaciones».
- **C · Ficha de estación:** en el panel lateral; tiene «Fuente», «Qué necesitas antes», «Dónde está en la carrera», «Material de estudio», «Es un tipo de y tipos», «Lo que pide y lo que enseña» (en un curso) y «Alrededor».
- **D · ¿Por qué?:** el diálogo con las relaciones de un tramo o de una línea, cada una con su fuente.
- **E · Qué contiene y en qué orden:** de un tema, una unidad o un área.
- **F · Cursos que conviene llevar antes:** cuando la meta es un curso.
- **G · Sin camino:** los estados vacíos, con su explicación y adónde seguir.

| Caso de uso | Pantallas | Cómo |
|---|---|---|
| CU-1 · Encontrar por dónde empezar | A | Buscador con origen y marca «con camino»; listas de metas, cursos y áreas; si nada coincide, ofrece las áreas. |
| CU-2 · Explorar lo que rodea a un elemento | C | «Alrededor»: vecinos directos por relación y, desplegado en la misma ficha, su segundo nivel; «Ver más» agrega relaciones ahí mismo. |
| CU-3 · Saber qué conceptos necesito antes de aprender uno | B, C, G | Columnas por distancia en el mapa y en «Indicaciones»; «Qué necesitas antes» en la ficha; lo que depende de él si no necesita nada. |
| CU-4 · Saber qué pide un curso y qué curso conviene llevar antes | F, C, D | «Lo que pide» sobre la línea del curso que lo enseña; la ficha lista lo que pide y lo que enseña. |
| CU-5 · Ubicar un concepto o tema dentro de la carrera | C | «Dónde está en la carrera»: una cadena tema › unidad › área por cada tema al que pertenece. |
| CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo | E, G | Pasos de orden en el mapa; «Qué contiene» anidado unidad › tema › conceptos, con pasos numerados dentro de cada tema. |
| CU-7 · Encontrar material de estudio sobre algo | C | «Material de estudio» con su tipo y su tema; en un concepto, el material de su tema. |
| CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas | B, D, G | Mapa con «Ver por: tema · curso · área», transbordos y «?» por tramo y por línea. |
| CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene | C | «Es un tipo de y tipos», con la fuente de cada relación. |
| CU-10 · Comprobar de dónde sale un dato | C, D | «Fuente» en cada ficha y en cada relación; «Ver fuente» abre el sílabo o CS2023. |

**RF-22, en todas las pantallas:** lo que viene de CS2023 se dibuja con cuadrado, insignia cuadrada y vía doble, y lleva la etiqueta «CS2023». Lo que viene de los sílabos se dibuja con círculo y línea llena, y lleva la etiqueta «Sílabo PUCP». La leyenda aclara qué es CS2023.

## 4. Componentes de la aplicación web (esbozo del nivel 3)

| Componente | Responsabilidad | Rutas que consume |
|---|---|---|
| Cliente de la API | Única puerta a R4 (`api(ruta, params)`); codifica las claves | todas |
| Buscador | Punto de entrada por nombre, con la marca «con camino» | `/api/search` |
| Entrada | Metas con camino, cursos y áreas | `/api/learning-path/targets`, `/api/courses` y `/api/areas` (nuevas), `/api/courses/prerequisites` |
| Vista del camino | Meta, pestañas, «Ver por», estados vacíos | `/api/learning-path`, `/api/elements/location`, `/api/courses/prerequisites`, `/api/nodes` |
| Modelo del camino | Convierte `{nodes, edges}` en estaciones, líneas y tramos, y los dispone en columnas; arma la evidencia | ninguna |
| Mapa de metro | Dibujo en D3: tramos octilineales, transbordos, insignias, zoom | ninguna |
| Indicaciones | El mismo camino como lista ordenada, accesible | ninguna |
| Ficha de estación | Fuente, qué necesitas antes, dónde está, material, tipos, lo que pide y enseña, alrededor | `/api/nodes`, `/api/elements/location`, `/api/elements/resources`, `/api/concepts/prerequisites`, `/api/concepts/specializations`, `/api/courses/prerequisites` |
| Diálogo «¿Por qué?» | Relaciones que justifican un tramo o una línea, con su fuente | `/resources/{clave}` (enlace) |
| Panel del operador | Común a las tres propuestas (`../panel-operador/`) | rutas de operación |

```likec4
model {
  extend kms.web {
    apiClient = component 'Cliente de la API' {
      technology 'JavaScript, fetch'
      summary 'Única puerta a la API de R4. Codifica las claves como parámetro de consulta.'
    }
    searchBox = component 'Buscador' {
      technology 'Vue'
      summary 'Punto de entrada por nombre; marca las metas con camino.'
    }
    home = component 'Entrada' {
      technology 'Vue'
      summary 'Metas con camino, cursos y áreas de la carrera.'
    }
    routeView = component 'Vista del camino' {
      technology 'Vue, vue-router'
      summary 'Meta, pestañas (camino, contenido y orden, cursos previos), Ver por y estados vacíos.'
    }
    routeModel = component 'Modelo del camino' {
      technology 'JavaScript'
      summary 'Convierte {nodes, edges} en estaciones, líneas y tramos; dispone las columnas por depth; arma la evidencia.'
    }
    metroMap = component 'Mapa de metro' {
      technology 'D3.js'
      summary 'Dibuja el camino: tramos octilineales, transbordos, insignias y zoom.'
    }
    directions = component 'Indicaciones' {
      technology 'Vue'
      summary 'El mismo camino como lista ordenada y accesible.'
    }
    stationCard = component 'Ficha de estación' {
      technology 'Vue'
      summary 'Fuente, prerrequisitos, ubicación, material, tipos, lo que pide y enseña un curso, vecinos.'
    }
    evidenceDialog = component 'Diálogo ¿Por qué?' {
      technology 'Vue'
      summary 'Relaciones que justifican un tramo o una línea, con su fuente.'
    }
    operatorPanel = component 'Panel del operador' {
      technology 'Vue'
      summary 'Carga de documentos, corridas, descartes y reporte. Común a las propuestas.'
    }
  }

  kms.web.home -> kms.web.searchBox 'Incluye'
  kms.web.searchBox -> kms.web.routeView 'Abre una meta'
  kms.web.home -> kms.web.routeView 'Abre una meta'
  kms.web.routeView -> kms.web.routeModel 'Entrega la respuesta'
  kms.web.routeView -> kms.web.metroMap 'Dibuja el modelo'
  kms.web.routeView -> kms.web.directions 'Lista el modelo'
  kms.web.metroMap -> kms.web.stationCard 'Abre al tocar una estación'
  kms.web.directions -> kms.web.stationCard 'Abre al tocar una parada'
  kms.web.metroMap -> kms.web.evidenceDialog 'Abre al tocar un tramo o una línea'
  kms.web.routeModel -> kms.web.evidenceDialog 'Arma la evidencia'

  kms.web.searchBox -> kms.web.apiClient 'Busca'
  kms.web.home -> kms.web.apiClient 'Metas, cursos y áreas'
  kms.web.routeView -> kms.web.apiClient 'Ruta elevada, composición y orden, prerrequisito entre cursos'
  kms.web.stationCard -> kms.web.apiClient 'Detalle, ubicación, recursos, prerrequisitos, especializaciones'
  kms.web.operatorPanel -> kms.web.apiClient 'Corridas, descartes y reporte, con token'

  kms.web.apiClient -> kms.api.navRoutes 'Consultas de navegación' {
    technology 'HTTP/JSON'
  }
  kms.web.evidenceDialog -> kms.api.navRoutes 'Abre el documento (/resources/{clave})' {
    technology 'HTTP'
  }
  kms.web.stationCard -> kms.api.navRoutes 'Abre el documento (/resources/{clave})' {
    technology 'HTTP'
  }
  kms.web.apiClient -> kms.api.opsRoutes 'Alta de corrida, estado, descartes y reporte' {
    technology 'HTTP/JSON, Bearer'
  }
}

views {
  view webComponents of kms.web {
    title 'Aplicación web: componentes (P3)'
    include *
  }
}
```

## 5. Rutas

**Que ya existen y usa:** `/api/search`, `/api/nodes`, `/api/learning-path?grain=topic|course|area`, `/api/courses/prerequisites`, `/api/elements/location`, `/api/elements/resources`, `/api/concepts/prerequisites`, `/api/concepts/specializations`, `/resources/{clave}`.

**Nuevas necesarias** (simuladas en la maqueta, con la etiqueta «simulado»). Mantienen la forma `{nodes, edges}` del §1 del diseño de las rutas:

| Ruta | Para qué | Respuesta |
|---|---|---|
| `GET /api/learning-path/targets` | Entrada: las metas con camino no vacío, sin que el estudiante tenga que adivinarlas (hoy 35 de 485) | `{"nodes": [{"key", "label", "name_es", "name_en", "layer", "depth"}], "edges": []}`, con `depth` = profundidad máxima del camino |
| `GET /api/courses` | Entrada: los cursos cargados, sin buscar | `{"nodes": [{"key", "label": "Course", "name_es", "name_en", "layer", "course_code"}], "edges": []}` |
| `GET /api/areas` | Entrada: las 17 áreas, distinguiendo las que tienen contenido de los sílabos (CU-1) | `{"nodes": [{"key", "label": "KnowledgeArea", "name_es", "name_en", "layer", "units", "topics", "concepts"}], "edges": []}`, con las cuentas bajo cada área |

En la maqueta, la primera sale de las respuestas reales de `learning-path`, y las otras dos, de `IEKG_SIMULADO`. La sección «Caminos que cruzan cursos o áreas» se arma con la primera y con `learning-path?grain=course|area` de cada meta. En R6 son 2 llamadas por meta: se limita a unas pocas metas o se quita. La búsqueda libre de la maqueta filtra en el cliente cuando el texto no está entre las búsquedas capturadas (rotulado «búsqueda simulada»). En R6 usa `/api/search`: no es una ruta nueva.

## 6. Riesgos

- **Escala.** Hoy los caminos tienen a lo sumo 3 columnas y 7 estaciones. Con más sílabos o una cota mayor, una columna puede tener decenas de estaciones, y el baricentro de una pasada cruza tramos. El orden interno de un área ya llega a 26 estaciones (KA-SDF, unos 2000 px de alto). Zoom y encaje ya están, y elkjs queda como plan B (P3-0017).
- **Legibilidad.** Los nombres largos se cortan a 3 líneas. Los temas se numeran por camino, así que el «1» de un camino no es el «1» de otro. En el camino de un concepto, su propio tema aparece como línea «directo» (*Ingreso y salida de datos*), porque la API lo devuelve así cuando un prerrequisito pertenece a él.
- **Accesibilidad.** Las estaciones, las insignias y los «?» se alcanzan con el teclado y tienen `aria-label`. «Indicaciones» es la lista equivalente al dibujo. El origen no depende del color. No se probó con un lector de pantalla.
- **Datos.** 450 de 485 metas dan camino vacío: la experiencia depende de que los estados vacíos estén bien escritos. `description` casi no existe: la ficha no la necesita.
- **Semántica.** El prerrequisito entre cursos y la ruta elevada son derivaciones distintas. La vista las separa en pestañas con aviso, y la pestaña por omisión de un curso es la de cursos previos (P3-0018).
- **Exploración (CU-2).** «Alrededor» muestra los vecinos directos, no los de segundo nivel que trae `/api/nodes`. «Ver más» consiste en abrir la ficha del vecino, no en sumar sus vecinos a la vista.
- **Sucesores.** Lo que viene después de un concepto solo aparece en su estado vacío («Conceptos que lo necesitan antes») y en «Alrededor».

## 7. Costo documental si se elige

- **Fase 1 de R5 (tesis):** el catálogo común (`../casos-de-uso.md`), los 10 flujos de la sección 2 y las capturas de `capturas/` como wireframes.
- **Fase 2 de R5:**
  - El bloque `likec4` del §4 entra en `docs/architecture/model.c4` (`extend kms.web`) y su vista en `views.c4`. Luego `arch:validate` y, en el hito, exportar los PNG.
  - Los niveles 1 y 2 no cambian.
  - `P3-0015` a `P3-0018` pasan a `docs/decisiones/0015` a `0018`, con 4 filas nuevas en la Tabla 20.
- **R4:**
  - Tres rutas nuevas, `GET /api/learning-path/targets`, `GET /api/courses` y `GET /api/areas`, con sus pruebas y su fila en `docs/diseño-de-las-rutas-de-navegación.md` §5.
  - No son patrones medidos, así que no tocan AC-05.
  - El README raíz suma sus ejemplos con `curl.exe`.
- **Panel del operador:** común a las tres propuestas, no suma costo propio.

## Archivos

| Archivo | Qué es |
|---|---|
| `index.html` | Maqueta: plantilla de Vue, en el mismo HTML |
| `estilos.css` | Estética de señalética de transporte (Jost, IBM Plex Mono) |
| `js/api.js` | `api(ruta, params)` sobre `IEKG_DATOS`, las 3 rutas nuevas simuladas y la búsqueda |
| `js/modelo.js` | Modelo del camino y disposición: funciones puras, probadas en node |
| `js/metro.js` | Dibujo del mapa con D3 |
| `js/app.js` | La aplicación de Vue, con el recorrido sugerido y el interruptor «Ver trazabilidad» |
| `adr/` | P3-0015 (`P3-0015-enfoque-de-navegacion-rutas.md`) a P3-0018 |
| `capturas/` | Wireframes; se rehacen al cerrar la propuesta |
