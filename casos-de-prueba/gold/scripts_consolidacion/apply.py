from load import *
from patches import P
import csv
rows_by={}; meta_by={}
def raw_rows(code):
    lines=load_raw(code).rstrip("\n").split("\n")
    return lines[0],[l.split("\t") for l in lines[2:]]
log=[]
for code in ORDER:
    meta,rr=raw_rows(code)
    rs=[]
    for f in rr:
        rid=f[0]
        if any(p[0]=="fixfields" and p[1]==rid for p in P):
            assert len(f)==10 and f[6]=="" , (rid,f)
            f=f[:6]+f[7:]
            log.append((code,rid,"fixfields","","10 campos","9 campos",[p for p in P if p[1]==rid and p[0]=="fixfields"][0][2],[p for p in P if p[1]==rid and p[0]=="fixfields"][0][3]))
        assert len(f)==9,(rid,len(f))
        rs.append(dict(zip(COLS,f)))
    rows_by[code]=rs; meta_by[code]=meta
idx={r["id"]:r for c in ORDER for r in rows_by[c]}
dropped=set()
for p in P:
    op,rid=p[0],p[1]; code=rid[:6]; r=idx[rid]
    if op=="fixfields": continue
    cat,why=p[-2],p[-1]
    if op=="unquote":
        old=r["nota"]; assert old.startswith('"') and old.endswith('"') and '""' in old, rid
        r["nota"]=old[1:-1].replace('""','"'); log.append((code,rid,op,"nota",old,r["nota"],cat,why))
    elif op=="set":
        fld,old,new=p[2],p[3],p[4]; assert r[fld]==old,(rid,fld,r[fld]); r[fld]=new
        log.append((code,rid,op,fld,old,new,cat,why))
    elif op=="alias_add":
        v=p[2]; al=[a for a in r["alias"].split("|") if a]
        assert norm(v) not in {norm(x) for x in al+[r["etiqueta"]]},(rid,v)
        old=r["alias"]; r["alias"]="|".join(al+[v]); log.append((code,rid,op,"alias","",v,cat,why))
    elif op=="alias_del":
        v=p[2]; al=r["alias"].split("|"); assert v in al,(rid,v); al.remove(v); r["alias"]="|".join(al)
        log.append((code,rid,op,"alias",v,"",cat,why))
    elif op=="alias_rep":
        o,n=p[2],p[3]; al=r["alias"].split("|"); assert o in al,(rid,o); al[al.index(o)]=n; r["alias"]="|".join(al)
        log.append((code,rid,op,"alias",o,n,cat,why))
    elif op=="drop":
        dropped.add(rid); log.append((code,rid,op,"fila",r["etiqueta"],"(eliminada)",cat,why))
    elif op=="reparent":
        new=p[2]
        for x in rows_by[code]:
            if x["tema_padre"]==rid and x["id"] not in dropped:
                log.append((code,x["id"],"set","tema_padre",rid,new,cat,why)); x["tema_padre"]=new
# chequeo: nadie apunta a una fila eliminada
for c in ORDER:
    for x in rows_by[c]:
        if x["id"] in dropped: continue
        assert x["tema_padre"] not in dropped, (x["id"],x["tema_padre"])
import os; os.makedirs("gold",exist_ok=True)
for c in ORDER:
    with open(f"gold/gold_{c}.tsv","w",encoding="utf-8") as fh:
        fh.write(meta_by[c]+"\n"+"\t".join(COLS)+"\n")
        for x in rows_by[c]:
            if x["id"] in dropped: continue
            fh.write("\t".join(x[k] for k in COLS)+"\n")
with open("changelog.tsv","w",encoding="utf-8") as fh:
    fh.write("silabo\tid\toperacion\tcampo\tantes\tdespues\tcategoria\tmotivo\n")
    for l in log: fh.write("\t".join(l)+"\n")
import collections
print(len(log),"cambios;",collections.Counter(l[6] for l in log))
print("filas eliminadas:",sorted(dropped))
