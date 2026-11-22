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
el grafo cargado (ver la [guía de operación](../docs/operacion.md)).

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
con `IEKG_WEB_PORT` en `.env`. Los pasos completos están en la guía de
operación ([`docs/operacion.md`](../docs/operacion.md)), sección «Desplegar con Docker».

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
  elegida en una frase y dice cómo leer el dibujo. Esa segunda frase se ve
  abierta la primera vez que aparece cada vista en la pestaña del navegador;
  después queda plegada tras «Cómo leerlo».
- **Capa y fuente.** Un hexágono con contorno es de CS2023 y un círculo relleno,
  de un sílabo; el color es la clase. Una línea, o el enlace «fuente» de la
  ficha, muestra qué documento afirma esa relación, con el enlace para abrirlo.
- **Teclado.** Tab recorre los puntos del mapa, las flechas pasan al punto más
  cercano, Enter pone un punto en foco y `+` trae sus conexiones.
  `Alt ←` vuelve al elemento anterior. Todo lo que el mapa dibuja está también
  como lista en la ficha de la derecha.
- **En el teléfono.** Hasta 900 px de ancho, el mapa ocupa la pantalla y la
  ficha va en una hoja que asoma abajo: se sube deslizándola o tocándola, y
  vuelve a bajar sola cuando el mapa cambia. Las preguntas son una franja que
  se desliza de lado. El mapa no se encoge hasta volver ilegibles los nombres:
  queda centrado en el foco y el resto se ve arrastrando o pellizcando; el
  botón de encuadre lo muestra entero. El panel del operador no se ofrece.
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

- `src/components/Sheet.svelte` y `src/lib/screen.svelte.js`: la hoja de la
  ficha en el teléfono y el ancho a partir del cual se usa.
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
[plan de pruebas](../casos-de-prueba/plan-de-pruebas-de-aceptacion-r6.md)
contra la API real, una vez con el puntero y otra solo con el teclado, y
compara lo que se ve con lo que responde la API. Es una comprobación previa:
las pruebas que cuentan para R6 se hacen con personas.

```powershell
npx playwright install chromium      # una vez
npm run walkthrough                  # contra http://localhost:5173
$env:INFOKNOWS_URL = "http://localhost"; npm run walkthrough   # contra el despliegue
node tests/walkthrough.mjs --shots ../docs/r6/capturas             # y guarda las capturas
```

`tests/operator-walkthrough.mjs` hace lo mismo con CA-11. Sube un documento, así
que **escribe en el grafo**: se corre sobre un grafo de ensayo, y después se
vuelve a cargar y a reaplicar. Contra una API en modo ensayo (`IEKG_REHEARSAL=1`)
no escribe nada: las corridas solo recorren sus estados.

### CA-11 con una ingesta completa y un proveedor simulado

Así se obtuvo la evidencia de `docs/r6/README.md` §4. Una corrida real de la
cadena final se vuelve a subir en un entorno de ensayo aparte, con otro Neo4j,
la API en el 8001 y una copia de los almacenes. La ingesta es la de
producción: Docling, validación, escritura y auditoría. Solo el modelo de
lenguaje es simulado: `scripts/replay_provider.py` responde con la salida que
esa corrida guardó. No se toca el despliegue local (`iekg-neo4j`, `var/`), no
se paga y no sale nada de la máquina.

Todo va en PowerShell, desde la raíz del repositorio. En el ejemplo se ensaya
la corrida 14 (1INF47); cualquier otra sirve, cambiando el número.

1. **Los almacenes de ensayo:** el estado justo antes de esa corrida, y su PDF
   aparte para subirlo.

   ```powershell
   uv run python scripts/prepare_replay_rehearsal.py --source var/medicion-r4 --run 14 --target var/ensayo-ca11
   ```

2. **Un Neo4j de ensayo** en otros puertos, sin volumen: se borra al detenerlo.

   ```powershell
   docker run -d --rm --name iekg-ca11-neo4j -p 127.0.0.1:17474:7474 -p 127.0.0.1:17687:7687 -e NEO4J_AUTH=neo4j/ensayo-ca11 neo4j:5.26.28-community
   ```

3. **Las variables del ensayo**, en cada terminal que se use en los pasos 4 y 6.
   Ganan sobre `.env`, así que la clave real del proveedor no se usa.

   ```powershell
   $env:NEO4J_URI = "bolt://127.0.0.1:17687"; $env:NEO4J_PASSWORD = "ensayo-ca11"
   $env:IEKG_OPERATIONAL_DB = "var/ensayo-ca11/operational.sqlite"
   $env:IEKG_FACTS_DIR = "var/ensayo-ca11/facts"; $env:IEKG_DOCUMENTS_DIR = "var/ensayo-ca11/documents"
   $env:IEKG_API_PORT = "8001"; $env:IEKG_OPERATOR_TOKEN = "ensayo-ca11"; $env:IEKG_REHEARSAL = ""
   $env:IEKG_LLM_MODEL = "gpt-6.1-sol"; $env:IEKG_LLM_API_KEY = "simulated"
   $env:IEKG_LLM_BASE_URL = "http://127.0.0.1:8766/v1"; $env:IEKG_LLM_MAX_RETRIES = "0"
   ```

4. **El grafo que vio esa corrida,** cuando el Neo4j de ensayo responda (unos
   30 s): los dos comandos deben salir con 0.

   ```powershell
   uv run iekg-build load; if ($LASTEXITCODE -eq 0) { uv run iekg-build reapply }
   ```

5. **El proveedor simulado,** en otra terminal, que se deja abierta:

   ```powershell
   uv run python scripts/replay_provider.py --operational-db var/medicion-r4/operational.sqlite --run 14
   ```

6. **La API de ensayo,** en la terminal del paso 3: `uv run iekg-api`.
7. **La web,** en otra terminal, en `web/`. Escucha en `localhost`, no en
   `127.0.0.1`.

   ```powershell
   npm run build; $env:IEKG_DEV_API = "http://127.0.0.1:8001"; npx vite preview --port 4174
   ```

8. **El recorrido,** en otra terminal, en `web/`. También se puede hacer a mano
   en `http://localhost:4174/?panel=operador`, con el token `ensayo-ca11`.

   ```powershell
   $env:INFOKNOWS_URL = "http://localhost:4174"; $env:INFOKNOWS_OPERATOR_TOKEN = "ensayo-ca11"
   node tests/operator-walkthrough.mjs ../var/ensayo-ca11/1INF47.pdf 1INF47 "Proyecto de Implementación de Software"
   ```

   Con `--shots ../docs/r6/capturas` guarda las capturas O1 a O6. La corrida
   tarda un par de minutos, sobre todo por Docling, y debe terminar
   «Terminada», con 15 reglas sin violaciones y sin descartes.

9. **Desmontar:** `docker stop iekg-ca11-neo4j`, cerrar las terminales y
   borrar `var/ensayo-ca11/`. Para repetir el ensayo, la carpeta tiene que
   estar vacía o no existir.

Los ejemplos de los dos recorridos son los del plan, que dependen del grafo
cargado: con el grafo final hay que fijarlos de nuevo.
