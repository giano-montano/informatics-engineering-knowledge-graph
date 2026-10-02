import sys
from load import *
src = sys.argv[1] if len(sys.argv)>1 else "raw"
tot=0
for code in ORDER:
    if src=="raw":
        txt=load_raw(code)
    else:
        txt=open(f"{src}/gold_{code}.tsv",encoding="utf-8").read()
    lines=txt.rstrip("\n").split("\n")
    meta,hdr,rows=lines[0],lines[1],lines[2:]
    probs=[]
    if hdr.split("\t")!=COLS: probs.append("header")
    ids={}
    for i,l in enumerate(rows):
        f=l.split("\t")
        if len(f)!=9: probs.append(f"{f[0]} campos={len(f)}"); continue
        r=dict(zip(COLS,f)); ids[r["id"]]=r
        pass
        if r["tipo"] not in("tema","concepto"): probs.append(f"{r['id']} tipo={r['tipo']}")
        if r["nivel"] not in("obligatoria","aceptable"): probs.append(f"{r['id']} nivel={r['nivel']}")
        if r["seccion"] not in("sumilla","contenidos","otra"): probs.append(f"{r['id']} seccion={r['seccion']}")
        if '""' in r["nota"]: probs.append(f"{r['id']} nota entrecomillada CSV")
    for r in ids.values():
        tp=r["tema_padre"]
        if tp:
            if tp not in ids: probs.append(f"{r['id']} padre inexistente {tp}")
            elif ids[tp]["tipo"]!="tema": probs.append(f"{r['id']} padre {tp} no es tema")
            if r["tipo"]=="tema": probs.append(f"{r['id']} tema con tema_padre {tp}")
        elif r["tipo"]=="concepto" and not r["nota"]: probs.append(f"{r['id']} concepto sin padre ni nota")
    tot+=len(rows)
    print(code, len(rows), meta.split("|")[-2].strip(), meta.split("|")[2].strip(), "; ".join(probs) or "OK")
print("total",tot)
