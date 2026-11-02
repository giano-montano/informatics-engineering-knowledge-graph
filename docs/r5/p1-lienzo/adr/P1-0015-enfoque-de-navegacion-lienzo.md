# P1-0015 · Enfoque de navegación: lienzo del grafo con un foco, lentes y panel lateral

**Contexto.** R5 debe dejar explorar el grafo de vecino en vecino (RF-19) y mostrar, para el elemento en foco, prerrequisitos, ubicación y recursos (RF-20). Los casos de uso CU-1 a CU-10 de `../casos-de-uso.md` son comunes a las tres propuestas. En la encuesta E16, el 61 % quiere entender cómo se conectan las áreas y el 52,6 %, descubrir temas que no conocía.

**Decisión.** El lienzo ocupa el centro. Siempre hay un elemento en foco, con su vecindario de `/api/nodes` alrededor, en anillos. Un clic en un vecino lo vuelve el foco, y **+** agrega las conexiones de un vecino sin perder lo anterior. Ocho **lentes** reordenan el mismo lienzo con la respuesta de una ruta y atenúan el resto: Vecindario, Qué necesitas antes, Camino hasta aquí, Cursos que conviene llevar antes, Dónde está en la carrera, Qué contiene, Material de estudio y Tipos. Un panel lateral lee el foco como ficha (fuente, ubicación, contenido y orden, prerrequisitos, material y conexiones), y un rastro de focos permite volver. Los códigos de casos de uso y requisitos solo aparecen con el interruptor «Ver trazabilidad».

**Descartadas.**
- Lienzo sin foco (todo el grafo de una vez): con 491 nodos no se lee nada, y la API está acotada a propósito (cotas 25/5).
- Una pantalla por caso de uso: rompe la continuidad, que es lo que contesta «¿cómo se conecta esto?».
- Panel flotante sobre el nodo: tapa justo lo que se quiere ver y no admite listas largas.

**Consecuencias.**
- Los diez casos de uso del estudiante se resuelven sobre el mismo lienzo, sin pantallas nuevas.
- El panel sirve también de alternativa en texto al lienzo (accesibilidad).
- Negativa: es la propuesta que más le exige al estudiante, porque tiene que leer un grafo. Para encontrar material de estudio (CU-7) es más lenta que un catálogo.

**Fila para la Tabla 20.** Enfoque de lienzo con foco, lentes y panel lateral · contesta «cómo se conecta» sin cambiar de pantalla y reutiliza las rutas de R4 tal como están.
