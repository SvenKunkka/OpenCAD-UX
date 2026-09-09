# Fixtures

`fc_commands_1.1.txt` – sorted FreeCAD command ids harvested from the
FreeCAD 1.1.3 (20260725, arm64 macOS) binaries shipped with this project's
development machine (see `scripts/harvest_commands.sh`). It is used by the
console test-suite to validate command resolution against a *real* command
set even when running headless (no GUI command table available in
FreeCADCmd). Regenerate per FreeCAD release before shipping.
