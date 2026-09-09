#!/usr/bin/env bash
# Build the distributable add-on ZIP: OpenCAD-UX-<version>.zip
# The zip root contains Init.py / InitGui.py / package.xml / opencad_ux/ ...
# so Addon Manager and manual installs both work.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
VER="$(grep -m1 '<version>' package.xml | sed -E 's/.*<version>([^<]+)<.*/\1/')"
DIST="dist"
OUT="$DIST/OpenCAD-UX-$VER.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
PKG="$STAGE/OpenCAD-UX"
mkdir -p "$PKG"

for item in Init.py InitGui.py package.xml opencad_ux resources examples LICENSE \
            README.md README.zh-CN.md CONTRIBUTING.md SECURITY.md CHANGELOG.md; do
  [ -e "$REPO/$item" ] && cp -R "$REPO/$item" "$PKG/"
done

mkdir -p "$DIST"
(cd "$STAGE" && zip -qr "$REPO/$OUT" OpenCAD-UX)
echo "created $OUT"
unzip -l "$OUT" | tail -3
