#!/usr/bin/env bash
# Build the three example consumer-electronics models and export STEP/STL.
# Usage: bash scripts/run_examples.sh
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
"$FC_CMD" -P "$REPO" -u "$CFG/user.cfg" -s "$CFG/system.cfg" \
  -c "import runpy, sys; sys.argv=['build_all']; runpy.run_path('$REPO/examples/build_all.py', run_name='__main__')"
