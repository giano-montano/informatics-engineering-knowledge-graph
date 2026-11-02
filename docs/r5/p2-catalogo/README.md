# P2 · Catálogo de fichas

Maqueta: abrir `index.html` con doble clic. Usa Vue 3 y Vue Router en su variante sin compilación (*build* global desde CDN); en R6 se compila con Vite (ADR P2-0016). Los PDF de los sílabos abren solo si la API corre en el puerto por omisión (`uv run iekg-api`, :8000).

- **Recorrido sugerido:** los 6 pasos comunes a las tres propuestas, en un recuadro que se cierra con × y se reabre con «Recorrido sugerido» en la barra. Cada paso deja la pantalla en su estado; también se abre con `index.html#paso=N`, que la maqueta traduce a la ruta de la ficha correspondiente.
- **Ver trazabilidad:** interruptor de la barra, apagado por omisión. Encendido, cada sección, vista y paso del recorrido muestra su caso de uso y sus códigos (p. ej. `CU-3 · PC1 · RF-11`), según `../casos-de-uso.md`. Apagado, no queda ningún código a la vista.
- **Operador:** el enlace de la barra abre el panel común, `../panel-operador/index.html`.
- **Capturas:** `capturas/` guarda los wireframes; se rehacen al cerrar la propuesta.

## 1. La idea

El conocimiento de la carrera se recorre como una enciclopedia. Cada área, unidad, tema, concepto, curso y sílabo tiene su **ficha**, con URL propia. La ficha lleva migas de ubicación, una frase de entrada armada con sus relaciones (no hay descripciones en el grafo), cifras que llevan a cada sección y secciones con nombres llanos: «Qué necesitas antes», «Qué contiene y en qué orden aprenderlo», «Cursos que lo enseñan o lo piden», «Es un tipo de · Tipos», «Material de estudio», «Camino hasta aquí» (con «Ver por: tema · curso · área») y «Fuente». Cada fila lleva una marca (`↗ 1INF01`) que abre el sílabo del que sale el dato. El grafo aparece solo como un **mini mapa** de lo que rodea al elemento, en el lateral, y se puede agrandar. El enfoque de navegación responde mejor a «¿qué hay sobre esto, y qué necesito antes?» (E16: 72,1 % y 83,1 %).

## 2. Flujos

Los casos de uso son comunes a las tres propuestas y están en [`../casos-de-uso.md`](../casos-de-uso.md). Aquí va un flujo por caso de uso: los pasos con que esta interfaz lo resuelve. Las pantallas se nombran con las letras de la sección 3.

**Flujo CU-1 · Encontrar por dónde empezar**
1. En la portada (A), el estudiante lee la bienvenida y escribe «lógica» en el buscador.
2. Ve los resultados (B), agrupados en temas y conceptos; cada fila dice si viene de CS2023 o de un sílabo PUCP. Hasta 20 resultados.
3. Abre el tema «Lógica proposicional» y llega a su ficha (D).
4. Sin escribir nada, también puede bajar en la portada (A) a los 4 cursos con sílabo o a las 17 áreas, separadas en 7 «Con contenido de los sílabos» y 10 «Por ahora, solo en CS2023».
5. Si busca «árbol», la pantalla (B) dice que ningún sílabo cargado trata ese tema y ofrece recorrer las áreas.

**Flujo CU-2 · Explorar lo que rodea a un elemento**
1. En la ficha de «Contradicción» (C), el recuadro «Mapa: lo que lo rodea» muestra sus vecinos: el tema, los conceptos que necesita, el curso que lo enseña y algunos vecinos de estos.
2. Las secciones de la ficha nombran cada relación por escrito: «Dónde está en la carrera», «Qué necesitas antes», «Qué depende de él», «Cursos que lo enseñan o lo piden».
3. Pulsa un vecino, en el mapa o en una lista: su ficha pasa a estar en foco. El botón «atrás» del navegador vuelve a la anterior.
4. Pulsa «Agrandar» (H): ve el mapa con nombres y zoom, y un anillo punteado en los vecinos que tienen más relaciones de las que caben. Para verlas, abre la ficha de ese vecino: el mapa no las agrega en el sitio.

**Flujo CU-3 · Saber qué conceptos necesito antes de aprender uno**
1. Abre la ficha de «Contradicción» (C).
2. En «Qué necesitas antes» ve, en «Directos», «Tabla de verdad», y en «A 2 pasos», «Conjunción», «Disyunción» y «Negación», cada uno con quién lo necesita («lo necesita Tabla de verdad»).
3. Para saber por qué uno va antes, mira la marca `↗ 1INF01` de su fila: es el sílabo que lo afirma (flujo CU-10).
4. Si el concepto no tiene nada antes (p. ej. «Ethernet IEEE 802.3»), la sección lo dice y remite a «Qué depende de él», en la misma ficha.

**Flujo CU-4 · Saber qué pide un curso y qué curso conviene llevar antes**
1. Abre «Técnicas de Programación» (INF144) desde la portada (A) o el buscador; llega a su ficha (F).
2. En «Lo que pide» ve los tres conceptos que el sílabo da por sabidos: «Algoritmia», «Estructuras de control de flujo» y «Subprogramas», cada uno con el curso que lo enseña.
3. En «Cursos que conviene llevar antes» ve «Fundamentos de Programación (1INF01)», con esos tres conceptos debajo como evidencia y las marcas de los dos sílabos.
4. En «Lo que enseña» ve sus 43 conceptos agrupados en 9 temas.

**Flujo CU-5 · Ubicar un concepto o tema dentro de la carrera**
1. En la ficha de «Contradicción» (C), las migas de arriba dicen: Fundamentos Matemáticos y Estadísticos › Matemática Discreta › Lógica proposicional.
2. La sección «Dónde está en la carrera» repite la cadena con la fuente de cada eslabón: el sílabo ubicó el tema en la unidad (`↗ 1INF01`); CS2023, la unidad en el área (`↗ CS2023`).
3. Pulsa un eslabón y llega a la ficha de ese tema (D), unidad o área (E).

**Flujo CU-6 · Ver qué contiene un tema, una unidad o un área, y en qué orden aprenderlo**
1. En la ficha de «Lógica proposicional» (D), «Qué contiene y en qué orden aprenderlo» agrupa sus 10 conceptos en tres pasos: primero «Negación», «Conjunción», «Disyunción» y otros; luego «Tabla de verdad»; al final «Tautología», «Contradicción» y «Contingencia».
2. Cada concepto dice en qué se apoya («se apoya en Tabla de verdad»).
3. En la ficha de una unidad o un área (E), «Qué contiene» lista sus partes nivel por nivel: unidades de CS2023 y, dentro, los temas de los sílabos con sus conceptos. En «Redes y Comunicación», 6 unidades con contenido y 2 que por ahora solo están en CS2023.

**Flujo CU-7 · Encontrar material de estudio sobre algo**
1. En la ficha de «Lógica proposicional» (D), «Material de estudio» muestra el «Sílabo 1INF01», de tipo sílabo, que trata directamente sobre el tema.
2. En un área (E), cada sílabo dice por qué partes llega («llega por sus partes: …»).
3. En un concepto (C), la sección avisa que un concepto no tiene material propio y muestra el de su tema, con un enlace al tema.
4. Pulsa «Abrir el sílabo (PDF)»: el documento se abre en otra pestaña.

**Flujo CU-8 · Ver el camino hasta una meta, por temas, cursos o áreas**
1. Abre la ficha de «Entrada y salida de datos desde archivos» (C) y baja a «Camino hasta aquí».
2. En «Ver por», elige «curso»: en «Directo» aparecen «Administración de Sistemas Operativos (1INF35)» y «Técnicas de Programación (INF144)»; al final, «Aquí», la meta.
3. Debajo de cada curso ve el concepto que lo justifica, «Archivos», con «lo necesita Entrada y salida de datos desde archivos» y sus marcas de fuente.
4. Cambia a «tema» o «área» y el mismo camino se agrupa en «Administración local» o en «Sistemas Operativos». La elección queda en la URL.
5. Si la meta es un curso, el camino sale vacío: la sección explica por qué y lleva a «Cursos que conviene llevar antes» (flujo CU-4).

**Flujo CU-9 · Ver de qué es un tipo un concepto y qué tipos tiene**
1. Busca «ethernet» y abre «Ethernet IEEE 802.3» (C).
2. En «Es un tipo de · Tipos» ve, en «Tipos», «FastEthernet», «Gigabit Ethernet» y «10GigabitEthernet».
3. Abre «FastEthernet»: la misma sección dice que «Es un tipo de» «Ethernet IEEE 802.3».

**Flujo CU-10 · Comprobar de dónde sale un dato**
1. En la ficha de «Contradicción» (C), la fila «Tabla de verdad» de «Qué necesitas antes» lleva la marca `↗ 1INF01`; al pasar el cursor dice «Ver fuente: Sílabo 1INF01».
2. La pulsa y el sílabo de Fundamentos de Programación se abre en otra pestaña.
3. Al pie, «Fuentes de esta ficha» lista los documentos citados, y la sección «Fuente», el documento del que sale el concepto. Las filas de CS2023 enlazan a su página en la ACM.

## 3. Cobertura

Pantallas:

- **A · Portada:** bienvenida, buscador, cursos con sílabo, áreas (con contenido de los sílabos / por ahora solo en CS2023) y «Cómo leer el catálogo».
- **B · Resultados de búsqueda:** resultados agrupados por clase, con su origen; estado vacío.
- **C · Ficha de concepto:** dónde está, qué necesitas antes, camino hasta aquí, qué depende de él, cursos, tipos, material, fuente.
- **D · Ficha de tema:** dónde está, qué contiene y en qué orden, camino hasta aquí, material, fuente.
- **E · Ficha de unidad o de área:** dónde está (unidad), qué contiene, camino hasta aquí, material, fuente.
- **F · Ficha de curso:** lo que pide, cursos que conviene llevar antes, lo que enseña, camino hasta aquí, material, fuente.
- **G · Ficha de sílabo:** trata sobre (curso y temas) y el botón para abrir el documento.
- **H · Mapa agrandado:** diálogo con el mapa de lo que rodea a la ficha, con nombres, zoom, teclado y leyenda.

En todas las fichas (C a G), el lateral lleva el mini mapa, el índice «En esta ficha» y «Datos de la ficha».

| Caso de uso | Pantallas | Cómo |
|---|---|---|
| CU-1 · Encontrar por dónde empezar | A, B | Buscador en la portada y en la barra; portada con cursos y áreas sin buscar (simulada); estado vacío que ofrece las áreas. |
| CU-2 · Explorar lo que rodea a un elemento | C–G, H | Mini mapa y secciones con cada relación por escrito; cada vecino lleva a su ficha; el mapa agrandado marca los vecinos con más relaciones, que se ven en su ficha. |
| CU-3 · Saber qué conceptos necesito antes | C | «Qué necesitas antes», en «Directos» y «A N pasos», con quién lo necesita y su fuente; «Qué depende de él». |
| CU-4 · Qué pide un curso y qué curso llevar antes | F | «Lo que pide», «Cursos que conviene llevar antes» con los conceptos como evidencia, «Lo que enseña» por tema. |
| CU-5 · Ubicar un concepto o tema | C, D, E | Migas y «Dónde está en la carrera», con la fuente de cada eslabón. |
| CU-6 · Qué contiene y en qué orden | D, E | «Qué contiene y en qué orden aprenderlo» (pasos por prerrequisitos internos); unidades y temas desplegables. |
| CU-7 · Encontrar material de estudio | C, D, E, F, G | «Material de estudio», con su tipo y por qué parte llega; en un concepto, el de su tema; botón para abrir el sílabo. |
| CU-8 · Ver el camino hasta una meta | C, D, E, F | «Camino hasta aquí» con «Ver por: tema · curso · área», etapas por distancia y la evidencia de cada paso; meta curso: explica el vacío y remite a CU-4. |
| CU-9 · De qué es un tipo y qué tipos tiene | C | «Es un tipo de · Tipos». |
| CU-10 · Comprobar de dónde sale un dato | C–G | Marca `↗` en cada fila, «Fuentes de esta ficha», sección «Fuente» y botón del sílabo en su ficha. |

**RF-22, en todas las pantallas:** CS2023 y Sílabo PUCP se distinguen por la insignia de texto, por la forma (cuadrado o círculo, en listas, migas y mapa) y por el filete de fichas y tarjetas (doble arriba o lateral); el color solo refuerza. La portada y la leyenda del mapa aclaran que CS2023 es el estándar internacional del currículo de computación (ACM/IEEE).

## 4. Componentes de la aplicación web (esbozo C4, nivel 3)

| Componente | Responsabilidad | Rutas que consume |
|---|---|---|
| Enrutador | Una URL por vista (`/`, `/buscar?q=`, `/ficha?key=&grano=`); atrás y adelante | — |
| Cliente de la API | Única puerta a R4 (`api(ruta, params)`); añade el token en las rutas de operación | todas |
| Modelo de fichas | Ordena y agrupa las respuestas en secciones, migas, cifras y marcas de fuente; no calcula patrones | (vía el cliente) |
| Portada | Áreas y cursos sin buscar; separa las áreas con contenido de los sílabos | `GET /api/catalog` (nueva) |
| Búsqueda | Resultados agrupados por clase, con su origen; estado vacío | `GET /api/search` |
| Ficha | Cabecera, secciones por clase, «Fuentes de esta ficha» y lateral | `/api/nodes`, `/api/elements/location`, `/api/concepts/prerequisites`, `/api/concepts/specializations`, `/api/courses/prerequisites`, `/api/elements/resources` |
| Sección «Camino hasta aquí» | Camino con «Ver por: tema · curso · área» | `GET /api/learning-path` |
| Mini mapa | Dibuja el vecindario que la ficha ya pidió; lo agranda en un diálogo | (respuesta de `/api/nodes`) |
| Marcas de fuente | Abren el documento de cada afirmación en otra pestaña | `GET /resources/{key}` |
| Trazabilidad | Muestra u oculta el caso de uso y los códigos de cada sección | — |
| Panel del operador (común) | El de `docs/r5/panel-operador/`, enlazado desde la barra | `POST /api/runs`, `GET /api/runs`, `/api/runs/{id}`, `/api/runs/{id}/discards`, `/api/audit-reports/latest` |

El recorrido sugerido es solo de la maqueta y no pasa a R6.

```likec4
// Borrador para agregar al modelo existente (docs/architecture/model.c4 y views.c4). No validado.
model {
  extend kms.web {
    router = component 'Enrutador' {
      technology 'Vue Router 5'
      summary 'Una URL por vista: portada, búsqueda y ficha.'
    }
    catalogHome = component 'Portada' {
      technology 'Vue 3'
      summary 'Áreas de CS2023 y cursos con sílabo, sin buscar.'
    }
    search = component 'Búsqueda' {
      technology 'Vue 3'
      summary 'Resultados por clase, con su origen, y estado vacío.'
    }
    card = component 'Ficha' {
      technology 'Vue 3'
      summary 'Migas, secciones por clase (PC1 a PC7), fuentes y procedencia.'
    }
    pathSection = component 'Camino hasta aquí' {
      technology 'Vue 3'
      summary 'Ruta elevada con selector de agrupamiento (PC6).'
    }
    miniMap = component 'Mini mapa' {
      technology 'D3.js 7 (d3-force, SVG)'
      summary 'Vecindario del elemento en foco; se agranda con zoom.'
    }
    cardModel = component 'Modelo de fichas' {
      technology 'JavaScript'
      summary 'Agrupa las respuestas {nodes, edges} en secciones y marcas de fuente.'
    }
    apiClient = component 'Cliente de la API' {
      technology 'fetch'
      summary 'Única puerta a R4; añade el token en operación.'
    }
    opsPanel = component 'Panel del operador' {
      technology 'Vue 3'
      summary 'Común a las tres propuestas: carga, corridas, descartes y reporte.'
    }
  }

  student -> kms.web.catalogHome 'Entra sin buscar'
  student -> kms.web.search 'Busca por nombre'
  student -> kms.web.card 'Lee la ficha y abre los documentos'
  operator -> kms.web.opsPanel 'Sube documentos y revisa corridas'

  kms.web.router -> kms.web.card 'Abre la ficha de una clave'
  kms.web.card -> kms.web.cardModel 'Pide secciones'
  kms.web.card -> kms.web.miniMap 'Entrega el vecindario'
  kms.web.card -> kms.web.pathSection 'Incluye'
  kms.web.pathSection -> kms.web.cardModel 'Pide el camino por agrupamiento'
  kms.web.catalogHome -> kms.web.apiClient 'Pide el catálogo'
  kms.web.search -> kms.web.apiClient 'Pide la búsqueda'
  kms.web.cardModel -> kms.web.apiClient 'Pide detalle y patrones'
  kms.web.opsPanel -> kms.web.apiClient 'Pide corridas y reporte'

  kms.web.apiClient -> kms.api.navRoutes 'Consultas de navegación' {
    technology 'HTTP/JSON'
  }
  kms.web.card -> kms.api.navRoutes 'Abre el documento de una afirmación' {
    technology 'HTTP (PDF)'
  }
  kms.web.apiClient -> kms.api.opsRoutes 'Alta de corrida, estado, descartes y reporte' {
    technology 'HTTP/JSON, token Bearer'
  }
}

views {
  view webComponents of kms.web {
    title 'Aplicación web: componentes (P2)'
    include *
  }
}
```

## 5. Rutas

**Usa (ya existen en R4):** `GET /api/search`, `/api/nodes`, `/api/concepts/prerequisites`, `/api/concepts/specializations`, `/api/courses/prerequisites`, `/api/elements/location`, `/api/elements/resources`, `/api/learning-path` y `/resources/{key}`. Las cinco de operación las usa el panel común.

**Rutas nuevas necesarias**

1. `GET /api/catalog`: la portada sin buscar. En la maqueta sale de `IEKG_SIMULADO` y va marcada «simulado».
   ```json
   {"areas": [{"key": "…#KA-NC", "name_es": "Redes y Comunicación", "name_en": "Networking and Communication",
               "units": 8, "topics": 14, "concepts": 132}],
    "courses": [{"key": "b2d9c106-…", "name_es": "Técnicas de Programación", "code": "INF144"}]}
   ```
   Los conteos son el número de unidades, temas y conceptos bajo cada área por `PART_OF`. Se aparta de la forma `{nodes, edges}`; la alternativa es `{nodes}` con los conteos como campos opcionales del nodo; se decide al agregarla a R4.

**Ampliación recomendada (no bloquea):** que `/api/courses/prerequisites` traiga también el tema de cada concepto que enseña (nodo `Topic` y arista `PART_OF`). Hoy, para agrupar «Lo que enseña» por tema, la ficha pide `/api/elements/location` por cada concepto: 43 llamadas en INF144. La forma no cambia: `{nodes, edges}` con nodos `Topic` y aristas `PART_OF` adicionales.

**Simulado en la maqueta, sin ruta nueva:** la búsqueda de un texto que no está entre las 15 capturadas se filtra en el cliente y se marca «búsqueda simulada» (en R6 responde `/api/search`).

## 6. Riesgos

- **Escala.** La ficha de un área grande es larga (KA-NC: 8 unidades, 14 temas, 132 conceptos); se pliega a 8 filas por grupo, y los temas y conceptos van bajo «Ver N temas». Con muchos más sílabos, la portada y «Lo que enseña» crecen linealmente: el catálogo aguanta mejor que un lienzo, pero pedirá paginación en R4. El mapa está acotado por el detalle (25 vecinos y 5 de segundo nivel).
- **Secciones recortadas.** «Qué depende de él» y «Cursos que lo enseñan o lo piden» salen de `/api/nodes`, con la cota de 25 vecinos. Si el foco tiene `more_neighbors`, «Datos de la ficha» avisa que algunas listas pueden estar recortadas; una ruta inversa de prerrequisitos lo resolvería.
- **Exploración a pedido (CU-2).** El mapa no agrega en el sitio los vecinos de un vecino: los marca con un anillo y remite a su ficha. Es coherente con el enfoque, pero no es la expansión incremental que describe el caso de uso.
- **Legibilidad.** El mini mapa pequeño solo rotula el foco: sirve para orientarse, no para leer. Las marcas de fuente se repiten en cada fila y son pequeñas.
- **Accesibilidad.** RF-22 va por forma, filete y texto, no solo por color. El mapa agrandado se recorre con teclado, y las mismas relaciones están escritas en las secciones. Pendiente: medir el contraste del ocre de CS2023 (#8a5a12 sobre #f7efe1) y el tamaño de las marcas (10,5 px), y probar con lector de pantalla.
- **Dependencias externas.** Las fuentes vienen de Google Fonts (hay respaldo en Georgia y system-ui); en R6 conviene servirlas con la aplicación.

## 7. Costo documental si se elige

- **Fase 1 de R5 (tesis):** el catálogo común de casos de uso (`../casos-de-uso.md`), los 10 flujos de la sección 2 y las capturas de `capturas/` como wireframes.
- **Fase 2 de R5:** el bloque `likec4` de §4 pasa a `docs/architecture/model.c4` (extensión de `kms.web`) y `views.c4` (vista `webComponents`), con `npm run arch:validate`. Los niveles 1 y 2 no cambian: `kms.web` ya existe con sus dos relaciones.
- **ADR:** P2-0015 a P2-0018 pasan a `docs/decisiones/` como 0015 a 0018, cada uno con su fila en la Tabla 20 (enfoque de navegación, framework, librería del mapa, procedencia y capas): [`P2-0015`](adr/P2-0015-enfoque-de-navegacion-catalogo-de-fichas.md), [`P2-0016`](adr/P2-0016-framework-vue-y-vue-router.md), [`P2-0017`](adr/P2-0017-mini-mapa-con-d3.md), [`P2-0018`](adr/P2-0018-procedencia-y-capas-en-la-ficha.md).
- **R4:** una ruta nueva, `GET /api/catalog` (con su prueba y su fila en la tabla de rutas de `docs/diseño-de-las-rutas-de-navegación.md` §5), y opcionalmente la ampliación de `/api/courses/prerequisites` con el tema de cada concepto.
- **Requisitos:** anotar en `docs/requisitos-funcionales-de-referencia.md` que RF-19 se cumple con portada, fichas y mini mapa.
