# -*- coding: utf-8 -*-
"""OpenCAD UX - FreeCAD addon module entry point (console-safe).

This file must never import FreeCADGui or create Qt objects at module level:
it is executed by the console (FreeCADCmd) as well as by the GUI.
"""

import os as _os

FreeCADModule = __name__

# Version is owned by opencad_ux/__init__.py; expose it here lazily to keep a
# single source of truth without importing the whole package.
__version__ = "0.1.0"


def _package_root():
    return _os.path.dirname(_os.path.abspath(__file__))
