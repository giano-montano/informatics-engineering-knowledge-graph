import glob, os, collections
# Orden de ingesta de los casos de prueba CP-01 a CP-13 (tesis, 5.2.5): nivel del curso en el plan y, dentro del nivel, código.
ORDER=["1INF25","1INF27","1INF33","1INF49","1INF29","1INF30","1INF31","1INF32","1INF24","1INF50","1INF37","1INF54","1INF47"]
GOLD=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # casos-de-prueba/gold
COLS="id tipo nivel etiqueta alias tema_padre seccion evidencia nota".split()
def gold_path(code):
    paths=glob.glob(os.path.join(GOLD,f"CP-*-gold_{code}.tsv"))
    assert len(paths)==1,(code,paths)
    cp=f"CP-{ORDER.index(code)+1:02d}-"
    assert os.path.basename(paths[0]).startswith(cp),(code,paths[0],"no coincide con ORDER")
    return paths[0]
def load_gold(code):
    return open(gold_path(code),encoding="utf-8").read()
import unicodedata, re
def norm(s):
    s=s.lower()
    s=unicodedata.normalize("NFD",s); s="".join(c for c in s if unicodedata.category(c)!="Mn")
    s=re.sub(r"[^\w\s]"," ",s)          # quita puntuación
    s=re.sub(r"_"," ",s)
    w=[re.sub(r"s$","",x) for x in s.split()]
    return " ".join(x for x in w if x)
def parse(txt):
    lines=txt.rstrip("\n").split("\n")
    return lines[0], [dict(zip(COLS,l.split("\t"))) for l in lines[2:]]
PREP={"de","del","con","en","para","a","al","por","entre","sobre","y","o","e","vs","versus","desde"}
def sing_word(w):
    lw=w.lower()
    if lw.endswith("ces") and len(lw)>4: return w[:-3]+("Z" if w[-3].isupper() else "z")
    if lw.endswith("iones"): return w[:-5]+("IÓN" if w[-5].isupper() else "ión")
    if lw.endswith("ones") and len(lw)>5: return w[:-4]+("ÓN" if w[-4].isupper() else "ón")
    if lw.endswith("es") and len(lw)>3 and lw[-3] in "lnrdy": return w[:-2]
    if lw.endswith("s") and len(lw)>3 and not lw.endswith("ss") and lw[-2] in "aeiouáéíóú": return w[:-1]
    return w
def singular_head(label):
    out=[];stop=False
    for w in label.split():
        if w.lower() in PREP or "(" in w or ":" in w: stop=True
        out.append(w if stop else sing_word(w))
    return " ".join(out)
