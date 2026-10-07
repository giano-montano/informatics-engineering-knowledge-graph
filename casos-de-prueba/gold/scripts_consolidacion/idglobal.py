# Paso 2: asignación de id_global (reglas 1-4 de la guía v2.1).
from load import *
import collections
def vocab(r): return {norm(t) for t in [r["etiqueta"]]+[a for a in r["alias"].split("|") if a.strip()]}

# Encabezados que nombran más de un saber (mitades como alias): enlazan solo por su etiqueta completa.
# Una mitad no es el encabezado (regla 2: la parte no es el todo); si enlazaran por sus mitades,
# encadenarían nociones distintas (p. ej. construcción de software = pruebas de software).
COMPUESTOS = """1INF27-009 1INF27-029 1INF25-009 1INF25-059 1INF29-018 1INF29-034 1INF29-049 1INF49-024 1INF49-028
1INF49-035 1INF30-022 1INF30-069 1INF32-001 1INF32-005 1INF24-001 1INF24-024 1INF24-029 1INF24-035 1INF24-065
1INF24-080 1INF37-019 1INF37-033 1INF37-040 1INF54-001 1INF54-015 1INF54-026 1INF54-033""".split()

# Regla 3: coinciden tras normalizar pero la evidencia muestra significados distintos -> se separan y se escalan.
SEPARAR = {
 "1INF30-003": ({"c","lenguaje c","lenguaje de programacion c"}, "C# (1INF30) y C++ (1INF25) se normalizan a 'c'."),
 "1INF24-043": ({"normalizacion","normalizacion de dato"}, "Normalización de datos en ML (escalado de variables) frente a normalización de bases de datos (1INF33)."),
 "1INF25-021": ({"manejo de memoria","gestion de memoria","memory management"}, "Manejo de memoria del programador en C++ frente a administración de memoria del SO (1INF29-041)."),
 "1INF31-045": ({"interface","interfaz"}, "Interfaces entre componentes de una arquitectura frente a la construcción 'interface' de Java/C# (1INF25-075, 1INF30-016)."),
 "1INF33-035": ({"restriccione","constraint"}, "Constraints de tablas SQL frente a restricciones de requisitos/arquitectura (1INF49-041, 1INF31-011)."),
 "1INF33-074": ({"relacione","relacion"}, "Relaciones entre entidades del modelo E-R frente a relaciones matemáticas (1INF33-017), ya separadas por el anotador."),
 "1INF29-060": ({"dato"}, "Datos de un archivo (componente del archivo) frente a datos como concepto de BD (1INF33-018)."),
 "1INF29-062": ({"operacione","operacion"}, "Operaciones sobre archivos frente a operaciones del modelo relacional (1INF33-027)."),
 "1INF30-074": ({"parametro"}, "Parámetros de un reporte JasperSoft frente a parámetros de subprogramas PL/SQL (1INF33-053)."),
 "1INF30-076": ({"variable"}, "Variables de un reporte JasperSoft frente a variables de PL/SQL (1INF33-054)."),
 "1INF29-074": ({"componente"}, "Componentes de un sistema operativo frente a componentes de una arquitectura de software (1INF31-012)."),
}
# Regla 4: fusiones sin coincidencia de etiqueta ni alias (escaladas).
FUSIONAR = [
 ("1INF24-016","1INF24-014","El ítem 'Importancia de la búsqueda en la solución de problemas de IA' es el mismo saber que el tema 'Búsqueda dentro de la IA' (el propio anotador lo pidió en la nota)."),
 ("1INF49-036","1INF54-018","'Validación y verificación del producto de software' y 'Verificación y validación' nombran ambos V&V del software."),
]

def asignar(rows):
    parent={r["id"]:r["id"] for r in rows}
    def f(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def u(a,b): parent[f(a)]=f(b)
    k2r=collections.defaultdict(list)
    for r in rows:
        ks = {norm(r["etiqueta"])} if r["id"] in COMPUESTOS else vocab(r)
        ks -= SEPARAR.get(r["id"],(set(),))[0]
        for k in ks: k2r[k].append(r["id"])
    for k,ids in k2r.items():
        for i in ids[1:]: u(ids[0],i)
    for a,b,_ in FUSIONAR: u(a,b)
    # numeración por orden de primera aparición (orden de los casos de prueba, luego orden de filas)
    gid={}; n=0; out={}
    for r in rows:
        root=f(r["id"])
        if root not in gid: n+=1; gid[root]=f"G-{n:04d}"
        out[r["id"]]=gid[root]
    return out, k2r
