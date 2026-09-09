# -*- coding: utf-8 -*-
"""Python command implementations registered into FreeCADGui.

Every command here performs its real work through the public FreeCAD python
API (see exporters.py / reference_images / execution) so the same operations
are covered by the headless test-suite.
"""

import os

from .. import logger
from ..compat import QtCore, QtGui, QtWidgets, get_gui, get_main_window  # noqa
from ..config import icon_path
from .. import __version__
from ..commands import adapters, exporters
from ..context_menu import context_actions_for
from ..reference_images import (RefImageError, create_reference_image,
                                set_transparency, set_locked, set_visibility,
                                set_world_width)
from .. import prefs


def _mw():
    return get_main_window()


def _msg(title, text, kind="info"):
    mw = _mw()
    parent = mw if mw is not None else None
    if kind == "warning":
        QtWidgets.QMessageBox.warning(parent, title, text)
    else:
        QtWidgets.QMessageBox.information(parent, title, text)


def _active_doc():
    import FreeCAD  # noqa

    return FreeCAD.ActiveDocument


def _selection():
    gui = get_gui()
    if gui is None:
        return []
    try:
        return gui.Selection.getSelection()
    except Exception:
        return []


def _run(cmd_name, **opts):
    pass


class _CommandBase(object):
    """Minimal FreeCAD python command scaffold."""
    CommandName = "OpencadUX_Base"
    MenuText = "OpenCAD UX base"
    ToolTip = ""
    IconName = "product-design"

    def GetResources(self):
        path = icon_path(self.IconName)
        return {"Pixmap": path, "MenuText": self.MenuText,
                "ToolTip": self.ToolTip or self.MenuText}

    def IsActive(self):
        return True

    def Activated(self):
        raise NotImplementedError

    def GetClassName(self):
        return "OpenCADUX_Command"


def _make_command(command_name, menu_text, tooltip, icon, activated):
    """Factory creating FreeCADGui command classes on the fly."""
    def act(self):
        activated()
    cls = type(
        command_name,
        (_CommandBase,),
        {"CommandName": command_name, "MenuText": menu_text,
         "ToolTip": tooltip, "IconName": icon, "Activated": act},
    )
    return cls


def _cmd_search():
    from ..command_search.dialog import show_command_search  # noqa

    show_command_search(parent=_mw())


def _cmd_context_menu():
    from ..command_search.dialog import _icon_provider  # noqa

    mw = _mw()
    if mw is None:
        return
    selection = _selection()
    actions = context_actions_for(selection)
    if not actions:
        return
    layout = None
    from ..commands import registry  # noqa

    layout = registry.load_ribbon_layout()
    menu = QtWidgets.QMenu(mw)
    theme = prefs.Settings().theme
    provider = _icon_provider(theme)
    menu.setObjectName("OpenCADUXContextMenu")
    for canonical in actions:
        btn = layout.by_id(canonical)
        label = btn.label_en if btn else canonical
        item = menu.addAction(label)
        icon = provider(canonical) if canonical else None
        if icon is not None:
            item.setIcon(icon)
        item.triggered.connect(
            lambda checked=False, c=canonical: _run_canonical(c))
    menu.exec_(QtGui.QCursor.pos())


def _run_canonical(canonical):
    from ..commands.execution import execute_canonical  # noqa

    res = execute_canonical(canonical)
    mw = _mw()
    if mw is not None and mw.statusBar() is not None:
        mw.statusBar().showMessage(res.message or res.status, 6000)


def _export_command(canonical, fmt, default_name, filter_str, ext):
    def act():
        doc = _active_doc()
        if doc is None:
            _msg("Export", "No active document to export.", "warning")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            _mw(), "Export %s" % fmt.upper(), default_name, filter_str)
        if not path:
            return
        if not path.lower().endswith(ext):
            path += ext
        try:
            fn = {"step": exporters.export_step, "stl": exporters.export_stl,
                  "obj": exporters.export_obj, "dxf": exporters.export_dxf}[fmt]
            selected = _selection()
            fn(doc, path, selected=selected if selected else None)
            _msg("Export", "Exported to:\n%s" % path)
        except Exception as exc:
            _msg("Export failed", str(exc), "warning")
    return act


def _cmd_import_step():
    def act():
        doc = _active_doc()
        if doc is None:
            _msg("Import STEP", "Please create/open a document first.", "warning")
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            _mw(), "Import STEP", "", "STEP files (*.step *.stp);;All files (*)")
        if not path:
            return
        try:
            exporters.import_step(path, doc=doc)
            _msg("Import STEP", "Imported into '%s'" % doc.Name)
        except Exception as exc:
            _msg("Import STEP failed", str(exc), "warning")
    return act


def _cmd_import_ref_image():
    def act():
        doc = _active_doc()
        if doc is None:
            _msg("Reference Image", "Please create/open a document first.", "warning")
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            _mw(), "Select reference image",
            "", "Images (*.png *.jpg *.jpeg);;All files (*)")
        if not path:
            return
        plane, width = _ask_plane()
        if plane is None:
            return
        try:
            world_width = None
            if width is not None and width.strip():
                world_width = float(width.strip())
            create_reference_image(doc, path, plane=plane,
                                   world_width_mm=world_width)
            _msg("Reference Image", "Attached '%s' on the %s plane.\n\n"
                 "Select the image in the tree afterwards to calibrate, "
                 "set transparency or lock it (context panel / Q)."
                 % (os.path.basename(path), plane))
        except (RefImageError, ValueError) as exc:
            _msg("Reference Image", str(exc), "warning")
    return act


def _ask_plane():
    """Ask for plane (+optional known width). Returns (plane, width_text|None)."""
    mw = _mw()
    dlg = QtWidgets.QDialog(mw)
    dlg.setWindowTitle("Attach plane")
    lay = QtWidgets.QVBoxLayout(dlg)
    combo = QtWidgets.QComboBox(dlg)
    combo.addItem("XY (top view) - XY（俯视）", "XY")
    combo.addItem("XZ (front view) - XZ（正视）", "XZ")
    combo.addItem("YZ (right view) - YZ（侧视）", "YZ")
    lay.addWidget(combo)
    width_edit = QtWidgets.QLineEdit(dlg)
    width_edit.setPlaceholderText("Known real width in mm (optional)")
    lay.addWidget(width_edit)
    box = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, dlg)
    box.accepted.connect(dlg.accept)
    box.rejected.connect(dlg.reject)
    lay.addWidget(box)
    if dlg.exec_() != QtWidgets.QDialog.Accepted:
        return None, None
    return combo.currentData(), width_edit.text()


def _cmd_calibrate_ref_image():
    def act():
        doc = _active_doc()
        sel = _selection()
        imgs = [o for o in sel if (getattr(o, "TypeId", "") == "Image::ImagePlane")]
        if doc is None or not imgs:
            _msg("Calibrate", "Select an ImagePlane reference image first.",
                 "warning")
            return
        obj = imgs[0]
        text, ok = QtWidgets.QInputDialog.getText(
            _mw(), "Calibrate width", "Known real width of the image (mm):")
        if not ok or not text.strip():
            return
        try:
            width = float(text.strip())
            set_world_width(obj, width)
            _msg("Calibrate", "Image width set to %.2f mm.\n\nFor two-point "
                 "calibration use the context panel (select the image)."
                 % width)
        except (ValueError, RefImageError) as exc:
            _msg("Calibrate", str(exc), "warning")
    return act


def _inspection_report(kind):
    def act():
        sel = _selection()
        if not sel:
            _msg("Inspect", "Select at least one shape object.", "warning")
            return
        try:
            if kind == "bbox":
                text = exporters.report_bounding_box(sel)
            elif kind == "mass":
                text = exporters.report_mass_properties(sel)
            else:
                text = exporters.report_interference(sel)
            _msg("OpenCAD UX - Inspect", text)
        except Exception as exc:
            _msg("Inspect", str(exc), "warning")
    return act


def _cmd_settings():
    def act():
        try:
            from ..preferences.page import show_settings  # noqa

            show_settings(parent=_mw())
        except Exception as exc:
            logger.debug("settings dialog failed: %s", exc)
            _msg("OpenCAD UX", "Settings dialog error: %s" % exc, "warning")
    return act


def _cmd_about():
    def act():
        _msg("OpenCAD UX", "OpenCAD UX %s\n\n"
             "A Fusion-inspired Product Design workspace for FreeCAD.\n"
             "Open source - GPL-3.0-or-later." % __version__)
    return act


def _cmd_gui_selftest():
    def act():
        try:
            from ..gui.selftest import run_gui_selftest  # noqa

            report = run_gui_selftest()
            _msg("OpenCAD UX self-test", report.get("summary", "done"))
        except Exception as exc:
            _msg("Self-test", "Failed: %s" % exc, "warning")
    return act


# ---------------------------------------------------------------------------
# command classes we register (name -> factory)
# ---------------------------------------------------------------------------

def build_command_classes():
    """Return {command_name: class} for every python command we register."""
    def cls(name, menu, tip, icon, fn):
        return _make_command(name, menu, tip, icon, fn)

    classes = {
        "OpencadUX_CommandSearch": cls("OpencadUX_CommandSearch",
                                       "OpenCAD UX: Command Search",
                                       "Open the bilingual command search (S)",
                                       "search", _cmd_search),
        "OpencadUX_ContextMenu": cls("OpencadUX_ContextMenu",
                                     "OpenCAD UX: Context Actions",
                                     "Context actions for the selection (Q)",
                                     "context", _cmd_context_menu),
        "OpencadUX_Settings": cls("OpencadUX_Settings",
                                  "OpenCAD UX Settings...",
                                  "OpenCAD UX preferences", "settings",
                                  _cmd_settings),
        "OpencadUX_About": cls("OpencadUX_About", "About OpenCAD UX",
                               "About OpenCAD UX", "product-design",
                               _cmd_about),
        "OpencadUX_RunGuiSelftest": cls(
            "OpencadUX_RunGuiSelftest", "OpenCAD UX: Run GUI self-test",
            "Run the GUI self-test and write a report",
            "selftest", _cmd_gui_selftest),
        "OpencadUX_ImportReferenceImage": cls(
            "OpencadUX_ImportReferenceImage", "Import Reference Image...",
            "Import a product reference image onto a construction plane",
            "import_ref_image", _cmd_import_ref_image),
        "OpencadUX_CalibrateReferenceImage": cls(
            "OpencadUX_CalibrateReferenceImage", "Calibrate Reference Image",
            "Scale a reference image to a known real-world width",
            "calibrate", _cmd_calibrate_ref_image),
        "OpencadUX_ImportStep": cls("OpencadUX_ImportStep", "Import STEP...",
                                    "Import a STEP file", "import_step",
                                    _cmd_import_step),
        "OpencadUX_ExportStep": cls("OpencadUX_ExportStep", "Export STEP...",
                                    "Export shapes to STEP", "export_step",
                                    _export_command("step", "step",
                                                    "model.step",
                                                    "STEP (*.step *.stp)",
                                                    ".step")),
        "OpencadUX_ExportStl": cls("OpencadUX_ExportStl", "Export STL...",
                                   "Export shapes to STL mesh",
                                   "export_stl",
                                   _export_command("stl", "stl", "model.stl",
                                                   "STL (*.stl)", ".stl")),
        "OpencadUX_ExportObj": cls("OpencadUX_ExportObj", "Export OBJ...",
                                   "Export shapes to OBJ mesh", "export_obj",
                                   _export_command("obj", "obj", "model.obj",
                                                   "OBJ (*.obj)", ".obj")),
        "OpencadUX_ExportDxf": cls("OpencadUX_ExportDxf", "Export DXF...",
                                   "Export 2D geometry to DXF", "export_dxf",
                                   _export_command("dxf", "dxf", "drawing.dxf",
                                                   "DXF (*.dxf)", ".dxf")),
        "OpencadUX_BoundingBox": cls(
            "OpencadUX_BoundingBox", "Bounding Box",
            "Report bounding boxes of the selection", "bounding_box",
            _inspection_report("bbox")),
        "OpencadUX_MassProperties": cls(
            "OpencadUX_MassProperties", "Mass Properties",
            "Volume / area / mass of the selection", "mass_properties",
            _inspection_report("mass")),
        "OpencadUX_Interference": cls(
            "OpencadUX_Interference", "Interference Check",
            "Detect overlapping solids", "interference",
            _inspection_report("interf")),
        "OpencadUX_MoveFace": cls(
            "OpencadUX_MoveFace", "Move Face",
            "Move a face (not available through FreeCAD public API)",
            "move_face",
            lambda: _msg("Move Face", adapters.not_available_reason("move_face"),
                         "warning")),
        "OpencadUX_OffsetFace": cls(
            "OpencadUX_OffsetFace", "Offset Face",
            "Offset a face (not available through FreeCAD public API)",
            "offset_face",
            lambda: _msg("Offset Face", adapters.not_available_reason("offset_face"),
                         "warning")),
    }
    return classes


def register_all(gui=None):
    """Register every python command; call once from InitGui/workbench."""
    gui = gui or get_gui()
    if gui is None:
        return 0
    count = 0
    for name, cls in build_command_classes().items():
        try:
            if hasattr(gui, "addCommand"):
                gui.addCommand(name, cls())
            count += 1
        except Exception as exc:
            logger.debug("register command %s failed: %s", name, exc)
    return count
