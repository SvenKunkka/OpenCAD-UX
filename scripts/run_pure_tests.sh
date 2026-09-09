#!/usr/bin/env bash
# Run the pure python test-suite (no FreeCAD required).
# Usage: bash scripts/run_pure_tests.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
python3 -m unittest discover -s tests/pure -v
