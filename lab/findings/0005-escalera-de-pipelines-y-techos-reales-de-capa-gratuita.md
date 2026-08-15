# 0005 — La escalera de pipelines, y los techos reales de la capa gratuita

- **Fecha:** 2026-08-14
- **Sustentabilidad:** alta para el diseño de la escalera y para las mediciones
  de comportamiento de las librerías (reproducibles con
  `lab/scripts/run_pipeline.py` y `uv run pytest tests/`). **Gris, y fechada, para
  los cupos de los proveedores**: son política comercial, cambian sin aviso y no
  deben citarse en la tesis como propiedad del método, solo como condición del
  entorno en que se corrió. Los números de la corrida de humo **no son
  resultados**: el texto es inventado y hay un solo documento.
- **Afecta a:** R4 (pipeline de ingesta), la matriz de comparación de O2, el
  catálogo de modelos y el diseño del enlace de entidades.

## Pregunta

`findings/0004` dejó dicho que no había bloqueo técnico para construir los
cuatro pipelines. Al construirlos: ¿se sostienen en la capa gratuita, y las
decisiones que quedaron escritas —fallback automático, umbral coseno, Docling—
resisten el contacto con la ejecución?

Tres de ellas no.

## Resultado 0 — Las tres correcciones que cambian el plan

| Lo escrito | Lo medido |
|---|---|
| `gemini-3.7-flash`: "15 RPM / 1500 RPD", el techo más alto disponible | **20 peticiones por día y por modelo** |
| "Fallback automático a `gemini-3.6-flash` ante 503" | El fallback **nunca se disparaba** |
| "umbral coseno" como regla de decisión del enlace | Un umbral absoluto **no puede separar** el acierto del casi-acierto |

Las tres estaban en el catálogo o en el handoff, ninguna era observable leyendo
el código, y las tres se rompen en silencio: no fallan, dan un resultado
distinto del que uno cree estar midiendo.

## Resultado 1 — La capa gratuita de Gemini da 20 peticiones al día, no 1500

El error 429 lo dice con nombre propio:

```
Quota exceeded for metric: generate_content_free_tier_requests, limit: 20,
model: gemini-3.7-flash
quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier, quotaValue: "20"
```

Es **por día, por proyecto y por modelo**. El catálogo decía "15 RPM / 1500 RPD"
y sobre esa cifra descansaba la elección de `workhorse` como modelo de
iteración: *"the highest request ceiling of anything available, so iteration
lives here"*. Es falso.

La consecuencia es aritmética. P2 y P3 hacen **1 + N llamadas** por sílabo, una
por tema: sobre el texto de prueba, 7 llamadas. Con 20 al día caben **dos
corridas y media**, contando que el probe de capacidades ya gasta cinco.
Sostener 2 modelos × 4 pipelines × 3 sílabos en `workhorse` es imposible.

Groq, en cambio, aguantó las corridas completas de P2 y P3 sin tocar techo. **La
iteración se muda a Groq**; Gemini queda para la corrida final medida, que es
exactamente el papel que el catálogo asignaba al *tier* `final`.

## Resultado 2 — El `fallback_to` estaba declarado y era inerte

Con `gemini-3.7-flash` agotado y `gemini-3.6-flash` respondiendo con normalidad,
la corrida moría. No degradaba: moría.

La causa es una composición de dos decisiones correctas por separado. El
transporte con reintentos convierte un 429 en `httpx.HTTPStatusError`, que es lo
que la política de tenacity vigila. Pero `FallbackModel` conmuta, por defecto,
solo ante `ModelAPIError`. Un `HTTPStatusError` no lo es, así que atraviesa el
`FallbackModel` sin activarlo y sale por arriba.

```python
FallbackModel(model, alt, fallback_on=(ModelAPIError, httpx.HTTPStatusError))
```

Verificado después del arreglo: pedir `workhorse` con 3.7 agotado devuelve
respuesta de `gemini-3.6-flash`.

**Y eso abre un problema de validez, no de ingeniería.** Un fallback que
funciona conmuta de modelo sin decirlo, y una corrida atribuida al modelo
equivocado es peor que una corrida fallida. Ahora cada llamada registra **qué
modelo contestó**, no cuál se pidió; el manifiesto lleva `answered_by` y
`fallback_fired`, y el runner lo grita por consola. Es la aplicación literal de
lo que el handoff ya pedía —"un run que aterriza ahí se reporta, nunca se acepta
en silencio"— que hasta hoy dependía de que alguien se acordara.

## Resultado 3 — El coseno no separa lo que hay que separar

Medido con `gemini-embedding-001` y tipos de tarea asimétricos
(`RETRIEVAL_QUERY` para la mención, `RETRIEVAL_DOCUMENT` para la etiqueta del
backbone):

| Consulta: "Modelado de datos: modelo entidad-relacion" | Coseno |
|---|---|
| `Data Modeling` — correcta | **0,733** |
| `Relational Databases` — casi-acierto, misma área | **0,708** |
| `Quantum Architectures` — sin relación | 0,560 |

El acierto le saca **0,025** al distractor plausible y **0,17** al irrelevante.
Cualquier umbral que acepte 0,733 acepta también 0,708: **un umbral absoluto
distingue lo relacionado de lo ajeno, no lo correcto de lo casi-correcto**, que
es justo la decisión que importa.

Peor: con `SEMANTIC_SIMILARITY` en vez de los tipos asimétricos, los valores se
comprimen contra 1 y un par sin relación queda en 0,82. El "umbral 0,72" que
figuraba como plan habría aceptado absolutamente todo.

Por eso la regla de decisión implementada es **umbral más margen sobre el
segundo candidato**, y **abstención** cuando el margen no se alcanza. La
abstención no es un fallo del enlace: es la cola de revisión humana que el
diseño ya contemplaba, y ahora se produce sola en vez de definirse a mano.
`linking.json` guarda los *k* candidatos con su puntaje, así que el umbral se
puede volver a barrer sin gastar una sola llamada más.

## Resultado 4 — `gemini-embedding-2` devuelve un solo vector por lote

Es el hallazgo más peligroso del día, porque no levanta ningún error.

| Textos enviados | Embeddings devueltos |
|---|---|
| 1 | 1 |
| 2 | **1** |
| 3 | **1** |

Un `zip(textos, respuesta.embeddings)` —el patrón obvio— habría emparejado el
primer vector con la primera etiqueta y **descartado el resto sin avisar**. El
índice del backbone habría quedado con 1 entrada creyendo tener 162, y el enlace
habría producido resultados plausibles y falsos.

El catálogo se queda en `gemini-embedding-001`, que es más antiguo, y el
interpretador **comprueba el largo de cada lote contra el largo de la entrada**
antes de aparearlos. Un conteo que cuadra no es una garantía; que no cuadre sí
es una alarma.

## Resultado 5 — El cupo de embeddings cuenta textos, no llamadas

```
Quota exceeded for metric: embed_content_free_tier_requests, limit: 100
quotaId: EmbedContentRequestsPerMinutePerUser...
```

Agrupar 162 etiquetas en 11 lotes de 16 **no las convierte en 11 peticiones**:
siguen contando 162 contra un techo de 100 por minuto. Agrupar no compra
holgura; hay que **espaciar**. Con el ritmo derivado del cupo declarado en el
catálogo, construir el índice tarda **116 s**, se cachea en disco y no se vuelve
a pagar.

## Resultado 6 — Docling no arranca en Windows sin compilador de C++

```
InvalidCxxCompiler: Compiler: cl is not found
torch._inductor.exc.InductorError
```

El modelo de layout corre bajo `torch.compile`, cuyo backend *inductor* invoca a
`cl.exe` de MSVC. Sin Visual Studio Build Tools, la conversión **no se degrada:
falla**. Con `TORCHDYNAMO_DISABLE=1` cae a ejecución *eager* y funciona: el
sílabo de 4 páginas convierte en **15 s**, con 2 tablas detectadas y 9.137
caracteres. La variable se fija desde el código, no desde la consola, porque una
instrucción de entorno que hay que recordar es una trampa esperando.

Nota de método: esa conversión se ejecutó **sin imprimir el contenido**, solo su
estructura, porque la anotación de referencia del sílabo todavía no está sellada.

## Resultado 7 — La escalera corre de punta a punta

Corrida de humo sobre un **texto inventado** de redes, nunca el sílabo real.
Cifras de funcionamiento, no resultados:

| | Modelo | Temas | Conceptos | Enlazados | Conformidad |
|---|---|---|---|---|---|
| P0 sin esquema | gemini-3.7-flash | 27 | **0** | — | **0,509** |
| P1 una pasada | gemini-3.7-flash | 6 | 21 | 1/6 | 0,935 |
| P2 multi-etapa | gpt-oss-120b | 6 | 21 | 0/6 | 0,921 |
| P3 + recuperación | gpt-oss-120b | 6 | 22 | **4/6** + 2 a revisión | **0,976** |

Lo que ya se ve, con un solo documento y sin poder concluir nada:

- **P0 no produce partonomía.** Devolvió 27 elementos planos y **cero**
  conceptos anidados: sin esquema, el modelo no distingue Tema de Concepto. La
  conformidad de 0,509 no mide alucinación, mide que la mitad de lo extraído no
  encaja en ninguna clase del grafo. Es el número que faltaba para responder
  "cuánto vale restringir".
- **El enlace léxico es tan malo como debía ser**: 1/6 y 0/6. Es el control, y
  su trabajo es dar un piso, no funcionar.
- **La recuperación por embeddings sube a 4/6 y abstiene en 2.** Los seis
  candidatos principales cayeron dentro del área correcta; los dos casos
  dudosos fueron precisamente aquellos cuyo margen sobre el segundo candidato
  era de 0,02.

## Qué se decide con esto

1. **La iteración se muda a Groq.** `workhorse` (Gemini) queda reservado para la
   corrida final medida. El catálogo mantiene el texto de límites, corregido.
2. **Ninguna corrida se atribuye a un modelo sin `answered_by`.** El manifiesto
   lo registra y el runner lo denuncia.
3. **El enlace decide por umbral y margen, con abstención explícita.** Los
   candidatos se guardan íntegros para poder barrer el umbral a posteriori.
4. **La compuerta ciega es código.** `run_pipeline.py` se niega a correr sobre
   un documento sin anotación de referencia sellada. `--ungated` existe, y queda
   escrito en el manifiesto.
5. **Los pipelines emiten, no cargan.** Cada corrida deja texto, prompts,
   extracción, decisiones de enlace, violaciones y el Cypher que *se escribiría*.
   Cargar es un paso aparte, después de leer.

## Lo que sigue abierto

- **La etiqueta de un Tema sale con su cola descriptiva.** De una fila de
  cronograma, el modelo extrae `"Layer model: encapsulation, protocols, data
  units"` como una sola etiqueta, y es fiel a la fuente. Decidir si eso se
  normaliza —y si normalizarlo es tarea del prompt o de código determinista—
  afecta directamente al enlace, porque una etiqueta larga desplaza el coseno.
- **`scope_iris`**: si dos sílabos que enseñan "Normalization" deben fundirse en
  un `Concept` o quedar separados. Está como opción, sin decidir, para poder
  medirlo.
- **Los prerrequisitos siguen fuera** de esta comparación, por decisión previa.

## Trampas encontradas

- **Un fallback declarado no es un fallback probado.** Estaba escrito en el
  catálogo, documentado en un finding y era inerte. Solo se descubrió al agotar
  la cuota de verdad.
- **Agrupar peticiones no reduce el consumo de cupo** si el proveedor cuenta
  elementos y no llamadas.
- **Un SDK puede devolver menos de lo que se le pidió sin error.** Comprobar el
  largo de la respuesta contra el de la entrada antes de aparearlas.
- **Google manda el tiempo de espera en el cuerpo, no en `Retry-After`.** Una
  política de reintentos que solo mire la cabecera espera de menos: hacían falta
  47 s y esperaba 30.
- **`torch.compile` necesita un compilador de C++ instalado.** En Windows sin
  MSVC no hay aviso, hay `ConversionError`.
