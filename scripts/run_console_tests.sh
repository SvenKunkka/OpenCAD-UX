#!/usr/bin/env bash
# Run the FreeCAD console test-suite against the local FreeCAD install.
# Usage: bash scripts/run_console_tests.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
FC_CMD="${FC_CMD:-}"
if [ -z "$FC_CMD" ]; then
  if [ -x "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd" ]; then
    FC_CMD="/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
  elif command -v freecadcmd >/dev/null 2>&1; then
    FC_CMD="$(command -v freecadcmd)"
  else
    echo "freecadcmd not found. Set FC_CMD=/path/to/freecadcmd" >&2
    exit 2
  fi
fi

CFG="$(mktemp -d)"
trap 'rm -rf "$CFG"' EXIT
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-offscreen}"

echo "== OpenCAD UX console tests (FreeCAD: $("$FC_CMD" --version | head -1)) =="
"$FC_CMD" -P "$REPO" -u "$CFG/user.cfg" -s "$CFG/system.cfg" \
  -c "import runpy, sys; sys.argv=['run_all']; runpy.run_path('$REPO/tests/fc/run_all.py', run_name='__main__')"
