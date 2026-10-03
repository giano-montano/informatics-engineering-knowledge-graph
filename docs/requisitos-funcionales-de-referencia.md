# **Catálogo de requisitos funcionales**

**Sistema:** KMS basado en grafo de conocimiento para Ingeniería Informática (PUCP) **Alcance:** R3–R6 · **Versión:** 1.2 · **Fecha:** octubre 2026

---

## **1\. Propósito y limitación declarada**

Este catálogo delimita qué funcionalidad ofrece el sistema. No procede de una elicitación con usuarios finales; se deriva retroactivamente de tres fuentes ya producidas en la investigación. Esa limitación se declara aquí y no se disimula: el sistema es un artefacto de diseño.

El catálogo se produce **junto al diseño arquitectónico, no antes de él**. Para que esa concurrencia no se confunda con circularidad, cada requisito se registra bajo tres relaciones distintas:

* **Origen** — qué hace que el requisito exista. Solo preguntas de competencia, escenarios de calidad o el ítem 16 de la encuesta.  
* **Restricción** — qué decisión de diseño previa acota su solución sin originarlo.  
* **Derivado (D)** — requisito que existe únicamente como consecuencia de una decisión arquitectónica. Se marca como tal; no se presenta como elicitado.

Un requisito sin origen no pertenece a este catálogo. Los pasos internos de un componente tampoco: pertenecen al nivel 3 del C4.

### **Fuentes de derivación**

| Código | Fuente | Ubicación |
| ----- | ----- | ----- |
| **PC1–PC7** | Preguntas de competencia de la ontología | R1, Paso 1 de Ontology Development 101 |
| **AC-001–AC-005** | Escenarios de calidad (Bass et al., ISO/IEC 25010\) | R3, Fase 1 |
| **E16** | Ítem 16 de la encuesta de orientación del aprendizaje (N=154) | Anexo D |
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
| **Estudiante** | Consulta y navega el grafo. No escribe. | AC-003, AC-005, PC1–PC7 |
| **Operador del grafo** | Sube documentos declarando su tipo y su curso, observa el resultado de cada ingesta y consulta el reporte de auditoría. Encarnado por el autor durante la tesis. | AC-001, AC-002, AC-004 |
| **Proveedor de modelo de lenguaje** (externo) | Servicio de extracción estructurada consumido por el pipeline. No escribe en la base. | ADR-003 |

Docling es librería del pipeline, no sistema externo. No aparece como actor.

El desarrollador tampoco es actor: ejecuta los procesos de construcción (sección 4), no usa el sistema construido.

---

## **3\. Requisitos del módulo del grafo y del pipeline (R3–R4)**

| ID | Requisito | Origen | Restricción |
| ----- | ----- | ----- | ----- |
| RF-02 **(D)** | Aceptar un documento académico con su tipo de recurso y, cuando el tipo lo implique, el código de su curso, y ejecutar la ingesta como trabajo asíncrono, devolviendo un identificador de ejecución. | Incorporación de material nuevo sin intervención de desarrollo | ADR-007, ADR-009 |
| RF-03 **(D)** | Consultar el estado y el resultado de una ejecución de ingesta por su identificador. | AC-002 | ADR-007, ADR-010 |
| RF-04 | Validar todo hecho candidato contra el modelo ontológico antes de escribir. Ningún hecho inválido se persiste. | AC-001 | ADR-003, ADR-005 |
| RF-05 | Registrar, por cada ejecución rechazada, cada violación con la regla que infringe y el lote candidato completo. Los descartes no reingresan al grafo. | AC-001 (medida), AC-002 | ADR-010 |
| RF-06 | Enlazar las entidades extraídas a los nodos ya existentes en el grafo —de cualquiera de las dos capas— cuando exista correspondencia, evitando duplicados. La escritura no crea ni modifica nodos de la capa de referencia. | AC-001 | DD-02, ADR-011 |
| RF-07 | Registrar la procedencia de cada instancia y de cada arista institucional escrita. | AC-003 | DD-09,  |
| RF-08 | Persistir los hechos institucionales validados escritas en el almacén de hechos, reaplicables sin volver a invocar el modelo de lenguaje. | AC-004 | ADR-004, ADR-012 |
| RF-09 | Ejecutar el conjunto de consultas de integridad declaradas Al cierre de la carga, de cada ingesta y de la reaplicación y emitir un reporte por regla de integridad y del módulo en una sola ejecución. | AC-002 | DD-10, ADR-005 |

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
| RF-18 | Buscar elementos del grafo por nombre legible, con coincidencia parcial. | Precondición de RF-11 a RF-17 | — |
| RF-24 | Servir el documento de un recurso de aprendizaje institucional en la dirección que registra su localizador | PC5, E16 (72.1%) | RI-10, ADR-009 |

---

## **4\. Procesos de construcción del grafo**

| ID | Requisito | Origen | Restricción |
| ----- | ----- | ----- | ----- |
| RF-01 | Cargar la capa de referencia curada en el grafo a partir del TTL del backbone, sobre una base vacía, de forma reproducible. | AC-004 | DD-02, ADR-004 |
| RF-10 **(D)** | Reaplicar, como paso aparte y después de una carga, los hechos guardados de cada ejecución, en su orden original y sin invocar al modelo de lenguaje. | AC-004 | ADR-004, ADR-012 |

**Alcance de RF-10.** La carga seguida de la reaplicación cubre cambios en la capa institucional, en el código de proyección y en los constructos añadidos solo al grafo, así como correcciones de etiqueta o descripción en la capa de referencia. **No cubre** cambios de identificador, fusión o eliminación de unidades de la capa de referencia, ni cambios en la T-Box: esos casos rompen los enlaces existentes y se atienden por migración planificada, fuera del alcance de este resultado. La medida de AC-04 se interpreta dentro de esta frontera.

---

## **5\. Requisitos del mecanismo de navegación (R5–R6)**

Enunciados en términos de capacidad, no de interacción. Los marcados como **provisional** quedan sujetos al diseño de flujos e interfaz de R5; los marcados como **firme** son compromisos ya adquiridos y no admiten revisión por criterio de producto.

| ID | Requisito | Origen | Restricción | Estado |
| ----- | ----- | ----- | ----- | ----- |
| RF-19 | Permitir al estudiante localizar un punto de entrada al grafo y explorarlo de forma visual e interactiva, recorriendo las relaciones desde un elemento hacia sus vecinos. | E16 (61.0%, 52.6%), PC1–PC7 | — | provisional |
| RF-20 | Presentar, para el elemento en foco, sus prerrequisitos, su ubicación estructural y sus recursos asociados con enlace de acceso. | PC1, PC3, PC5, PC6, E16 (83.1%, 72.1%) | — | provisional |
| RF-21 | Exponer al estudiante el documento del que se derivó cada afirmación institucional presentada. | AC-003 | DD-009 | **firme** |
| RF-22 | Distinguir de forma perceptible los elementos de la capa de referencia de los de la capa institucional. | AC-003 | DD-002 | **firme** |
| RF-23 **(D)** | Ofrecer al operador una vista para cargar un documento, seguir el estado de su ingesta, revisar los descartes de esa ejecución y consultar su reporte de auditoría. | AC-002 | ADR-007 | **firme** |

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
| PC1 | RF-11, RF-20 |
| PC2 | RF-12 |
| PC3 | RF-13, RF-20 |
| PC4 | RF-13 |
| PC5 | RF-14, RF-20, RF-24 |
| PC6 | RF-15, RF-20 |
| PC7 | RF-16 |
| AC-001 | RF-04, RF-05, RF-06 |
| AC-002 | RF-03, RF-05, RF-09, RF-23 |
| AC-003 | RF-07, RF-17, RF-21, RF-22 |
| AC-004 | RF-01, RF-08, RF-10 |
| AC-005 | RF-11 a RF-16 (patrones medidos) |

AC-005 no genera requisitos propios: califica el desempeño de los ya declarados. Los requisitos marcados **(D)** —RF-02, RF-03, RF-10, RF-23— existen por decisión arquitectónica y no por elicitación.

