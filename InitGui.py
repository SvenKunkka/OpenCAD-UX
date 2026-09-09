# -*- coding: utf-8 -*-
"""OpenCAD UX - InitGui (GUI entry).

The FreeCAD workbench loader may evaluate this file *partially* during
discovery (class + nearby statements only), so this file keeps all side
effects behind functions: registration and command installation happen from
``OpenCADUXWorkbench.Activated`` (which runs after the module is fully
imported) and are idempotent.
"""

import FreeCADGui as Gui


class OpenCADUXWorkbench(Gui.Workbench):
    MenuText = "Product Design (OpenCAD UX)"
    ToolTip = ("Fusion-inspired product design workspace for "
               "consumer-electronics mechanical design")
    Icon = ""

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        try:
            from opencad_ux import workbench

            workbench.install_once()
        except Exception:
            pass
        return True

    def Activated(self):
        try:
            from opencad_ux import workbench

            workbench.install_once()
            workbench.activate()
        except Exception:
            pass

    def Deactivated(self):
        try:
            from opencad_ux import workbench

            workbench.deactivate()
        except Exception:
            pass
