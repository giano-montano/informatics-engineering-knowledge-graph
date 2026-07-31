#!/usr/bin/env bash
# Sonda: que tipos de restriccion acepta REALMENTE esta instancia.
# No asume nada de la documentacion; intenta crear cada una y reporta.
# Se ejecuta dentro del contenedor. Limpia todo lo que crea.
#
# Uso: docker compose exec -T neo4j bash -s < lab/scripts/probe_constraints.sh
# Espera la contrasena en $HEALTHCHECK_PASSWORD o $PROBE_PASSWORD.

PW="${HEALTHCHECK_PASSWORD:-$PROBE_PASSWORD}"
cs() { cypher-shell -u neo4j -p "$PW" --format plain "$1" 2>&1; }

run_probe() {
  local etiqueta="$1" stmt="$2"
  local salida
  salida="$(cs "$stmt")"
  if [ $? -eq 0 ] && ! printf '%s' "$salida" | grep -qi "error\|not supported\|unsupported"; then
    printf '  OK       %s\n' "$etiqueta"
  else
    local motivo
    motivo="$(printf '%s' "$salida" | grep -io 'is not supported[^.]*\|requires Neo4j Enterprise[^.]*\|Unsupported[^.]*' | head -1)"
    [ -z "$motivo" ] && motivo="$(printf '%s' "$salida" | head -2 | tr '\n' ' ')"
    printf '  NO       %-28s -> %s\n' "$etiqueta" "$motivo"
  fi
}

echo "=== edicion e instancia ==="
cs "CALL dbms.components() YIELD name, versions, edition RETURN versions[0] AS version, edition;"

echo ""
echo "=== restricciones sobre NODOS ==="
run_probe "unicidad"            "CREATE CONSTRAINT p_n_uniq FOR (n:_Probe) REQUIRE n.k IS UNIQUE;"
run_probe "clave compuesta"     "CREATE CONSTRAINT p_n_key  FOR (n:_Probe) REQUIRE (n.k, n.j) IS NODE KEY;"
run_probe "existencia"          "CREATE CONSTRAINT p_n_exi  FOR (n:_Probe) REQUIRE n.m IS NOT NULL;"
run_probe "tipo de propiedad"   "CREATE CONSTRAINT p_n_typ  FOR (n:_Probe) REQUIRE n.s IS :: STRING;"

echo ""
echo "=== restricciones sobre RELACIONES ==="
run_probe "unicidad"            "CREATE CONSTRAINT p_r_uniq FOR ()-[r:_PROBE]-() REQUIRE r.k IS UNIQUE;"
run_probe "clave compuesta"     "CREATE CONSTRAINT p_r_key  FOR ()-[r:_PROBE]-() REQUIRE (r.k, r.j) IS RELATIONSHIP KEY;"
run_probe "existencia"          "CREATE CONSTRAINT p_r_exi  FOR ()-[r:_PROBE]-() REQUIRE r.m IS NOT NULL;"
run_probe "tipo de propiedad"   "CREATE CONSTRAINT p_r_typ  FOR ()-[r:_PROBE]-() REQUIRE r.s IS :: STRING;"

echo ""
echo "=== lo que quedo creado ==="
cs "SHOW CONSTRAINTS YIELD name, type, entityType RETURN name, type, entityType ORDER BY name;"

echo ""
echo "=== limpieza ==="
for c in p_n_uniq p_n_key p_n_exi p_n_typ p_r_uniq p_r_key p_r_exi p_r_typ; do
  cs "DROP CONSTRAINT $c IF EXISTS;" >/dev/null 2>&1
done
cs "SHOW CONSTRAINTS YIELD name RETURN count(*) AS restricciones_restantes;"
