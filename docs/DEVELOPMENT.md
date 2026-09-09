# Development notes

## Environment used for this MVP

- macOS 26.6 (arm64), FreeCAD **1.1.3** official build at
  `/Applications/FreeCAD.app` (bundled conda Python 3.11.14, PySide6/Qt6).
- Headless CLI: `.../Contents/Resources/bin/freecadcmd`.

### Running FreeCAD headlessly on this machine

FreeCADCmd never opens windows; GUI processes can run on the Qt **offscreen**
platform to avoid the known macOS Qt accessibility crash caused by an
external AX scanner (`SkyComputerUseService`) documented in this repo's
sibling analysis (`FreeCAD-macOS崩溃-根因分析与修复方案.md`):

```bash
QT_QPA_PLATFORM=offscreen /Applications/FreeCAD.app/Contents/MacOS/FreeCAD \
  -u <tmp>/user.cfg -s <tmp>/system.cfg --disable-addon FreeCAD-Ribbon
```

Important lessons (verified empirically):

- Always pass **fresh `-u`/`-s` cfg paths**: killed processes can truncate a
  cfg file, and the real user cfg silently loads add-ons such as
  FreeCAD-Ribbon which restructure the UI.
- `$HOME` is **ignored** for FreeCAD's user data dir on macOS, and
  `-M`-style extra module roots are not scanned for startup module loading;
  the console test-suite therefore imports modules through `-P` + `runpy`
  rather than FreeCAD's own module discovery.
- `-t` GUI test enumeration runs add-on `InitGui.py` but custom
  `Test*.py` names under add-on dirs segfault on this build; the supported
  GUI verification path is the add-on's own **in-GUI self-test command**
  (`OpencadUX_RunGuiSelftest`).

## Repo layout

```
Init.py, InitGui.py, package.xml     # FreeCAD add-on entry points
opencad_ux/
  workbench.py                       # activation glue (plain functions)
  prefs.py config.py logger.py       # settings/paths/debug
  compat/                            # PySide2/6 + FreeCADGui lazy access
  commands/  adapters,registry,execution,python_commands,exporters
  ribbon/widgets.py                  # Qt ribbon
  themes/                            # data + qss + apply
  keymap/  presets,conflicts,dispatcher
  navigation/                        # mouse navigation presets
  command_search/ engine,dialog
  context_menu/  __init__,panel
  reference_images/                  # workflow + calibration math
  preferences/page.py                # settings dialog
  gui/ controller,context_panel,selftest
resources/  ribbon.json keymap.json themes/ icons/{light,dark}
examples/    model_lib + 3 example models + build_all
tests/       pure/*  fc/*  fixtures/*
scripts/     run_* check_static install uninstall make_zip make_icons
```

## Adding a ribbon button (3 steps)

1. `resources/ribbon.json` – new button entry (labels EN/ZH, keywords incl.
   Chinese, icon id).
2. `scripts/make_icons.py` – glyph for the icon id (or extend an existing
   one), then run `python3 scripts/make_icons.py`.
3. `opencad_ux/commands/adapters.py` – native candidates or python fallback
   mapping; add a test in `tests/pure` and (when model-level) `tests/fc`.

Run `scripts/check_static.sh` afterwards – it fails when the JSON, glyphs and
generated SVGs get out of sync.

## Harvesting the FreeCAD command-id fixture

The console suite validates command resolution against a snapshot of real
command ids (`tests/fixtures/fc_commands_1.1.txt`). Regenerate per FreeCAD
release with:

```bash
for L in .../lib/{SketcherGui,PartDesignGui,PartGui,libFreeCADGui}.so/dylib; do
  strings "$L";
done | grep -oE '^(Sketcher|PartDesign|Part|Std|Image)_[A-Za-z0-9_]+' | sort -u \
  > tests/fixtures/fc_commands_<version>.txt
```

## Running the GUI self-test inside FreeCAD

Inside a running FreeCAD GUI (menu or python console):

```python
import FreeCADGui
FreeCADGui.runCommand("OpencadUX_RunGuiSelftest")
```

The report lands in the FreeCAD user data dir under
`OpenCADUX/gui_selftest_report.json` and a screenshot is saved next to it.
