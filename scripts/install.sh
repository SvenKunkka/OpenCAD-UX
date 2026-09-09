#!/usr/bin/env bash
# Install OpenCAD UX into FreeCAD's user Mod directory with a config backup.
#
# - never hard-codes user paths: it asks the running FreeCAD where its user
#   data dir is (or falls back to the standard location for the OS)
# - backs up FreeCAD user/system.cfg BEFORE writing anything
# - refuses to overwrite an existing different OpenCAD-UX install without
#   telling you (backup first, then replace)
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VER="0.1.0"
SRC_NAME="OpenCAD-UX"

msg(){ printf '\n== %s ==\n' "$*"; }

# --- find FreeCAD command & user data dir -------------------------------
FC_CMD="${FC_CMD:-}"
if [ -z "$FC_CMD" ]; then
  if [ -x "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd" ]; then
    FC_CMD="/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
  elif command -v freecadcmd >/dev/null 2>&1; then
    FC_CMD="$(command -v freecadcmd)"
  else
    FC_CMD=""
  fi
fi

USER_MOD=""
CFG_DIR=""
if [ -n "$FC_CMD" ]; then
  CFG="$(mktemp -d)"
  trap 'rm -rf "$CFG"' EXIT
  INFO="$("$FC_CMD" -u "$CFG/user.cfg" -s "$CFG/system.cfg" \
    -c "import FreeCAD,os;print(FreeCAD.getUserAppDataDir());print(os.path.dirname(FreeCAD.ConfigGet('UserParameter')))" 2>/dev/null | tail -2 || true)"
  APP_DATA="$(echo "$INFO" | sed -n '1p')"
  CFG_DIR="$(echo "$INFO" | sed -n '2p')"
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
msg "Installing OpenCAD UX $VER into: $USER_MOD"

if [ ! -d "$USER_MOD" ]; then
  msg "Creating Mod dir (existing FreeCAD config is not modified)"
  mkdir -p "$USER_MOD"
fi

# --- backup the FreeCAD config files (only what FreeCAD itself writes) ---
BK_ROOT="$(dirname "$USER_MOD")"
BK_DIR="$BK_ROOT/OpenCADUX-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BK_DIR"
for cfgfile in "$CFG_DIR/user.cfg" "$CFG_DIR/system.cfg"; do
  if [ -n "${CFG_DIR:-}" ] && [ -f "$cfgfile" ]; then
    cp "$cfgfile" "$BK_DIR/" && msg "$(basename "$cfgfile") backed up -> $BK_DIR"
  fi
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) install of OpenCAD-UX $VER" > "$BK_DIR/README.txt"

# --- copy the add-on -------------------------------------------------------
DEST="$USER_MOD/$SRC_NAME"
if [ -e "$DEST" ]; then
  if [ -f "$DEST/package.xml" ] && grep -q "<name>OpenCAD UX</name>" "$DEST/package.xml"; then
    msg "OpenCAD UX is already installed; moving it to a timestamped backup"
    mv "$DEST" "$DEST.prev-$(date +%Y%m%d-%H%M%S)"
  else
    echo "ERROR: '$DEST' exists and is not an OpenCAD UX install." >&2
    echo "Move it away manually, then rerun." >&2
    exit 3
  fi
fi
mkdir -p "$DEST"
for item in Init.py InitGui.py package.xml opencad_ux resources examples LICENSE \
            README.md README.zh-CN.md CHANGELOG.md; do
  cp -R "$REPO/$item" "$DEST/"
done
msg "Installed. Restart FreeCAD and switch workbench to:"
echo "    Product Design (OpenCAD UX)"
echo
echo "Backups: $BK_DIR"
echo "To uninstall later: bash $REPO/scripts/uninstall.sh"
