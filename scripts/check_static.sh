#!/usr/bin/env bash
# Static checks that need no FreeCAD:
#   1. python syntax across the repo
#   2. ribbon.json schema + icon assets are in sync
#   3. regenerating the icons is deterministic (idempotent diff)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "== py_compile (all python sources) =="
python3 -m compileall -q opencad_ux examples Init.py InitGui.py scripts \
  tests || { echo "compileall failed"; exit 1; }
echo OK

echo "== icon generation deterministic =="
TMP_OUT="$(mktemp -d)"
trap 'rm -rf "$TMP_OUT"' EXIT
python3 scripts/make_icons.py "$TMP_OUT"
diff -r "$TMP_OUT/light" resources/icons/light >/dev/null \
  || { echo "icons out of sync - run scripts/make_icons.py"; exit 1; }
diff -r "$TMP_OUT/dark" resources/icons/dark >/dev/null \
  || { echo "icons out of sync - run scripts/make_icons.py"; exit 1; }
echo OK

echo "== ribbon schema validation =="
python3 - <<'EOF'
import json, os, sys
sys.path.insert(0, ".")
from opencad_ux.commands import registry, adapters
layout = registry.load_ribbon_layout()
ids = [b.id for b in layout.all_buttons()]
assert len(ids) == len(set(ids))
assert sum(len(g.buttons) for g in layout.groups) >= 40
for b in layout.all_buttons():
    assert b.label_en and b.label_zh
    assert adapters.candidates_for(b.cmd) or adapters.python_command_name(b.cmd) \
        or adapters.not_available_reason(b.cmd), b.id
    for theme in ("light", "dark"):
        p = os.path.join("resources", "icons", theme, b.icon + ".svg")
        assert os.path.isfile(p), p
print("OK: %d buttons across %d groups" % (len(ids), len(layout.groups)))
EOF
echo "ALL STATIC CHECKS PASSED"
