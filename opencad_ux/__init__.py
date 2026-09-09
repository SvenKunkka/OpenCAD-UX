# -*- coding: utf-8 -*-
"""OpenCAD UX - a Fusion-inspired Product Design workspace for FreeCAD.

Layout of responsibilities
--------------------------
* ``config``     - path resolution (no hard-coded user paths).
* ``prefs``      - one settings namespace, FreeCAD parameters or in-memory.
* ``logger``     - optional file logger behind the same ``debug`` switch.
* ``compat``     - FreeCAD / PySide version differences.
* ``commands``   - ribbon.json command specs, alias/fallback resolution,
                  safe execution through public FreeCAD APIs.
* ``ribbon``     - schema loading/validation + Qt ribbon widget.
* ``themes``     - original light/dark theme data, QSS/Palette builders.
* ``keymap``     - shortcut presets, conflict detection, apply/export/import.
* ``navigation`` - mouse-navigation preset detection and application.
* ``command_search`` - bilingual fuzzy command search engine + dialog.
* ``context_menu``   - selection-driven contextual actions.
* ``reference_images`` - reference-image import, attach, calibration, lock.
* ``gui``         - glue: controller that attaches/detaches UI to FreeCAD.
* ``workbench``   - the FreeCAD Python workbench that ties it together.

The GUI parts never run at import time: everything is created on demand by
``opencad_ux.workbench`` (activated workbench) or by explicit commands, so the
package stays importable from the console (FreeCADCmd) and from unit tests.
"""

__version__ = "0.1.0"
__addon_name__ = "OpenCAD UX"

# Versions that define the supported matrix.  `min` is FreeCAD >= 0.20;
# 1.0+/1.1+ receive native-style handling where available.
FREECAD_MIN = (0, 20, 0)

# internal module marker used by import tests
__opencad_ux_pkg__ = True


def version_tuple():
    return tuple(int(x) for x in str(__version__).split("."))
