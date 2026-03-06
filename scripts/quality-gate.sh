#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[quality-gate] Backend coverage gate (>=85%)"
PYTHONPATH=backend pytest --cov=backend/app --cov-report=term --cov-fail-under=85

echo "[quality-gate] Frontend high-value coverage gate"
npm --prefix frontend run test:high-value -- --coverage

echo "[quality-gate] All quality gates passed."
