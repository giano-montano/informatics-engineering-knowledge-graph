#!/usr/bin/env bash
# Probe: which constraint types this instance ACTUALLY accepts.
# Assumes nothing from the docs; tries to create each one and reports.
# Runs inside the container. Cleans up everything it creates.
#
# Usage: docker compose exec -T neo4j bash -s < lab/scripts/probe_constraints.sh
# Expects the password in $HEALTHCHECK_PASSWORD or $PROBE_PASSWORD.

PW="${HEALTHCHECK_PASSWORD:-$PROBE_PASSWORD}"
cs() { cypher-shell -u neo4j -p "$PW" --format plain "$1" 2>&1; }

run_probe() {
  local label="$1" stmt="$2"
  local output
  output="$(cs "$stmt")"
  if [ $? -eq 0 ] && ! printf '%s' "$output" | grep -qi "error\|not supported\|unsupported"; then
    printf '  OK       %s\n' "$label"
  else
    local reason
    reason="$(printf '%s' "$output" | grep -io 'is not supported[^.]*\|requires Neo4j Enterprise[^.]*\|Unsupported[^.]*' | head -1)"
    [ -z "$reason" ] && reason="$(printf '%s' "$output" | head -2 | tr '\n' ' ')"
    printf '  NO       %-28s -> %s\n' "$label" "$reason"
  fi
}

echo "=== edition and instance ==="
cs "CALL dbms.components() YIELD name, versions, edition RETURN versions[0] AS version, edition;"

echo ""
echo "=== NODE constraints ==="
run_probe "uniqueness"      "CREATE CONSTRAINT p_n_uniq FOR (n:_Probe) REQUIRE n.k IS UNIQUE;"
run_probe "composite key"   "CREATE CONSTRAINT p_n_key  FOR (n:_Probe) REQUIRE (n.k, n.j) IS NODE KEY;"
run_probe "existence"       "CREATE CONSTRAINT p_n_exi  FOR (n:_Probe) REQUIRE n.m IS NOT NULL;"
run_probe "property type"   "CREATE CONSTRAINT p_n_typ  FOR (n:_Probe) REQUIRE n.s IS :: STRING;"

echo ""
echo "=== RELATIONSHIP constraints ==="
run_probe "uniqueness"      "CREATE CONSTRAINT p_r_uniq FOR ()-[r:_PROBE]-() REQUIRE r.k IS UNIQUE;"
run_probe "composite key"   "CREATE CONSTRAINT p_r_key  FOR ()-[r:_PROBE]-() REQUIRE (r.k, r.j) IS RELATIONSHIP KEY;"
run_probe "existence"       "CREATE CONSTRAINT p_r_exi  FOR ()-[r:_PROBE]-() REQUIRE r.m IS NOT NULL;"
run_probe "property type"   "CREATE CONSTRAINT p_r_typ  FOR ()-[r:_PROBE]-() REQUIRE r.s IS :: STRING;"

echo ""
echo "=== what actually got created ==="
cs "SHOW CONSTRAINTS YIELD name, type, entityType RETURN name, type, entityType ORDER BY name;"

echo ""
echo "=== cleanup ==="
for c in p_n_uniq p_n_key p_n_exi p_n_typ p_r_uniq p_r_key p_r_exi p_r_typ; do
  cs "DROP CONSTRAINT $c IF EXISTS;" >/dev/null 2>&1
done
cs "SHOW CONSTRAINTS YIELD name RETURN count(*) AS remaining_constraints;"
