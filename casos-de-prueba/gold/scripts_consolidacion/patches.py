# Correcciones de la re-pasada de coherencia (paso 1 de la consolidación, guía v2.1).
# Cada parche: (op, id, *args, categoria, motivo). apply.py los aplica y genera el changelog.
C_FMT = "formato"
C_DUP = "fila duplicada"
C_VOC = "vocabulario"
C_SING = "alias singular (-es)"
C_NIV = "nivel"
C_TIPO = "regla Fundamentos de X"

SUMILLA_TEMA = "Mención de la sumilla que coincide con un tema de los contenidos: la guía dice que es la misma fila."

P = [
  # --- formato ---
  ("fixfields", "1INF50-001", C_FMT, "Tenía una tabulación de más (10 campos): sección y evidencia quedaban corridas."),
  ("fixfields", "1INF50-014", C_FMT, "Tenía una tabulación de más (10 campos): sección y evidencia quedaban corridas."),
  *[("unquote", i, C_FMT, "Nota con comillado CSV (\"\") dentro de un TSV; se deja el texto plano.")
    for i in ["1INF49-016","1INF49-036","1INF29-002","1INF29-005","1INF29-013","1INF29-014","1INF29-040","1INF29-050","1INF29-077","1INF29-078"]],
  ("set", "1INF31-008", "tema_padre", "1INF31-006", "", C_FMT, "Los temas llevan tema_padre vacío."),

  # --- filas duplicadas dentro del sílabo ---
  ("drop", "1INF33-004", C_DUP, SUMILLA_TEMA + " Coincide con el tema 1INF33-011 NORMALIZACIÓN (y duplicaba al concepto 046)."),
  ("drop", "1INF33-007", C_DUP, SUMILLA_TEMA + " Coincide con el tema 1INF33-013 (PL/SQL)."),
  ("drop", "1INF29-004", C_DUP, SUMILLA_TEMA + " Coincide con el tema 1INF29-041 ADMINISTRACIÓN DE MEMORIA; sus alias pasan al tema."),
  ("alias_add", "1INF29-041", "manejo de memoria", C_DUP, "Alias heredado de la fila 1INF29-004 eliminada (forma literal de la sumilla)."),
  ("alias_add", "1INF29-041", "gestión de memoria", C_DUP, "Alias heredado de la fila 1INF29-004 eliminada."),
  ("drop", "1INF49-045", C_DUP, "Repetía la noción y el tipo de 1INF49-022 Prototypes (que ya tiene 'prototipos' como alias): una sola fila por noción y tipo."),

  # --- 'Fundamentos de X' aplicado a 1INF29 ---
  ("set", "1INF29-006", "etiqueta", "PERSPECTIVA GENERAL DE SISTEMAS OPERATIVOS", "Sistemas operativos", C_TIPO,
   "'Perspectiva general de X' y 'Conceptos fundamentales de X' son la fórmula 'Introducción/Fundamentos de X': la entidad es X (como en 1INF31-001, 1INF50-002, 1INF30-037). Los dos capítulos nombran la misma noción y tipo: una sola fila."),
  ("set", "1INF29-006", "alias", "perspectiva general de sistemas operativos|general perspective of operating systems", "sistema operativo|operating systems|operating system", C_TIPO,
   "Alias de la nueva etiqueta; la forma con la fórmula no nombra exactamente lo mismo."),
  ("set", "1INF29-006", "evidencia", "CAPÍTULO 2 PERSPECTIVA GENERAL DE SISTEMAS OPERATIVOS", "CAPÍTULO 2 PERSPECTIVA GENERAL DE SISTEMAS OPERATIVOS / CAPÍTULO 3 CONCEPTOS FUNDAMENTALES DE SISTEMAS OPERATIVOS", C_TIPO,
   "Evidencia de ambos encabezados."),
  ("set", "1INF29-006", "nota", "", "Consolidación: caps. 2 y 3 son 'Introducción/Fundamentos de X'; la entidad es X y se fusionan en esta fila (antes 006 y 011).", C_TIPO, "Nota de la decisión."),
  ("drop", "1INF29-011", C_TIPO, "Fusionado en 1INF29-006 (misma noción y tipo)."),
  ("reparent", "1INF29-011", "1INF29-006", C_TIPO, "Los hijos de 1INF29-011 pasan a 1INF29-006."),

  # --- vocabulario ---
  ("set", "1INF33-046", "etiqueta", "Normalización de datos: Primera, segunda y tercera forma normal", "Normalización de datos", C_VOC,
   "La etiqueta arrastraba la enumeración ya anotada en 047-049; se deja el núcleo, como los demás encabezados en línea 'X: a, b'."),
  ("alias_rep", "1INF49-035", "validación", "validación de requisitos", C_VOC,
   "Mitad de encabezado en forma explícita (criterio de 1INF54-015/026/033); 'validación' suelta fusionaba por error con 1INF37-038 Validación de software."),
  ("alias_add", "1INF29-074", "componentes de los sistemas operativos", C_VOC, "Forma contextual de RA1 ('los componentes ... de los sistemas operativos'); la etiqueta suelta es genérica."),
  ("alias_add", "1INF31-006", "diseño de la arquitectura", C_VOC, "Forma nominal del encabezado en gerundio (criterio que el mismo anotador aplicó en 1INF49-032)."),
  ("alias_add", "1INF31-013", "presentación de la arquitectura", C_VOC, "Forma nominal del encabezado en gerundio."),
  ("alias_add", "1INF31-019", "documentación de la arquitectura", C_VOC, "Forma nominal del ítem en gerundio."),
  ("alias_add", "1INF31-020", "refinamiento de la arquitectura", C_VOC, "Forma nominal del encabezado en gerundio."),
  ("alias_add", "1INF31-031", "evaluación de la arquitectura", C_VOC, "Forma nominal del encabezado en gerundio."),
  ("alias_del", "1INF30-038", "elementos básicos de HTML", C_VOC, "Forma con la fórmula 'Fundamentos de X': no nombra exactamente lo mismo (criterio de 1INF31-001, 1INF24-002)."),
  ("alias_del", "1INF24-029", "fundamentos de machine learning y redes neuronales artificiales", C_VOC, "Forma con la fórmula 'Fundamentos de X'."),
  ("alias_del", "1INF24-001", "introducción a la IA búsqueda y optimización en IA", C_VOC, "Concatenación de dos encabezados con la fórmula 'Introducción a'; no es una variante de uso."),

  # --- nivel ---
  *[("set", i, "nivel", "aceptable", "obligatoria", C_NIV, "Nombrada literalmente en la sumilla: obligatoria (no es agrupador, implícito ni de otra sección).")
    for i in ["1INF49-044","1INF49-046","1INF49-047","1INF31-034","1INF31-035","1INF31-036","1INF31-037","1INF31-038","1INF31-039","1INF31-040"]],
]

# --- singular de plurales en -es (regla v2.1: el singular va como alias) ---
SING = {
  "1INF49-017": "estándar para el diseño de interfaces gráficas de usuario",
  "1INF49-026": "estándar internacional para la especificación de requisitos",
  "1INF49-028": "modelo conceptual con diagramas de clases",
  "1INF49-033": "patrón para la creación de modelos conceptuales con diagramas de clases",
  "1INF49-040": "necesidad del usuario",
  "1INF49-049": "necesidad del negocio",
  "1INF49-053": "patrón de diseño de interfaces de usuario",
  "1INF49-057": "restricción de la solución",
  "1INF33-061": "disparador",
  "1INF29-009": "función de un sistema operativo típico",
  "1INF29-075": "abstracción creada por los sistemas operativos",
  "1INF31-008": "factor que impacta en la arquitectura",
  "1INF31-009": "requerimiento funcional",
  "1INF31-011": "restricción",
  "1INF31-044": "requisito no funcional",
  "1INF31-045": "interfaz",
  "1INF24-064": "cuestión ética del ML/IA",
  "1INF37-065": "consideración técnica del despliegue",
  "1INF37-066": "consideración procedimental del despliegue",
}
P += [("alias_add", i, s, C_SING, "Plural en -es: la normalización actual no lo iguala con el singular.") for i, s in SING.items()]
