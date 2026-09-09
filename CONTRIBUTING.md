# Contributing to OpenCAD UX

Thanks for helping! Please keep the project's design rules in mind:

## Ground rules

1. **Everything must run on stock FreeCAD through public APIs or standard
   commands.** No screen-coordinate clicking, no private parameter hacking,
   no patched FreeCAD binaries in the default path.
2. **Never break an existing user setup.** Any change that touches FreeCAD
   preferences must go through `opencad_ux.prefs` and record a restore path
   (see `themes.apply`, `navigation`).
3. **Config over code.** New ribbon buttons/groups go into
   `resources/ribbon.json` + `scripts/make_icons.py` glyphs first; code only
   adds the command mapping in `opencad_ux/commands/adapters.py`.
4. **Original assets only.** Do not copy Fusion 360 (or any proprietary)
   icons, names, or visual assets. New icons must be authored as glyph
   definitions in `scripts/make_icons.py`.
5. **Cross-version discipline.** When you touch a command id, add the newest
   id first and keep legacy candidates (see `adapters.NATIVE`).
6. **Console-safe imports.** GUI modules must not be imported at module level
   of console-safe modules. Use the `compat` lazy helpers when in doubt.
7. **Every feature ships with a test**: pure logic tests under `tests/pure/`,
   FreeCAD integration under `tests/fc/`, GUI checks inside the in-GUI
   self-test (`opencad_ux/gui/selftest.py`).

## Workflow

1. Open an issue describing the change first (feature or bug + FreeCAD
   version and OS).
2. Branch from `main`, keep commits focused, conventional style:
   `feat(ribbon): ...`, `fix(keymap): ...`, `test(examples): ...`.
3. Run locally before pushing:

```bash
bash scripts/run_pure_tests.sh
bash scripts/run_console_tests.sh    # needs FreeCADCmd on PATH or /Applications
bash scripts/run_examples.sh
bash scripts/check_static.sh
```

4. Open a pull request; CI runs the pure + static checks automatically and
   the FreeCAD-console suite when a runner with FreeCAD is available.

## Testing FreeCAD versions

`adapters.resolve_canonical` resolves against the live command table in the
GUI, or against `tests/fixtures/fc_commands_1.1.txt` in the console suite.
When adding a new FreeCAD major, harvest its command ids
(`strings` on the GUI libs, see `docs/DEVELOPMENT.md`) into a new fixture and
map your expectations there.

## Code of conduct

Be respectful; this project values clear, evidence-based discussion.
