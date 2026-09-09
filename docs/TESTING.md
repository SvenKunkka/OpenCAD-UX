# OpenCAD UX test report

Report produced by the automated test-suite. `git log`/timestamp tells you
which revision this refers to.

## Summary

| Suite | Scope | Result |
|---|---|---|
| `scripts/run_pure_tests.sh` | 36 unit tests, no FreeCAD | see below |
| `scripts/run_console_tests.sh` | 25 integration tests inside real FreeCADCmd 1.1.3 | see below |
| `scripts/check_static.sh` | syntax + icon determinism + schema | see below |
| `scripts/run_examples.sh` | 3 example models + STEP/STL export | see below |
| GUI self-test | run inside FreeCAD GUI (`OpencadUX_RunGuiSelftest`) | see below |

## Pure python tests (no FreeCAD needed)

Coverage:

- ribbon schema: 7 groups, 53 buttons, bilingual labels, unique ids,
  keywords include Chinese, every icon file exists for light+dark
- adapters: modern-first and legacy-fallback command resolution,
  every button has an executable path or is documented-unavailable
- keymap: preset loads, no internal conflicts, per-platform `mod` expansion,
  external conflict detection
- search engine: EN `chamfer`, 中文 `倒角` `外壳` `拉伸` `合并`, recents
  boost, disabled filtering
- context decision: sketch / solid / multi-solid / body / image / empty
- themes: light+dark present, QSS strings non-trivial
- reference image math: PNG size parser, mm-per-pixel calibration, errors
- navigation mapping: Revit fallback, style class strings, docs list

## FreeCAD console tests (real FreeCADCmd 1.1.3)

- package imports + resource paths
- settings param-group round trip; config-file backup machinery
- parametric flow: sketch → pad → edit pad length (history recompute,
  volume 1.5×) → circle pocket (hole) → OCC fillet → OCC thickness →
  save/reopen `.FCStd`
- exporters: STEP (round-trip import), STL, OBJ file sizes; bounding box /
  mass / interference reports (clear + overlapping)
- reference images: create on XZ plane, width calibration 80→160 px, mm-per-px
  2.0, opacity, lock semantics, error paths
- example models: keyboard / mouse / enclosure build valid solids > 500 mm³,
  save .FCStd
- navigation parameter write/read; command resolution against the harvested
  command-id snapshot (FreeCAD 1.1.3) incl. every ribbon button resolving or
  documented-unavailable (only `move_face`, `offset_face`)

## GUI verification status

On the development machine a known Qt/macOS accessibility bug (documented in
`docs/DEVELOPMENT.md`) can crash FreeCAD's GUI when an external AX service is
active, so *pixel automation* of the GUI was not reliable here. Instead:

- the GUI layer is exercised by the **in-GUI self-test command**
  (`OpencadUX_RunGuiSelftest`) which builds the ribbon widget, themes,
  search, reference images, keymap and command registration inside a real
  FreeCAD GUI session and writes
  `gui_selftest_report.json` (+ screenshot) under the FreeCAD user data dir;
- users/CI on unaffected machines should run that command and paste the
  report into issues.

This is the honest boundary of automated GUI verification for the MVP.

## Result bookkeeping

Last full run on the development machine (macOS 26.6 arm64, FreeCAD 1.1.3
2026-07 build, console `freecadcmd` with isolated `-u/-s` configs):

| Suite | Result |
|---|---|
| pure (`run_pure_tests.sh`) | **OK – 36/36 passed** |
| console (`run_console_tests.sh`) | **OK – 25/25 passed** |
| static (`check_static.sh`) | **OK** (compileall, icon determinism, ribbon schema) |
| examples (`run_examples.sh`) | **OK – 3/3 models + STEP/STL exported** |
| GUI self-test (`OpencadUX_RunGuiSelftest`) | **not executed on this host** — the documented Qt/macOS accessibility crash (see `docs/DEVELOPMENT.md`) makes GUI pixel automation unreliable here; the in-GUI self-test command is provided for healthy machines. UI *preview* images in `docs/screenshots/` are rendered from the real config/icons via `scripts/make_preview.py` (headless Chrome). |
