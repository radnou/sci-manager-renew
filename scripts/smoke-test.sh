#!/bin/bash
# GererSCI — Post-deployment smoke test
# Usage: ./scripts/smoke-test.sh [BASE_URL]
# Default: http://localhost:8000

set -e

BASE="${1:-http://localhost:8000}"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'
FAILURES=0

check() {
    local name="$1"
    local method="$2"
    local url="$3"
    local expected_status="$4"
    local body="${5:-}"

    if [ "$method" = "GET" ]; then
        status=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    else
        status=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 -X "$method" \
            -H "Content-Type: application/json" -d "$body" "$url" 2>/dev/null || echo "000")
    fi

    if [ "$status" = "$expected_status" ]; then
        echo -e "  ${GREEN}✓${NC} $name ($status)"
    else
        echo -e "  ${RED}✗${NC} $name — expected $expected_status, got $status"
        ((FAILURES++))
    fi
}

echo "=== GererSCI Smoke Test ==="
echo "Base URL: $BASE"
echo ""

echo "── Health Checks ──"
check "Liveness"  GET "$BASE/health/live" "200"
check "Readiness" GET "$BASE/health/ready" "200"

echo ""
echo "── Auth (unauthenticated) ──"
check "Login page reachable"   GET "$BASE/api/v1/auth/login" "405"
check "SCIs without auth"      GET "$BASE/api/v1/scis" "401"
check "Dashboard without auth" GET "$BASE/api/v1/dashboard" "401"
check "Export without auth"    GET "$BASE/api/v1/export/loyers" "401"

echo ""
echo "── API Structure ──"
check "OpenAPI schema" GET "$BASE/openapi.json" "200"
check "404 on unknown" GET "$BASE/api/v1/nonexistent" "404"

echo ""
if [ $FAILURES -gt 0 ]; then
    echo -e "${RED}=== $FAILURES check(s) failed ===${NC}"
    exit 1
else
    echo -e "${GREEN}=== All checks passed ===${NC}"
fi
