# **Catálogo de requisitos funcionales**

**Sistema:** KMS basado en grafo de conocimiento para Ingeniería Informática (PUCP) **Alcance:** R3–R6 · **Versión:** 1.3 · **Fecha:** octubre 2026

Documento interno: guía los requisitos del módulo y su única fuente de verdad es este repositorio. No se replica en los documentos oficiales.

---

## **1\. Propósito y limitación declarada**

Este catálogo delimita qué funcionalidad ofrece el sistema. No procede de una elicitación con usuarios finales; se deriva retroactivamente de tres fuentes ya producidas en la investigación. Esa limitación se declara aquí y no se disimula: el sistema es un artefacto de diseño.

El catálogo se produce **junto al diseño arquitectónico, no antes de él**. Para que esa concurrencia no se confunda con circularidad, cada requisito se registra bajo tres relaciones distintas:

* **Origen** — qué hace que el requisito exista. Solo preguntas de competencia, escenarios de calidad, el ítem 16 de la encuesta o el protocolo de los casos de prueba de la ingesta.  
* **Restricción** — qué decisión de diseño previa acota su solución sin originarlo.  
* **Derivado (D)** — requisito que existe únicamente como consecuencia de una decisión arquitectónica. Se marca como tal; no se presenta como elicitado.

Un requisito sin origen no pertenece a este catálogo. Los pasos internos de un componente tampoco: pertenecen al nivel 3 del C4.

### **Fuentes de derivación**

| Código | Fuente | Ubicación |
| ----- | ----- | ----- |
| **PC1–PC7** | Preguntas de competencia de la ontología | R1, Paso 1 de Ontology Development 101 |
| **AC-01–AC-05** | Escenarios de calidad (Bass et al., ISO/IEC 25010\) | R3, Fase 1 |
| **E16** | Ítem 16 de la encuesta de orientación del aprendizaje (N=154) | Anexo D |
| **CP-01–CP-16** | Protocolo de los casos de prueba de la ingesta | Tesis, §5.2.5 |
| **DD-xx / ADR-xxx** | Decisiones de diseño validadas y decisiones arquitectónicas | R1 y R3 |

### **Frecuencias del ítem E16 (N=154, opción múltiple)**

| Funcionalidad valorada | % |
| ----- | ----- |
| Ver qué conceptos previos necesito antes de abordar un tema | 83.1 |
| Encontrar recursos de estudio asociados a un concepto específico | 72.1 |
| Entender cómo se conectan distintas áreas de la carrera | 61.0 |
| Orientarme sobre qué cursos electivos llevar según mis metas | 53.2 |
| Descubrir temas que no sabía que existían dentro de mi carrera | 52.6 |

Los ítems de valoración de la propuesta (15) no se emplean como evidencia del problema por deseabilidad social; el ítem 16 se emplea aquí como insumo de priorización de funcionalidad, no como validación.

---

## **2\. Actores y sistemas externos**

| Actor | Descripción | Traza |
| ----- | ----- | ----- |
| **Estudiante** | Consulta y navega el grafo. No escribe. | AC-03, AC-05, PC1–PC7 |
| **Operador del grafo** | Sube documentos declarando su tipo y su curso, observa el resultado de cada ingesta y consulta el reporte de auditoría. Encarnado por el autor durante la tesis. | AC-01, AC-02, AC-04 |
| **Proveedor de modelo de lenguaje** (externo) | Servicio de extracción estructurada consumido por el pipeline. No escribe en la base. | ADR-003 |

Docling es librería del pipeline, no sistema externo. No aparece como actor.

El desarrollador tampoco es actor: ejecuta los procesos de construcción (sección 4), no usa el sistema construido.

---

## **3\. Requisitos del módulo del grafo y del pipeline (R3–R4)**

| ID | Requisito | Origen | Restricción |
| ----- | ----- | ----- | ----- |
| RF-02 **(D)** | Aceptar un documento académico con su tipo de recurso y, cuando el tipo lo implique, el código y nombre de su curso, y ejecutar la ingesta como trabajo asíncrono, devolviendo un identificador de ejecución. | PC2, PC5 | ADR-007, ADR-009 |
| RF-03 **(D)** | Consultar el estado y el resultado de una ejecución de ingesta por su identificador. | AC-02 | ADR-007, ADR-010 |
| RF-04 | Validar todo hecho candidato contra el modelo ontológico antes de escribir. Ningún hecho inválido se persiste. | AC-01 | ADR-003, ADR-005 |
| RF-05 | Registrar, por cada ejecución rechazada, cada violación con la regla que infringe y el lote candidato completo. Los descartes no reingresan al grafo. | AC-01 (medida), AC-02 | ADR-010 |
| RF-06 | Enlazar las entidades extraídas a los nodos ya existentes en el grafo —de cualquiera de las dos capas— cuando exista correspondencia, evitando duplicados. La escritura no crea ni modifica nodos de la capa de referencia. | AC-01 | DD-02, ADR-011 |
| RF-07 | Registrar la procedencia de cada instancia y de cada arista institucional escrita. | AC-03 | DD-09 |
| RF-08 | Persistir en el almacén de hechos los hechos institucionales escritos en el grafo, de modo que puedan reaplicarse sin volver a invocar el modelo de lenguaje. | AC-04 | ADR-004, ADR-012 |
| RF-25 | Fijar en la configuración el modelo de lenguaje por su versión exacta, no por un alias que el proveedor pueda mover, junto con sus parámetros de generación, y registrar con cada ejecución esos valores y la versión del prompt. | CP-01–CP-13 | — |
| RF-09 | Ejecutar el conjunto de consultas de integridad declaradas al cierre de la carga, de cada ingesta y de la reaplicación, y emitir un reporte por regla de integridad y del módulo en una sola ejecución. | AC-02 | DD-10, ADR-005 |

### **Consultas expuestas por la API**

| ID | Requisito | Origen | Restricción |
| ----- | ----- | ----- | ----- |
| RF-11 | Devolver los conceptos prerrequisito de un concepto dado, con cierre transitivo y profundidad acotada. | PC1, E16 (83.1%) | DD-07 |
| RF-12 | Devolver los conceptos que un curso enseña y los que asume, y derivar el prerrequisito conceptual entre cursos sin almacenarlo. | PC2 | DD-07 |
| RF-13 | Devolver la ubicación estructural de un elemento (tema, unidad, área) y su composición descendente. | PC3, PC4, E16 (61.0%) | DD-06 |
| RF-14 | Devolver los recursos de aprendizaje asociados a un elemento, agregando por roll-up sobre sus partes, con su localizador resuelto. | PC5, E16 (72.1%) | DD-07 |
| RF-15 | Devolver la ruta de aprendizaje hacia un elemento objetivo, elevando el prerrequisito conceptual al grano solicitado. | PC6 | DD-07 |
| RF-16 | Devolver el cierre de especialización de un concepto: de qué concepto es tipo y qué conceptos son tipos de él. | PC7 | DD-08 |
| RF-17 | Devolver, junto a toda afirmación institucional, la referencia al documento del que se derivó. | AC-03 | DD-09 |
| RF-18 | Buscar elementos del grafo por nombre legible, con coincidencia parcial. | PC1–PC7, como precondición de RF-11 a RF-17 | — |
| RF-24 | Servir el documento de un recurso de aprendizaje institucional en la dirección que registra su localizador | PC5, E16 (72.1%) | RI-10, ADR-009 |

---

## **4\. Procesos de construcción del grafo**

| ID | Requisito | Origen | Restricción |
| ----- | ----- | ----- | ----- |
| RF-01 | Cargar la capa de referencia curada en el grafo a partir del TTL del backbone, sobre una base vacía, de forma reproducible. | AC-04 | DD-02, ADR-004 |
| RF-10 **(D)** | Reaplicar, como paso aparte y después de una carga, los hechos guardados de cada ejecución, en su orden original y sin invocar al modelo de lenguaje. | AC-04 | ADR-004, ADR-012 |

**Alcance de RF-10.** La carga seguida de la reaplicación cubre cambios en la capa institucional, en el código de proyección y en los constructos añadidos solo al grafo, así como correcciones de etiqueta o descripción en la capa de referencia. **No cubre** cambios de identificador, fusión o eliminación de unidades de la capa de referencia, ni cambios en la T-Box: esos casos rompen los enlaces existentes y se atienden por migración planificada, fuera del alcance de este resultado. La medida de AC-04 se interpreta dentro de esta frontera.

---

## **5\. Requisitos del mecanismo de navegación (R5–R6)**

Enunciados en términos de capacidad, no de interacción. Los marcados como **provisional** quedan sujetos al diseño de flujos e interfaz de R5; los marcados como **firme** son compromisos ya adquiridos y no admiten revisión por criterio de producto.

| ID | Requisito | Origen | Restricción | Estado |
| ----- | ----- | ----- | ----- | ----- |
| RF-19 | Permitir al estudiante localizar un punto de entrada al grafo y explorarlo de forma visual e interactiva, recorriendo las relaciones desde un elemento hacia sus vecinos. | E16 (61.0%, 52.6%), PC1–PC7 | — | provisional |
| RF-20 | Presentar, para el elemento en foco, sus prerrequisitos, su ubicación estructural y sus recursos asociados con enlace de acceso. | PC1, PC3, PC5, PC6, E16 (83.1%, 72.1%) | — | provisional |
| RF-21 | Exponer al estudiante el documento del que se derivó cada afirmación institucional presentada. | AC-03 | DD-09 | **firme** |
| RF-22 | Distinguir de forma perceptible los elementos de la capa de referencia de los de la capa institucional. | AC-03 | DD-02 | **firme** |
| RF-23 **(D)** | Ofrecer al operador una vista para cargar un documento, seguir el estado de su ingesta, revisar los descartes de esa ejecución y consultar su reporte de auditoría. | AC-02 | ADR-007 | **firme** |

El alcance de RF-23 se agota en esas cuatro capacidades. La prueba de aceptación de R6 evalúa exploración y acceso a recursos por parte del estudiante; la vista del operador no forma parte de ella.

---

## **6\. Fuera de alcance**

Lo siguiente se excluye de forma explícita. La exclusión es parte del requisito.

| Excluido | Motivo |
| :---- | ----- |
| Verificación de integridad bajo demanda | La auditoría corre al cierre de la carga, de cada ingesta y de la reaplicación; el último reporte describe el estado vigente del grafo |
| Curación experta con flujo de aprobación, rechazo, comparación de versiones o aprobación por lotes | Fuera del alcance de la tesis; declarado como trabajo futuro |
| Reingreso al grafo de hechos descartados | RF-05; el registro es instrumento de medida, no cola de trabajo |
| Edición manual de nodos o aristas desde la interfaz | Toda escritura pasa por el pipeline |
| Modificación de la capa de referencia por vía automatizada | DD-02 |
| Migración del grafo ante cambio de identificadores de la capa de referencia o de la T-Box | Ver alcance de RF-10; se atiende por migración planificada |
| Cuentas de usuario, roles múltiples y gestión de permisos | Prototipo monousuario; autenticación por token fijo para el operador |
| Recomendación de cursos electivos según metas profesionales | Requiere modelado del estudiante, excluido por DD-03. Parcialmente atendido por RF-12 y RF-15, que exponen la estructura de prerrequisitos sin personalizarla |
| Modelado de competencias (K-S-D-T de CC2020) | DD-03 |
| Ingesta de fuentes ajenas al material académico PUCP del conjunto piloto | Alcance de R4: 13 sílabos del eje CS+SE |
| Ejecuciones de ingesta concurrentes | Escritor único del grafo (ADR-007) |
| Más de un tipo de recurso y filtrado de recursos por tipo | El modelo los admite (R1); el piloto puebla solo el tipo Sílabo |

---

## **7\. Trazabilidad inversa por origen**

| Origen | Requisitos que lo atienden |
| ----- | ----- |
| PC1 | RF-11, RF-18, RF-19, RF-20 |
| PC2 | RF-02, RF-12, RF-18, RF-19 |
| PC3 | RF-13, RF-18, RF-19, RF-20 |
| PC4 | RF-13, RF-18, RF-19 |
| PC5 | RF-02, RF-14, RF-18, RF-19, RF-20, RF-24 |
| PC6 | RF-15, RF-18, RF-19, RF-20 |
| PC7 | RF-16, RF-18, RF-19 |
| AC-01 | RF-04, RF-05, RF-06 |
| AC-02 | RF-03, RF-05, RF-09, RF-23 |
| AC-03 | RF-07, RF-17, RF-21, RF-22 |
| AC-04 | RF-01, RF-08, RF-10 |
| AC-05 | RF-12 a RF-16 (patrones medidos) |
| E16 | RF-11, RF-13, RF-14, RF-19, RF-20, RF-24 |
| CP-01–CP-13 | RF-25 |

AC-05 no genera requisitos propios: califica el desempeño de los ya declarados. Los requisitos marcados **(D)** —RF-02, RF-03, RF-10, RF-23— existen por decisión arquitectónica y no por elicitación.

---

## **8\. Pendientes que el protocolo de medición deja a la ingesta**

No son requisitos todavía: son lo que el protocolo de la tesis (§5.2.5 y Tabla 15) da por supuesto y nadie ha decidido cómo se cumple. Cada uno se cierra en el ADR o en el requisito que lo resuelva.

| Pendiente | Lo que exige el protocolo | Qué falta decidir |
| ----- | ----- | ----- |
| Medición de las relaciones | CP-15 juzga todas las aristas de partonomía de tema a unidad; CP-16, una muestra aleatoria con semilla fija de 30 aristas de prerrequisito, de especialización y de concepto requerido, o todas si hay menos. Ambos, sobre el grafo final. | Cómo se obtienen esas aristas de forma reproducible y dónde vive ese procedimiento. |
| Medición de AC-05 | Los cinco patrones desde cada uno de sus nodos de partida, diez ejecuciones tras una pasada de calentamiento, la ejecución en frío aparte, y el tamaño del grafo y el entorno junto a la medición. | Lo mismo: cómo se ejecuta de forma reproducible y dónde vive. |
| Concepto requerido sin tema | CP-16 juzga `REQUIRES_CONCEPT`: un concepto que el curso necesita y no enseña. RI-08 exige que todo concepto tenga un tema padre. | De dónde sale ese tema cuando el sílabo no enseña el concepto. Es una pregunta para el ADR del extractor. |

Un tercero no queda pendiente: la precisión de los intentos rechazados sale del lote candidato que guarda RF-05. Ante una salida no conforme (EX-01) puede no haber lote legible, y la tesis lo acepta («cuando ese lote es legible»).
