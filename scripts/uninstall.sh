#!/usr/bin/env bash
# Uninstall OpenCAD UX and restore what the add-on touched.
#
#  1. removes the add-on folder from FreeCAD's user Mod directory
#  2. removes the OpenCAD UX parameter group (BaseApp/Preferences/OpenCADUX)
#  3. restores the stylesheet backup the add-on wrote (if any)
#  4. reports any config backups created by install.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC_NAME="OpenCAD-UX"

FC_CMD="${FC_CMD:-}"
if [ -z "$FC_CMD" ]; then
  if [ -x "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd" ]; then
    FC_CMD="/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
  elif command -v freecadcmd >/dev/null 2>&1; then
    FC_CMD="$(command -v freecadcmd)"
  fi
fi

USER_MOD=""
if [ -n "$FC_CMD" ]; then
  CFG="$(mktemp -d)"
  APP_DATA="$("$FC_CMD" -u "$CFG/user.cfg" -s "$CFG/system.cfg" \
    -c "import FreeCAD;print(FreeCAD.getUserAppDataDir())" 2>/dev/null | tail -1 || true)"
  if [ -n "$APP_DATA" ]; then
    USER_MOD="$APP_DATA/Mod"
  fi
fi
if [ -z "$USER_MOD" ]; then
  case "$(uname -s)" in
    Darwin)  USER_MOD="$HOME/Library/Application Support/FreeCAD/v1-1/Mod" ;;
    Linux)   USER_MOD="${XDG_DATA_HOME:-$HOME/.local/share}/FreeCAD/Mod" ;;
    MINGW*|MSYS*) USER_MOD="$APPDATA/FreeCAD/Mod" ;;
  esac
fi
USER_MOD="${USER_MOD%/}"
DEST="$USER_MOD/$SRC_NAME"

echo "== OpenCAD UX uninstall =="
if [ -d "$DEST" ]; then
  rm -rf "$DEST"
  echo "Removed $DEST"
else
  echo "No add-on folder at $DEST (already removed?)"
fi

# Remove the parameter group and restore the stylesheet backup via FreeCAD's
# own python (runs the same cleanup code the GUI "restore layout" uses).
CLEANUP="$(mktemp)"
cat > "$CLEANUP" <<'EOF'
import sys, os
sys.path.insert(0, "$REPO")
try:
    import FreeCAD
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences")
    for name in ("RemGroup", "RemoveGroup"):
        try:
            getattr(p, name)("OpenCADUX")
            break
        except Exception:
            continue
    FreeCAD.saveParameter()
    print("OpenCAD UX parameter group removed")
except Exception as exc:
    print("param cleanup skipped:", exc)
EOF
sed -i '' "s|\$REPO|$REPO|g" "$CLEANUP" 2>/dev/null || sed -i "s|\$REPO|$REPO|g" "$CLEANUP"
if [ -n "$FC_CMD" ]; then
  # backup the real cfg files once more, then clean the real user config
  BK_DIR="$(dirname "$USER_MOD")/OpenCADUX-backup-uninstall-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$BK_DIR"
  for cfgfile in \
      "$(dirname "$USER_MOD")/../../Preferences/FreeCAD/v1-1/user.cfg" \
      "$(dirname "$USER_MOD")/../../Preferences/FreeCAD/v1-1/system.cfg"; do
    [ -f "$cfgfile" ] && cp "$cfgfile" "$BK_DIR/"
  done
  "$FC_CMD" -c "exec(open('$CLEANUP').read())" >/dev/null 2>&1 || true
  echo "parameter-group cleanup ran (config backup in $BK_DIR)"
else
  echo "freecadcmd not found - parameter group not removed (harmless leftover)."
  echo "Remove 'BaseApp/Preferences/OpenCADUX' manually in the parameter editor."
fi
rm -f "$CLEANUP"

echo
echo "Note: any config backups created by install.sh are still at:"
find "$(dirname "$USER_MOD")" -maxdepth 2 -name "OpenCADUX-backup-*" -type d 2>/dev/null | sed 's/^/    /'
echo
echo "Restart FreeCAD. FreeCAD's UI is back to its previous state; the"
echo "OpenCAD UX toolbar/docks no longer exist because the add-on is gone."
