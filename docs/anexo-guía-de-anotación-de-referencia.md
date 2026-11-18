# **Anexo L. Guía de anotación de referencia**

Este anexo resume la guía con la que se anotaron los sílabos de los casos de prueba de la ingesta. Las reglas de emparejamiento y conteo están en esa sección. En el repositorio del proyecto ([https\://github.com/giano-montano/informatics-engineering-knowledge-graph](https://github.com/giano-montano/informatics-engineering-knowledge-graph)) están el texto completo de la guía, tal como se entregó al modelo anotador, las anotaciones y los scripts de consolidación (ver L.7).

## **L.1 Qué se anota**

Se anotan solo temas y conceptos. Cada sílabo se anota completo, aunque otro sílabo contenga lo mismo.

* La sumilla y los contenidos aportan entradas obligatorias y aceptables.  
* Las demás secciones (resultados de aprendizaje, requisitos, metodología) aportan solo entradas aceptables.  
* La bibliografía y el sistema de evaluación no aportan entradas.

No son entidades las actividades, las evaluaciones, los títulos de libros, las competencias genéricas, los nombres o códigos de cursos ni los encabezados genéricos ("Introducción", "Unidad I").

## **L.2 Tipo**

El tipo se asigna por la estructura del sílabo:

* **Tema:** el título de una unidad, capítulo o subunidad que agrupa ítems. Si hay dos niveles de encabezado, es tema el que contiene directamente los ítems; el nivel superior es tema aceptable si nombra un saber.  
* **Concepto:** cada ítem dentro de un tema. También es concepto la entidad que aparece solo en la sumilla, salvo que coincida con un tema de los contenidos.

Todo concepto se asocia al tema que lo contiene o, si no tiene encabezado, al tema de los contenidos que mejor le corresponde.

## **L.3 Granularidad**

* **"Introducción a X" o "Fundamentos de X":** la entidad es X.  
* **Enumeraciones:** cada elemento que se pueda nombrar por sí solo es una entrada. El término que las agrupa es tema aceptable si no aparece literal.  
* **Ítem que nombra más de un saber:** una entrada por saber, salvo que juntos formen un saber con nombre propio.  
* **Encabezado que nombra más de un saber:** una sola entrada de tema; cada saber del encabezado va como nombre alternativo.  
* **Lenguajes, notaciones y estándares:** son conceptos. Los productos y herramientas concretos son conceptos aceptables si el curso los enseña o los usa como contenido.  
* **Calificadores:** se conservan ("SQL avanzado" no se reduce a "SQL"). Se quitan las fórmulas de actividad ("estudio de", "aplicaciones de").  
* **Repeticiones:** una sola entrada por noción y tipo dentro de un mismo sílabo.

## **L.4 Nivel**

* **Obligatoria:** nombrada literalmente en la sumilla o en los contenidos.  
* **Aceptable:** el término que agrupa una enumeración, un concepto implícito inequívoco o una entidad nombrada solo en otras secciones. Un implícito que no es inequívoco no se anota.

## **L.5 Etiqueta, nombres alternativos y evidencia**

* **Etiqueta:** como figura en el sílabo, sin numeración ni horas.  
* **Nombres alternativos:** siglas, traducción, singular y variantes de uso común que nombran exactamente lo mismo, nunca algo más general ni más específico.  
* **Evidencia:** el fragmento literal del sílabo que sustenta la entrada.

## **L.6 Consolidación**

Terminada la anotación de los 13 sílabos, se revisó que las reglas se hubieran aplicado igual en todos y se registró cada corrección. Luego se asignó un identificador global a cada noción con estas reglas:

1. Las entradas comparten identificador si nombran la misma noción, sin importar el tipo ni la redacción.  
2. Se agrupa por identidad, no por parentesco: una generalización, una parte o un caso particular llevan identificadores distintos.  
3. Las entradas cuyos nombres coinciden tras normalizarlos comparten identificador, salvo que la evidencia muestre significados distintos.  
4. Las agrupaciones sin coincidencia de nombres, y las separaciones de nombres coincidentes, se sometieron a adjudicación del autor.

## **L.7 Archivos en el repositorio**

Consultables en:

[https\://github.com/giano-montano/informatics-engineering-knowledge-graph/tree/dev/casos-de-prueba/gold](https://github.com/giano-montano/informatics-engineering-knowledge-graph/tree/dev/casos-de-prueba/gold) 

