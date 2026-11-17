# InfoKnows

La aplicación web de navegación del grafo de conocimiento de Ingeniería
Informática (resultado R6 de la tesis). Un estudiante busca un tema, un
concepto o un curso, lo pone en foco en un mapa y le hace preguntas: qué
necesita antes, dónde está en la carrera, qué contiene, con qué material
estudiarlo y de dónde sale cada dato. Incluye el panel del operador, que sube
sílabos y sigue su ingesta.

Es una aplicación de una sola página: Svelte 5.57.3 con Vite 8.3.8
([ADR-017](../docs/decisiones/0017-framework-de-la-aplicacion-web-svelte.md))
y D3 7.9.2 en SVG
([ADR-018](../docs/decisiones/0018-visualizacion-con-d3-en-svg.md)). Solo
presenta: toda la lógica de navegación vive en la API.

## Levantarla en desarrollo

Hace falta Node 20.19, 22.12 o 24 en adelante (ADR-017), y la API respondiendo en el puerto 8000 con
el grafo cargado (ver el [README de la raíz](../README.md)).

```powershell
# En la raíz del repositorio: la base y la API
docker compose up -d neo4j
uv run iekg-api

# En web/
npm ci
npm run dev               # http://localhost:5173
```

La aplicación llama siempre a `/api` y `/resources` en relativo. En desarrollo,
Vite reenvía esas rutas a la API (`vite.config.js`); si la API está en otra
dirección, se indica con `IEKG_DEV_API`:

```powershell
$env:IEKG_DEV_API = "http://127.0.0.1:9000"; npm run dev
```

`npm run build` deja el compilado estático en `dist/`, y `npm run preview` lo
sirve en <http://localhost:4173> con el mismo reenvío.

## Levantarla desplegada

El `docker-compose.yml` de la raíz levanta todo: `docker compose up -d --build`.
El contenedor `web` compila la aplicación y la sirve con nginx, que reenvía
`/api` y `/resources` a la API bajo el mismo origen
([ADR-007](../docs/decisiones/0007-invocacion-de-la-ingesta-y-escritor-unico.md)):
por eso no hay CORS ni ninguna dirección con el host escrito. El puerto, el 80 por omisión, se elige
con `IEKG_WEB_PORT` en `.env`. Los pasos completos están en el README de la
raíz, sección «Desplegar con Docker».

Los documentos subidos guardan en el grafo un localizador con el host
([ADR-009](../docs/decisiones/0009-documentos-subidos-localizador-y-datos-declarados.md)).
Cuando un localizador apunta a `/resources/…`, la aplicación usa solo su ruta,
así que el PDF abre desde el origen en que se sirve la web; un enlace externo,
como el de CS2023, queda como está.

## Cómo se usa

- **Inicio.** El mapa muestra las áreas de CS2023 alrededor y los cursos con
  sílabo al centro. Las áreas que ya tienen temas de los sílabos se ven
  encendidas, con sus cifras; el panel lista lo mismo en texto.
- **Buscar.** `Ctrl K` o `/` llevan al buscador; las flechas recorren los
  resultados y Enter abre uno.
- **Foco y preguntas.** El elemento elegido queda al centro. Las pestañas de la
  cabecera son las preguntas que aplican a su clase; la cabecera responde la
  elegida en una frase y dice cómo leer el dibujo.
- **Capa y fuente.** Un hexágono con contorno es de CS2023 y un círculo relleno,
  de un sílabo; el color es la clase. Una línea, o el enlace «fuente» de la
  ficha, muestra qué documento afirma esa relación, con el enlace para abrirlo.
- **Teclado.** Tab recorre los puntos del mapa, las flechas pasan al punto más
  cercano, Enter pone un punto en foco y `+` trae sus conexiones.
  `Alt ←` vuelve al elemento anterior. Todo lo que el mapa dibuja está también
  como lista en la ficha de la derecha.
- **Operador.** El botón «Operador» abre el panel. Pide el token, que se teclea
  y se guarda solo en la pestaña: no está en el código ni en el compilado.

La dirección refleja lo que se ve: `?key=<clave>&lente=<pregunta>&ver=<tema|curso|area>`,
o `?panel=operador`. Se puede copiar y volver a abrir.

## Estructura

Los componentes siguen la vista `webComponents` del modelo C4
(`docs/architecture/`), uno a uno:

| Componente del modelo | Archivo |
|---|---|
| Estado de la exploración | `src/lib/exploration-state.svelte.js` |
| Cliente de la API | `src/lib/api-client.js` |
| Buscador | `src/components/Search.svelte` |
| Inicio | `src/components/Home.svelte` |
| Lienzo del grafo | `src/components/GraphCanvas.svelte`, con `src/lib/canvas-renderer.js` (D3) y `src/lib/layouts.js` (una disposición por pregunta) |
| Cabecera de contexto | `src/components/ContextHeader.svelte`, con `src/lib/lens-summary.js` |
| Panel del foco | `src/components/FocusPanel.svelte` |
| Línea de paradas | `src/components/StopsLine.svelte` |
| Panel del operador | `src/components/OperatorPanel.svelte` |

Lo demás es apoyo de esos componentes:

- `src/lib/vocabulary.js`: cómo se llama en pantalla cada clase, capa, relación
  y pregunta.
- `src/lib/graph-reading.js`: lecturas de una respuesta `{nodes, edges}`. Solo
  reordenan lo que la API devolvió; no derivan nodos ni aristas.
- `src/lib/examples.svelte.js`: las búsquedas de ejemplo del inicio. Ninguna
  está escrita en la aplicación: son nombres tomados al azar del grafo
  cargado, de los temas y conceptos junto a dos cursos.
- `src/components/`: `NodeLink`, `LayerMark`, `DocLink`, `RelationCard` e `Icon`,
  piezas que comparten la ficha, la cabecera y el buscador.
- `src/app.css`: los colores, la tipografía y los estilos del lienzo. El color
  tiene dos usos y ninguno más: el de un punto es su clase y el de una línea,
  su relación. Lo que la interfaz marca (selección, foco de teclado) va en
  blanco. La tipografía es Atkinson Hyperlegible Next, servida desde el propio
  compilado.

Los umbrales con que el mapa resume lo que no cabe con nombre (14 vecinos por
grupo, 24 conceptos en un árbol, 4 unidades sin temas y 10 vecinos de segundo
nivel) están al inicio de `src/lib/layouts.js`.

## Recorrido técnico

`tests/walkthrough.mjs` recorre con Playwright los casos CA-01 a CA-10 del
[plan de pruebas de aceptación](../casos-de-prueba/plan-de-pruebas-de-aceptacion-r6.md)
contra la API real, una vez con el puntero y otra solo con el teclado, y
compara lo que se ve con lo que responde la API. Es una comprobación previa:
la prueba de aceptación se hace con personas.

```powershell
npx playwright install chromium      # una vez
npm run walkthrough                  # contra http://localhost:5173
$env:INFOKNOWS_URL = "http://localhost"; npm run walkthrough   # contra el despliegue
node tests/walkthrough.mjs --shots ../docs/r6/capturas             # y guarda las capturas
```

`tests/operator-walkthrough.mjs` hace lo mismo con CA-11. Sube un documento, así
que **escribe en el grafo**: se corre sobre un grafo de ensayo, y después se
vuelve a cargar y a reaplicar.

Los ejemplos de los dos recorridos son los del plan, que dependen del grafo
cargado: con el grafo final hay que fijarlos de nuevo.
