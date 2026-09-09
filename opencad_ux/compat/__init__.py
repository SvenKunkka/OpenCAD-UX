# -*- coding: utf-8 -*-
"""Compatibility helpers: Qt binding selection and FreeCAD feature checks.

FreeCAD history:
* <= 0.20 : PySide2 / Qt5
* 0.21    : PySide2 / Qt5 (Qt6 builds exist but are rare)
* 1.0+    : PySide6 / Qt6, with a ``PySide`` alias kept for addons

We always try the real bindings first and fall back to the ``PySide`` alias
FreeCAD installs, so the same code path serves GUI and console runs.
"""

from .. import logger


def _import_pyside():
    """Return (QtCore, QtGui, QtWidgets) or (None, None, None)."""
    candidates = ()
    try:
        # FreeCAD 1.x ships PySide6 and aliases it as PySide
        import PySide6  # noqa

        candidates = ("PySide6", "PySide", "PySide2")
    except Exception:
        try:
            import PySide2  # noqa

            candidates = ("PySide2", "PySide")
        except Exception:
            try:
                import PySide  # noqa

                candidates = ("PySide",)
            except Exception:
                return None, None, None
    for name in candidates:
        try:
            mod = __import__(name, fromlist=["QtCore", "QtGui", "QtWidgets"])
            return (
                getattr(mod, "QtCore", None),
                getattr(mod, "QtGui", None),
                getattr(mod, "QtWidgets", None),
            )
        except Exception:
            continue
    return None, None, None


QtCore, QtGui, QtWidgets = _import_pyside()


def qt_binding_name():
    if QtCore is None:
        return None
    return QtCore.__name__.rsplit(".", 1)[0]


def is_qt6():
    if QtCore is None:
        return False
    name = qt_binding_name()
    if name == "PySide6":
        return True
    if name == "PySide2":
        return False
    # FreeCAD 1.x aliases PySide6 as ``PySide``; PySide2/0.21 also aliases
    # itself as PySide, so fall back to the enum style instead.
    try:
        return not hasattr(QtCore.Qt, "Key_Escape")
    except Exception:
        return False


def qapplication_available():
    return QtWidgets is not None


def translate(context, text, disambig=None):
    """FreeCAD's translate() when available (GUI), identity fallback."""
    try:
        import FreeCAD

        return FreeCAD.Qt.translate(context, text, disambig)
    except Exception:
        return text


# --- FreeCAD version facts -------------------------------------------------

def fc_version_tuple():
    try:
        import FreeCAD

        v = [int(p) for p in FreeCAD.Version()[0:3] if p.isdigit()]
        return tuple(v[:3])
    except Exception:
        return (0, 0, 0)


def fc_major_minor():
    v = fc_version_tuple()
    return (v[0], v[1]) if len(v) >= 2 else (0, 0)


def is_fc1():
    return fc_version_tuple() >= (1, 0, 0)


def gui_importable():
    """True when FreeCADGui can be imported (GUI process only)."""
    try:
        import FreeCADGui  # noqa

        return True
    except Exception:
        return False


def get_gui():
    """Return the FreeCADGui module or None (console)."""
    if not gui_importable():
        return None
    import FreeCADGui

    return FreeCADGui


def get_main_window():
    gui = get_gui()
    if gui is None:
        return None
    try:
        return gui.getMainWindow()
    except Exception:
        return None
