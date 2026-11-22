# Guion de la sesión con usuarios (R6)

Se lee tal cual en cada sesión, para que las tres sean iguales. Los casos, los resultados esperados
y qué cuenta como indicación están en `plan-de-pruebas-de-aceptacion-r6.md`. Duración: unos 40
minutos.

## Antes de la sesión

- La aplicación desplegada responde, con el grafo de la corrida final de R4: la «Hoja 2» de
  `plan-de-pruebas-de-aceptacion-r6.md`, en esta misma carpeta.
- El participante tiene abierta una ventana privada de al menos 1366 × 768, en el inicio.
- Están abiertos el registro de la sesión y el enlace al formulario.
- No hay ninguna ingesta corriendo.

## 1. Presentación (2 min)

> Gracias por ayudarme. Vas a usar InfoKnows, una aplicación que muestra cómo se relacionan los
> temas y conceptos de los cursos de Informática con el currículo internacional CS2023. Lo que se
> prueba es la aplicación, no a ti.
>
> Primero te muestro cómo se usa, unos diez minutos; ahí puedes preguntarme todo. Después te leo diez
> tareas. Intenta hacerlas solo. Si te trabas, puedes pedirme ayuda y te la doy, pero lo anoto; o
> dime «paso» y seguimos con la siguiente. Si puedes, piensa en voz alta. Al final llenas un
> formulario corto.

## 2. Capacitación (10 min)

Se hace con elementos de **Bases de Datos (1INF33)**, que ninguna tarea usa. Ninguna tarea se
resuelve en la capacitación. El evaluador maneja y el participante mira; después, el participante
repite los pasos 2 a 4 por su cuenta.

1. **El inicio.** Las 17 áreas de CS2023 y los cursos con sílabo. Las áreas con temas de los
   sílabos se distinguen, con sus cifras.
2. **Buscar.** Se escribe «subconsultas». Cada resultado dice su clase y si viene de CS2023 o de un
   sílabo. Se elige el concepto «Subconsultas».
3. **El foco.** El elemento queda en el centro del mapa, con sus vecinos y el nombre de cada
   relación. La ficha del panel muestra lo mismo como lista («Conexiones»). Un vecino con **+**
   trae sus conexiones sin cambiar el foco. Al hacer clic en un vecino, este pasa a ser el foco. Lo
   visitado permite volver.
4. **Las preguntas del panel**, sobre «Subconsultas»: «Qué necesitas antes», «Tipos» y «Dónde está
   en la carrera». Si una vista trae «Cómo leerlo», se abre una vez.
5. **Un tema**, «SQL DML»: «Qué contiene», con el orden en que conviene aprender sus conceptos, y
   «Material de estudio», que abre el PDF del sílabo.
6. **Un curso**, «Bases de Datos»: «Cursos que conviene llevar antes» y «Camino hasta aquí», con
   el selector «Ver por» (tema, curso, área) arriba del mapa y el «¿Por qué?» de una parada.
7. **De dónde sale un dato.** Se selecciona una relación y se muestra su fuente. El interruptor
   «Fuentes» une cada elemento con su documento.

> ¿Alguna pregunta antes de empezar? Desde ahora, intenta hacerlo solo.

## 3. Tareas (25 min)

Se lee cada tarea completa; la línea «Después» se lee cuando el participante termina la parte
anterior. Si pide repetir, se repite igual. Se vuelve al inicio solo si la tarea lo dice.

| Caso | Se lee |
|---|---|
| CA-01 | «Quieres repasar cómo administra la memoria un sistema operativo. Encuentra el tema ADMINISTRACIÓN DE MEMORIA y ábrelo.» Después: «Ahora quieres saber si hay algo sobre compiladores. Búscalo.» |
| CA-02 | «Mira con qué se relaciona el tema ADMINISTRACIÓN DE MEMORIA, pasa a su concepto Memoria virtual y vuelve al tema. Después, sin que el tema deje de estar en el centro, haz que el mapa muestre también con qué se relaciona uno de sus vecinos.» |
| CA-03 | «Antes de estudiar Memoria virtual, averigua qué deberías saber, y por qué una de esas cosas va antes.» Después: «Haz lo mismo con el concepto Memoria, del sílabo de Programación 2.» |
| CA-04 | «Vas a llevar Sistemas Operativos. Averigua qué conceptos te pide su sílabo saber al empezar, y qué otro curso enseña esos conceptos, para llevarlo antes.» |
| CA-05 | «Averigua en qué parte de la carrera está Memoria virtual.» |
| CA-06 | «Mira qué conceptos tiene el tema ADMINISTRACIÓN DE MEMORIA y en qué orden conviene aprenderlos. Después, mira qué contiene el área Sistemas Operativos.» |
| CA-07 | «Busca material para estudiar el tema ADMINISTRACIÓN DE MEMORIA y ábrelo. Luego intenta lo mismo con Memoria virtual.» Después: «Ahora busca material del área Fundamentos Algorítmicos.» |
| CA-08 | «Quieres llegar a entender Memoria virtual. Contando no solo lo que necesita justo antes, sino también lo que necesita eso, y así hacia atrás, averigua por qué cursos te conviene pasar antes, y por qué.» Después, una a una: «Mira ese mismo camino agrupado por temas, y luego por áreas.» · «¿Por qué pasar por Programación 2?» · «Ahora pon como meta el curso Sistemas Operativos: ¿por qué cursos conviene pasar antes, siguiendo la misma cadena hacia atrás?» |
| CA-09 | «Averigua qué tipos de Llamadas al sistema hay, y de qué es un tipo uno de ellos.» Después: «Mira los tipos de Memoria virtual.» |
| CA-10 | «El sistema dice que Memoria virtual necesita antes Paginación. Comprueba en qué documento se dice eso y ábrelo.» Después: «¿Y de dónde sale la unidad Gestión de Memoria?» |

**Para el evaluador, no se lee.** Algunas partes no tienen resultado a propósito: prueban cómo
responde el sistema cuando no hay nada que mostrar. Lo que
debe verse en cada paso está en `plan-de-pruebas-de-aceptacion-r6.md`, sección «Hoja de datos» ›
«Hoja 2 · Grafo de la corrida final» › «Resultados esperados».

- **CA-01.** «compiladores» no está en ningún sílabo ni en CS2023. Lo esperado: el aviso de que
  nada coincide y la oferta de ver las áreas.
- **CA-02.** Es el botón **+** del vecino en el mapa: sus conexiones se agregan al mapa y el tema
  sigue en el centro. Seleccionar una relación y leer su ficha no cuenta: eso es CA-10.
- **CA-04.** Es la pregunta de un solo paso, «Cursos que conviene llevar antes»: lo que el sílabo
  de 1INF29 pide («Memoria» y «Programación») y los cursos que lo enseñan (1INF25 y 1INF27).
  «Camino hasta aquí» no es esta respuesta.
- **CA-07.** Que Memoria virtual no tenga material es lo esperado: el sistema dice que un concepto
  no tiene material propio y remite al de su tema.
- **CA-08.** Es «Camino hasta aquí», que sigue los prerrequisitos hacia atrás todos los pasos.
  «Por temas y por áreas» es el selector «Ver por», arriba del mapa, que solo aparece en esa
  vista. Con el curso como meta, el camino (1INF25, 1INF27 y 1INF30) no coincide con CA-04, y el
  sistema lo dice; que difieran no reprueba el caso.

Durante las tareas, el evaluador no ofrece ayuda. Si el participante la pide, da la indicación
mínima para que siga y la anota: el caso queda reprobado por uso. A «¿así?» responde «haz lo que
harías si estuvieras solo», salvo que sea un pedido de ayuda. Cada paso se anota en el registro al
momento.

## 4. Cierre (3 min)

> Eso es todo, gracias. Te paso el enlace del formulario: son cuatro preguntas de opinión y unos datos
> tuyos. Tu nombre no aparece en la tesis.
