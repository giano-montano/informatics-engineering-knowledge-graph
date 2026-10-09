# Atributos de calidad del módulo del grafo de conocimiento

Resultado R3, Fase 1. La fuente es la tesis (§5.2.1, Tablas 14 y 15); ante una discrepancia, prima la tesis.

Método: escenarios de calidad en la forma de seis partes de Bass, Clements y Kazman (*Software Architecture in Practice*, 4.ª ed., 2021, cap. 3). Vocabulario: ISO/IEC 25010.

**Regla de uso:** toda decisión de diseño que se registre como ADR debe citar el atributo que la motiva. Si no cita ninguno, o no es una decisión arquitectónica o falta un atributo.

---

## Condiciones que determinan el conjunto

1. **El módulo opera sin razonador.** HermiT valida la ontología en tiempo de diseño. En ejecución, nadie comprueba dominio, rango, disyunción ni pertenencia. Esa verificación pasa a ser responsabilidad del módulo.
2. **El contenido institucional proviene de extracción con modelos de lenguaje.** Salida no determinista y de precisión inferior a la unidad. Se trata como hechos candidatos, nunca como afirmaciones aceptadas.

---

## Atributos

| ID | Propiedad | Origen | Prioridad |
|---|---|---|---|
| AC-01 | El grafo cargado cumple las condiciones que el modelo ontológico declara sobre su contenido | Ausencia de razonador en ejecución y salida no determinista de la extracción | Alta |
| AC-02 | Es posible demostrar AC-01 con un procedimiento documentado y re-ejecutable, sin inspeccionar el código | La ingesta debe ser verificable frente a un criterio de aceptación | Alta |
| AC-03 | Toda instancia y afirmación que la corrida crea queda asociada al documento del que fue derivada; las que ya existían conservan su procedencia | El estudiante debe poder remitir a su fuente la información que el sistema le presenta | Alta |
| AC-04 | Corregir una capa no obliga a reconstruir la otra | La capa de referencia se corrige y los documentos se reprocesan de forma reiterada durante el ciclo | Media |
| AC-05 | Las consultas con recorrido transitivo responden en tiempo compatible con navegación interactiva | La navegación exploratoria pierde utilidad si la respuesta interrumpe el flujo de atención | Media |

En conflicto, AC-01/02/03 ganan a AC-04/05.

---

## Escenarios

| | AC-01 | AC-02 | AC-03 | AC-04 | AC-05 |
|---|---|---|---|---|---|
| **Fuente** | Proceso de ingesta | Asesor, jurado o autor | Proceso de ingesta | Autor | Estudiante |
| **Estímulo** | Un lote de afirmaciones candidatas incluye elementos que violan las restricciones del modelo | Se requiere establecer si el grafo satisface las condiciones que el modelo ontológico declara sobre su contenido | Se ingesta un documento institucional | Se corrige la capa de referencia o se incorpora un documento nuevo | Se solicita una consulta con cierre transitivo o agregación multinivel |
| **Artefacto** | Grafo de conocimiento | Grafo de conocimiento | Capa de contenido institucional | Proceso de construcción del grafo | Base de datos |
| **Entorno** | Ingesta del conjunto piloto | Posterior a cualquier carga | Cualquier corrida de ingesta | Ciclo de desarrollo | Grafo cargado con el conjunto piloto (13 sílabos, del orden de mil nodos) en el entorno de despliegue del prototipo, tras una pasada de calentamiento |
| **Respuesta** | Las afirmaciones que violan esas condiciones no se incorporan al grafo; los que escapan se detectan después de la carga y se reportan | Se obtiene un reporte por condición | Toda instancia y afirmación que la corrida crea queda asociada al documento del que fue derivada; las que ya existían conservan su procedencia | La operación no re-ejecuta las etapas propias de la otra capa | Se retorna el resultado completo de la derivación |
| **Medida** | Cero violaciones detectadas después de la carga; afirmaciones rechazadas por documento y por tipo de condición | Toda condición declarada cuenta con una comprobación asociada; el reporte se obtiene en una única ejecución | Cero elementos institucionales sin procedencia tras la corrida | Una corrección de la capa de referencia no dispara ninguna extracción asistida por modelo de lenguaje | Tiempo de ejecución en el motor, sin serialización ni transporte, de los cinco patrones de consulta, cada uno ejecutado diez veces desde cada uno de sus nodos de partida válidos: mediana y percentil 95 por debajo de un segundo para cada patrón |

**Nota sobre AC-01.** La auditoría posterior a la carga es una medida necesaria pero insuficiente: el pipeline valida los hechos candidatos antes de escribirlos, de modo que difícilmente lleguen violaciones a la base. Por eso se registra también cuántos hechos candidatos fueron descartados en la validación y por qué motivo, dato que se reporta junto con la precisión de la extracción, ya que una precisión alta acompañada de un descarte masivo indicaría que el pipeline incorporó muy poco contenido.

**Nota sobre AC-05.** Los cinco patrones son el prerrequisito entre cursos, el área de un concepto, los recursos de un elemento agregados sobre sus partes, el prerrequisito elevado a tema, curso o área, y el cierre de especialización. La consulta del detalle de un nodo no se mide, porque recorre una distancia fija, el nodo y su vecindario cercano, y no deriva ningún cierre ni agregado. Ejecutar cada patrón desde todos sus nodos de partida evita elegir los parámetros de las consultas. El tamaño exacto del grafo y las características del entorno (procesador, memoria y versión del motor) se reportan junto con la medición, y la primera ejecución, con la caché fría, se reporta aparte y sin umbral.

---

## Pendientes

- **[AC-05]** El umbral de un segundo necesita cita (escala de tiempos de respuesta de Nielsen). Verificar antes de citar.
