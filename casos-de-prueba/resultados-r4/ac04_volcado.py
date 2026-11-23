"""Vuelca la capa institucional del grafo, ordenada, y la etiqueta de KU-OS-Purpose."""
import json, sys
from neo4j import GraphDatabase
from iekg.settings import Settings

s = Settings.from_environment()
with GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password)) as d:
    with d.session(database=s.neo4j_database) as ses:
        nodes = ses.run("MATCH (n {layer:'institutional'}) RETURN n.key AS k, labels(n) AS l, properties(n) AS p").data()
        edges = ses.run("MATCH (a)-[r]->(b) WHERE a.layer='institutional' RETURN a.key AS a, type(r) AS t, b.key AS b, properties(r) AS p").data()
        ku = ses.run("MATCH (u {key:'http://www.informatics-engineering-kms.org/ontology/informatic-engineering#KU-OS-Purpose'}) RETURN u.prefLabelEs AS es").single()["es"]
        total = ses.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        rels = ses.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
for n in nodes: n["l"] = sorted(n["l"])
out = {"nodes": sorted(nodes, key=lambda n: n["k"]),
       "edges": sorted(edges, key=lambda e: (e["a"], e["t"], e["b"])),
       "ku_os_purpose_es": ku, "total_nodes": total, "total_edges": rels}
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, indent=1)
print(sys.argv[1], len(nodes), "nodos institucionales,", len(edges), "aristas institucionales;", total, "nodos y", rels, "aristas; KU-OS-Purpose:", ku)
