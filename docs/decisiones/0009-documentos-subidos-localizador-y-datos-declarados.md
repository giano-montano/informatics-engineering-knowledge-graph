# ADR-009: Documentos subidos, localizador y datos declarados por el operador

**Estado:** Aceptada (enmendada 2026-10)
**Fecha:** 2026-10
**Atributos:** AC-03 (principal), AC-01

## Contexto

Todo recurso de aprendizaje necesita un localizador que el estudiante pueda abrir (RI-10 y la regla del módulo sobre localizadores). Los sílabos subidos no tienen una dirección pública propia. Además, cada documento trae datos que no conviene pedirle al modelo de lenguaje: de qué tipo es y a qué curso pertenece.

## Decisión

- **Todo recurso de aprendizaje institucional es un documento subido.** La API acuña su clave al recibirlo, guarda el archivo con esa clave en el almacén de documentos y lo sirve en `/recursos/{clave}`. Esa URL es su localizador. CS2023 conserva su URL pública.
- **El operador declara al subir el tipo de recurso y, si el tipo lo implica, el código del curso.** Ninguno de los dos pasa por el modelo de lenguaje.
- La clave del tipo de recurso y la del curso se **derivan de forma determinista** de su nombre y de su código, de modo que el MERGE es idempotente. El código de curso se guarda como propiedad del nodo curso.
- Cada sílabo afirma solo su propio curso: lo crea si no existe y, si existe, se fusiona como cualquier hecho (ADR-006). Los prerrequisitos formales entre cursos no se extraen.

## Alternativas consideradas

| Alternativa | Motivo del descarte |
|---|---|
| Bucket externo para los documentos | Dependencia, credenciales y costo en una máquina virtual de la especialidad. |
| Relajar RI-10 a una URI interna | Una URI que solo entiende el sistema no le sirve al estudiante y obligaría a un segundo campo. |
| Inferir el tipo de recurso de la extensión del archivo | El tipo es semántico («slides de clase»), no técnico («pptx»). |
| Clave del curso acuñada al azar, con enlace por etiqueta | Expone a duplicados el caso de identidad más simple del sistema. |
| Código del curso extraído por el modelo | Un error de lectura crearía otro curso, en silencio. |
| Archivo semilla para los tipos de recurso | El nodo nace por MERGE en la ingesta y la reaplicación lo reproduce. |

## Consecuencias

- **Los localizadores llevan el host escrito.** Cambiar de host exige migrar datos. El almacén de hechos no se reutiliza en otro host: en un host nuevo se vuelve a ingestar.
- El inventario de recursos que ve el estudiante es exactamente lo ingestado: en el piloto, 13 sílabos. Se declara como limitación.
- Un error de tipeo del operador en el código del curso crea otro curso. El error es visible en la corrida, pero no hay forma de retirar una corrida ya escrita —tampoco la de un documento subido por error—, y la reaplicación la reproduce. Se declara como limitación.

## Enmienda (2026-10)

- **Nombre del curso.** Junto con el código, el operador declara el nombre del curso, que se guarda como su etiqueta preferida en español. Tampoco pasa por el modelo de lenguaje: así la extracción se limita al contenido del documento. El nombre no interviene en la clave, de modo que un error de tipeo en él no crea otro curso. Como la ingesta no modifica nodos existentes (ADR-006), el curso conserva el nombre declarado en su primer documento.
