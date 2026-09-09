# License & attribution

## Code license

All code in this repository is licensed under
**GNU General Public License v3.0 or later** — see [LICENSE](../LICENSE).

This project is an independent add-on for FreeCAD. FreeCAD itself is
LGPL-2.0-or-later; nothing from FreeCAD's codebase is copied into this
repository — FreeCAD functionality is invoked through its **public Python API
and standard commands at runtime**.

## Icons

Every icon under `resources/icons/{light,dark}` is an **original work** of
this project: glyphs are geometric primitives defined in
`scripts/make_icons.py` and rendered to SVG at build time. No Autodesk,
Fusion 360, or other proprietary icon assets are used or derived from.

License for the icon SVGs: GPL-3.0-or-later (same as the project).

## Referenced projects / interaction patterns (not copied)

The following projects/patterns were studied for *interaction logic only*;
none of their code, icons, trademarks, or visual assets are included:

| Reference | What was studied | License of the reference (not bundled) |
|---|---|---|
| Autodesk Fusion 360 | Ribbon grouping concepts, command search, two-point calibration workflow, key ideas (generic CAD UX patterns) | Proprietary (not used) |
| FreeCAD | Public Python API, command ids, parameter system, `Image::ImagePlane` | LGPL-2.0-or-later |
| FreeCAD-Ribbon (APEbbers) | Demonstrates that global ribbon docks are feasible | GPL-3.0 (not copied) |

## Third-party runtime dependencies

None. OpenCAD UX only depends on what FreeCAD already ships (FreeCAD,
FreeCADGui, PySide2/PySide6, Part/PartDesign/Sketcher/Mesh/Import/Draft
modules).

## Trademarks

Fusion 360 and Autodesk are trademarks of Autodesk, Inc. They are referenced
here only to describe generic interaction patterns and compatibility goals,
and OpenCAD UX is not affiliated with or endorsed by Autodesk.
