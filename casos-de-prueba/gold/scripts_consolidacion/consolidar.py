# Paso 3: genera gold_consolidado.tsv uniendo los 13 TSV corregidos y el mapeo id_local -> id_global.
from load import *
from idglobal import asignar
rows=[]; meta={}
for c in ORDER:
    m,rs=parse(open(f"gold/gold_{c}.tsv",encoding="utf-8").read()); meta[c]=m; rows+=rs
mapa,_=asignar(rows)
with open("mapeo_id_global.tsv","w",encoding="utf-8") as fh:
    fh.write("silabo\tid\tid_global\n")
    for r in rows: fh.write(f"{r['id'][:6]}\t{r['id']}\t{mapa[r['id']]}\n")
with open("gold_consolidado.tsv","w",encoding="utf-8") as fh:
    fh.write("# gold_consolidado | silabos=13 | guia=v2.1 | fecha=2026-10-02 | consolidador=Claude Opus 5.5\n")
    fh.write("silabo\tid_global\t"+"\t".join(COLS)+"\n")
    for r in rows:
        fh.write(f"{r['id'][:6]}\t{mapa[r['id']]}\t"+"\t".join(r[k] for k in COLS)+"\n")
print(len(rows),"filas,",len(set(mapa.values())),"id_global")
