#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[quality-gate] Backend coverage gate (>=80%)"
cd backend
PYTHONPATH=. pytest --cov=app --cov-report=term-missing --cov-fail-under=80
cd "$ROOT_DIR"

echo "[quality-gate] Frontend high-value coverage gate"
pnpm --dir frontend run test:high-value -- --coverage

echo "[quality-gate] All quality gates passed."
