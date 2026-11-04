# R5: propuestas del mecanismo de navegación

**Estado:** tres propuestas alternativas; ninguna elegida todavía.

Tres propuestas del mecanismo de navegación, cada una con un enfoque de navegación distinto, más
un panel del operador común. Todas usan datos **reales** del grafo de desarrollo (backbone CS2023 y
4 sílabos), capturados de la API de R4 el 2026-10-29. Lo que la API no da está rotulado en pantalla
como «simulado».

Las tres resuelven los mismos casos de uso, definidos en [`casos-de-uso.md`](casos-de-uso.md): diez
del estudiante y uno del operador. Cada README de propuesta describe sus **flujos**, uno por caso de
uso, que son los pasos con que esa interfaz resuelve cada uno.

| | Carpeta | Nombre en pantalla | Enfoque de navegación |
|---|---|---|---|
| P1 | [`p1-lienzo/`](p1-lienzo/README.md) | Constelación | El lienzo del grafo es el protagonista: foco, vecindario y **lentes** (una por patrón) sobre el mismo lienzo. |
| P2 | [`p2-catalogo/`](p2-catalogo/README.md) | Catálogo del conocimiento | Enciclopedia de **fichas** con URL propia; el grafo es un mini mapa secundario. |
| P3 | [`p3-rutas/`](p3-rutas/README.md) | Itinerario | Se elige una **meta** y se ve el camino hasta ella como mapa de metro, agrupado por tema, curso o área a elección. |
| — | [`panel-operador/`](panel-operador/README.md) | Panel del operador | Una pantalla sobria para RF-23, integrable en cualquiera de las tres. |

## Cómo abrirlas

- Doble clic en el `index.html` de cada carpeta. No hace falta servidor ni API: los datos vienen de
  [`datos/datos.js`](datos/LEEME.md) (7,8 MB, tarda alrededor de un segundo).
- Las tres traen el mismo **recorrido sugerido** de seis pasos (ver abajo), que se cierra con ×. Cada
  paso se abre directo con `index.html#paso=N`.
- Los códigos de trazabilidad (caso de uso, pregunta de competencia, requisito) no se ven por
  omisión; el interruptor «Ver trazabilidad» los muestra junto a cada sección.
- **PDF de los sílabos (RF-21):** los enlaces apuntan a `http://localhost:8000/resources/<clave>`,
  el localizador guardado en el grafo. Abren con la API levantada en el puerto por omisión:
  `docker compose up -d` y `uv run iekg-api`. El de CS2023 abre la página de la ACM.
- Las capturas de P3 (`p3-rutas/capturas/`) son sus wireframes de la Fase 1. Las de P1 y P2 se
  rehacen al cerrar la propuesta.
- Las librerías y las fuentes vienen de jsDelivr y Google Fonts, así que hace falta conexión.

## Recorrido sugerido

El mismo en las tres propuestas, para compararlas sobre la misma historia: un estudiante que quiere
aprender *Contradicción* y, después, mira más allá.

| Paso | Qué se hace | Caso de uso |
|---|---|---|
| 1 | Busca «lógica» y abre el tema «Lógica proposicional». | CU-1 |
| 2 | Mira qué contiene, en qué orden conviene aprenderlo y su material de estudio. | CU-6, CU-7 |
| 3 | Abre «Contradicción»: ¿qué necesitas saber antes? | CU-3 |
| 4 | ¿De dónde sale que «Contradicción» requiere «Tabla de verdad»? Ver la fuente. | CU-10 |
| 5 | El camino hasta «Entrada y salida de datos desde archivos», visto por cursos. | CU-8 |
| 6 | «Técnicas de Programación»: qué pide y qué curso conviene llevar antes. | CU-4 |

CU-2 y CU-5 aparecen dentro de los pasos 1 a 3, sin un paso propio. CU-9 queda fuera del recorrido:
con el ejemplo de *Ethernet IEEE 802.3*, cada README lo cubre en su flujo.

## Vocabulario de la interfaz

Las tres usan las mismas palabras para lo mismo, en lenguaje llano y sin códigos.

| Término del diseño | En pantalla |
|---|---|
| Prerrequisitos de un concepto (PC1) | «Qué necesitas antes» |
| Prerrequisito entre cursos (PC2) | «Cursos que conviene llevar antes», «Lo que pide», «Lo que enseña» |
| Ubicación (PC3) | «Dónde está en la carrera» |
| Composición y orden (PC4) | «Qué contiene», «en qué orden aprenderlo» |
| Recursos (PC5) | «Material de estudio» |
| Ruta elevada (PC6) y grano | «Camino hasta aquí»; «Ver por: tema · curso · área» |
| Especialización (PC7) | «Es un tipo de», «Tipos» |
| Procedencia (RF-21) | «Fuente», «Ver fuente» |
| Capa de referencia | «CS2023», el estándar internacional del currículo de computación (ACM/IEEE) |
| Capa institucional | «Sílabo PUCP» |

## Comparación

| | P1 · Lienzo | P2 · Catálogo | P3 · Rutas |
|---|---|---|---|
| Necesidad que atiende mejor (E16) | Entender cómo se conectan las áreas (61 %) y descubrir temas (52,6 %) | Encontrar recursos de estudio (72,1 %) | Saber qué conceptos previos se necesitan (83,1 %) |
| Punto fuerte | Muestra el grafo como grafo; las lentes ponen los siete patrones sobre el mismo dibujo. | Se sostiene con datos escasos y sin descripciones; cada fila lleva su sílabo (RF-21 por arista); URL enlazables; la más accesible. | Responde la necesidad más votada en una sola pantalla; el «¿por qué?» de cada tramo muestra la evidencia, y el cambio de grano es inmediato. |
| Punto débil | Legibilidad y accesibilidad: un área trae 158 nodos (resuelto con anillos y zoom), y un lienzo es difícil de recorrer con teclado o lector de pantalla. | El grafo queda en segundo plano: la exploración visual se concentra en un mapa acotado al vecindario. | Depende de que haya rutas: hoy 35 destinos tienen una, de profundidad 2 como máximo, y la vista de un curso se apoya en el prerrequisito entre cursos (PC2). |
| Stack para R6 | Svelte 5.57.3 + Vite 8.3.5 · D3 7.9.0 (d3-force, SVG) | Vue 3.5.44 + Vue Router 5.4.0 + Vite · D3 7.9.0 (mini mapa) | Vue 3.5.44 + Vue Router 5.4.0 + Vite 8.3.5 · D3 7.9.0 con disposición por columnas propia |
| Rutas nuevas en R4 | `GET /api/overview` (portada: áreas con conteos y cursos) | `GET /api/catalog` (ídem); opcional, el tema de cada concepto en `/api/courses/prerequisites` | `GET /api/learning-path/targets` (metas con camino), `GET /api/courses`, `GET /api/areas` |
| Esfuerzo para R6 | **Alto:** simulación de fuerzas, expansión incremental, lentes, rendimiento y una alternativa accesible. | **Bajo:** listas y fichas, más un mini mapa acotado a 25 vecinos. | **Medio:** un dibujo a medida por grano, el caso especial del curso y los estados vacíos. |

Las tres distinguen la capa (RF-22) por **forma y etiqueta de texto**, no solo por color: P1 usa
hexágono y círculo; P2 y P3, cuadrado y círculo, con las insignias «CS2023» y «Sílabo». Las tres
encapsulan los datos en `api(ruta, params)`: en R6 esa función se cambia por un `fetch`.

Las versiones se verificaron en el registro de npm el 2026-10-29. D3 7.9.0 es común a las tres (es
la última estable).

## Datos que condicionan las propuestas

- **`description` solo existe en un nodo** (CS2023): ninguna ficha depende de ella.
- **Ruta elevada (PC6) con un curso como objetivo:** sale vacía en los 4 cursos, porque sus
  prerrequisitos entre conceptos quedan dentro del propio curso. El prerrequisito entre cursos
  (1INF01 → INF144, INF238 → 1INF35) sale de `/api/courses/prerequisites` (PC2).
- **Ruta elevada con grano tema:** la ruta de un concepto incluye su propio tema cuando el
  prerrequisito pertenece a él, porque el objetivo es el concepto y no su tema (diseño de las rutas,
  §6). Por ejemplo, *Entrada y salida de datos desde archivos* muestra *Ingreso y salida de datos*.
- **Portada sin buscar:** las tres piden una ruta nueva con el mismo contenido (áreas con conteos y
  cursos) bajo nombres distintos. La propuesta elegida fija el nombre y la forma.

## Estructura

```
casos-de-uso.md   los once casos de uso, comunes a las tres propuestas
datos/            datos.js, operacion.json, simulado.json y LEEME.md (forma de cada respuesta)
p1-lienzo/        index.html, js/, estilos.css, README.md, adr/P1-0015…0018
p2-catalogo/      index.html, *.js, estilos.css, README.md, adr/P2-0015…0018
p3-rutas/         index.html, js/, estilos.css, README.md, adr/P3-0015…0018, capturas/
panel-operador/   index.html, panel.js, panel.css, README.md
```

Cada README de propuesta cierra con su **costo documental**: qué pasa a la Fase 1 y a la Fase 2 de
R5, el bloque `likec4` que extiende `kms.web` y las filas de la Tabla 20. Los ADR llevan prefijo
provisional (`P1-`, `P2-`, `P3-`); los de la propuesta elegida pasan a `docs/decisiones/` desde el
0015.
