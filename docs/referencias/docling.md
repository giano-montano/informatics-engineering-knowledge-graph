# Docling: lo que importa para la implementación

**Verificado:** 2026-11-12, contra el código y las fuentes externas listadas al
final. Antes de usar una cifra o una licencia de terceros en la tesis, volver a
comprobarla.

Nota de referencia interna. No es un ADR ni un entregable.

## Qué es y cómo se usa aquí

Docling (IBM Research, licencia MIT) convierte documentos (PDF, imágenes,
formatos de Office, HTML) a Markdown, JSON o HTML. Para el PDF usa dos modelos
propios: uno de análisis de diseño, que distingue título, párrafo, lista y
tabla, y otro (TableFormer) que reconstruye la estructura de las tablas. Corre
localmente, en hardware común.

En `dev` lo usa solo `read_document` (`src/iekg/ingestion/extractor.py`):

- `DocumentConverter` con `PdfPipelineOptions(do_ocr=False)`. Los sílabos son
  PDF digitales y ya traen el texto, así que el OCR no hace falta.
- La salida es `converter.convert(path).document.export_to_markdown()`. El
  Markdown conserva los encabezados (`##`) y las listas (`-`).
- `TORCHDYNAMO_DISABLE=1` antes de importar. En Windows, `torch.compile` invoca
  `cl.exe` (MSVC), y sin él Docling no arranca. Se midió en el laboratorio
  (`docs/repositorio/traspaso-del-laboratorio.md` §2).
- Versión fijada: `docling>=2.135,<3` en `pyproject.toml`; instalada, 2.135.0.

Es una librería del extractor, no un sistema externo. No aparece como actor en
el C4 (`docs/requisitos-funcionales-de-referencia.md`). En el modelo figura
como tecnología del worker (`docs/architecture/model.c4`).

## Por qué importa la estructura

La regla de extracción depende de cómo está organizado el sílabo: un tema es
un encabezado que agrupa ítems, y un concepto es cada ítem (Anexo L y la
sección «Topics» de `INSTRUCTIONS`). Un extractor de texto plano entrega
encabezados e ítems con la misma forma, una línea cada uno, y deja la
jerarquía a la inferencia del modelo. El Markdown de Docling la marca.

En el laboratorio se midió algo relacionado, aunque no lo mismo: solo cambiar
cómo se le pide al modelo que identifique un tema movió la precisión exacta de
0,00 a 0,38 en un documento (traspaso §3.3). Eso muestra que la estructura de
encabezados es la materia prima de la extracción. **No compara Docling contra
otra herramienta.**

## Lo que no está hecho

- **No hay comparación medida** de Docling contra otra herramienta sobre los
  sílabos. La elección es argumentada: estructura, ejecución local y licencia.
- **Ni la tesis ni ningún ADR justifican Docling.** ADR-003 lo nombra como paso
  del pipeline, sin alternativas.

## Alternativas y por qué no

| Alternativa | Qué ofrece | Por qué no | Fuente |
|---|---|---|---|
| PyMuPDF, pdfplumber, pypdf | Texto rápido y liviano | Pierden la jerarquía. PyMuPDF es AGPL | Benchmark de extractores: preprint, **gris**. Licencia: ver *opendataloader-bench*, **gris** |
| Marker | PDF → Markdown de buena calidad; primero en algún benchmark de GitHub | Licencia GPL. Sin ventaja que el piloto necesite | *opendataloader-bench*, **gris** |
| Unstructured | Partición en elementos tipados | El modo de alta calidad es pesado; su salida son elementos, no Markdown jerárquico | Benchmarks de GitHub y blogs, **gris** |
| Servicios en la nube (LlamaParse y similares) | Calidad sin instalar modelos | Mandan el documento a un tercero y suman otro proveedor con su cuota y sus fallos (traspaso §3) | Razonamiento propio |
| PDF directo a un modelo multimodal | Sin conversión | No queda texto intermedio que se pueda inspeccionar, ata la tubería al proveedor y cuesta más tokens | Razonamiento propio |

No se encontró un estudio revisado por pares que compare Docling, Marker,
PyMuPDF y Unstructured juntos. El preprint comparativo más cercano
(arXiv 2410.09871) no incluye ni Docling ni Marker.

## Lo que se cede

- **Peso:** PyTorch y los modelos se descargan la primera vez. Es más lento que
  leer texto plano.
- **Fricción en Windows:** lo de MSVC, ya resuelto con la variable de entorno.
- **Dependencia del diseño visual:** un encabezado escrito como texto en
  negrita puede no reconocerse como título. El prompt lo cubre en parte con la
  regla de los encabezados genéricos.

## Fuentes

- Livathinos, N., Auer, C., et al. (2025). *Docling: An Efficient Open-Source
  Toolkit for AI-driven Document Conversion*. AAAI 2025, Workshop on
  Open-Source AI for Mainstream Use. arXiv:2501.17887.
  <https://arxiv.org/abs/2501.17887>. **Citable con reserva:** es un taller,
  no la conferencia principal. Página de IBM Research:
  <https://research.ibm.com/publications/docling-an-efficient-open-source-toolkit-for-ai-driven-document-conversion>.
- *Docling Technical Report*, arXiv:2408.09869. Preprint: **gris**.
- Adhikari, N. S., et al. Comparativa de extractores de PDF, arXiv:2410.09871.
  Preprint: **gris**. No incluye Docling ni Marker.
- *opendataloader-bench*:
  <https://github.com/opendataloader-project/opendataloader-bench>.
  Repositorio: **gris**.
- *pdf-parser-benchmark*:
  <https://github.com/applied-artificial-intelligence/pdf-parser-benchmark>.
  Repositorio: **gris**.
