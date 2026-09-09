# -*- coding: utf-8 -*-
"""The FreeCAD Python workbench that assembles the Product Design workspace.

Only imported from the GUI (InitGui.py). Everything here is idempotent so
activating the workbench twice, or disabling the addon, never corrupts the
FreeCAD session.
"""

from . import __version__, logger, prefs
from .compat import QtCore, get_gui, get_main_window  # noqa

_state = {"controller": None, "theme_applied": False, "nav_backed": False,
          "installed": False}


def install_once():
    """Idempotent install of python commands + workbench registration + a
    GUI self-test schedule used by automated verification."""
    if _state["installed"]:
        return True
    try:
        from .compat import get_gui  # noqa

        gui = get_gui()
        if gui is None:
            return False
        from .commands import python_commands  # noqa

        python_commands.register_all(gui)
        known = set(gui.listWorkbenches()) if hasattr(gui, "listWorkbenches") else set()
        if "OpenCADUXWorkbench" not in known:
            # executed lazily from Activated on later switches; the GUI
            # discovers the class from InitGui metadata already
            pass
        _state["installed"] = True
    except Exception as exc:
        logger.debug("install_once failed: %s", exc)
        return False
    _maybe_schedule_autorun()
    return True


def _maybe_schedule_autorun():
    """GUI-verification hook (param GuiAutoSelftest=1): run the GUI self-test
    ~2s after activation then close FreeCAD.  Never active for normal users."""
    try:
        from . import prefs as _p

        store = _p.get_store()
        if not store.GetBool("GuiAutoSelftest", False):
            return
    except Exception:
        return
    try:
        from .compat import QtCore  # noqa

        QtCore.QTimer.singleShot(2000, _run_autorun_selftest)
    except Exception:
        pass


def _run_autorun_selftest():
    try:
        from .gui.selftest import run_gui_selftest  # noqa

        report = run_gui_selftest(autoclose=True)
        try:
            print("OPENCADUX_AUTOSELFTEST %s" % report.get("summary", "done"))
        except Exception:
            pass
    except Exception as exc:  # pragma: no cover
        try:
            print("OPENCADUX_AUTOSELFTEST FAILED %r" % (exc,))
        except Exception:
            pass


def _controller():
    from .gui.controller import UxController  # noqa

    if _state["controller"] is None:
        _state["controller"] = UxController()
    return _state["controller"]


def ui_language():
    """Language used for OpenCAD UX labels: 'en' | 'zh'."""
    try:
        s = prefs.Settings()
        override = s.get_string(prefs.K["language_override"], "")
        if override in ("en", "zh"):
            return override
    except Exception:
        pass
    try:
        import FreeCAD  # noqa

        p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/General")
        lang = p.GetString("Language", "")
        if "hinese" in lang:
            return "zh"
    except Exception:
        pass
    return "en"


def activate():
    """Runs when the Product Design workbench is activated."""
    logger.debug("workbench activate (v%s)", __version__)
    _apply_session_theme()
    ctrl = _controller()
    ctrl.attach()
    ctrl.attach_context_panel()
    visible = prefs.Settings().get_bool(prefs.K["context_panel_visible"], False)
    if ctrl.context_dock is not None:
        ctrl.context_dock.setVisible(visible)
    ctrl.install_dispatcher()
    ctrl.set_dispatcher_active(True)
    _apply_nav_preset()
    return True


def deactivate():
    """Runs when the user leaves the Product Design workbench."""
    ctrl = _state.get("controller")
    if ctrl is not None:
        ctrl.set_dispatcher_active(False)
        ctrl.set_ribbon_visible(False)
    logger.debug("workbench deactivate (ui hidden, not destroyed)")


def rebuild_ui():
    """Re-attach UI after settings changes (sizes/theme/groups/language)."""
    ctrl = _controller()
    # detach docks and rebuild from current prefs
    mw = get_main_window()
    ctrl.detach()
    if mw is not None:
        ctrl.attach(mw)
    rebuild_dispatcher()


def rebuild_dispatcher():
    ctrl = _controller()
    app = QtCore.QCoreApplication.instance() if QtCore is not None else None
    ctrl.remove_dispatcher()
    ctrl.install_dispatcher()
    ctrl.set_dispatcher_active(True)


def disable_ux(full=False):
    """Remove OpenCAD UX UI and restore FreeCAD appearance.

    Used by 'restore default layout' and by the uninstaller (via a small
    python script that runs inside FreeCADGui).
    """
    ctrl = _state.get("controller")
    if ctrl is not None:
        ctrl.remove_dispatcher()
        ctrl.detach()
        ctrl.detach_context_panel()
    try:
        from .themes import apply as ta  # noqa

        ta.restore_previous()
    except Exception as exc:
        logger.debug("theme restore failed: %s", exc)
    if full:
        try:
            prefs.Settings().reset_all()
        except Exception:
            pass
    return True


# ---------------------------------------------------------------------------
# Workbench class
#
# The concrete class must subclass FreeCADGui.Workbench, which is only
# importable in a GUI session.  InitGui.py therefore defines the class and
# delegates every behaviour to the plain functions of this module.
# ---------------------------------------------------------------------------

def wb_icon():
    from .config import icon_path  # noqa

    return icon_path("product-design")


WB_MENU_TEXT = "Product Design (OpenCAD UX)"
WB_TOOLTIP = ("Fusion-inspired product design workspace for "
              "consumer-electronics mechanical design")


# ---------------------------------------------------------------------------
# session helpers
# ---------------------------------------------------------------------------

def _apply_session_theme():
    if _state["theme_applied"]:
        return
    try:
        from .themes import apply as ta  # noqa

        s = prefs.Settings()
        ta.apply_theme(s.theme, remember=True)
        _state["theme_applied"] = True
    except Exception as exc:
        logger.debug("session theme not applied: %s", exc)


def _apply_nav_preset():
    s = prefs.Settings()
    preset = s.get_string(prefs.K["nav_preset"], "")
    if not preset:
        return
    try:
        from . import navigation  # noqa

        prev = navigation.current_style()
        if prev and not s.get_string(prefs.K["nav_previous"], ""):
            s.set_string(prefs.K["nav_previous"], prev)
        res = navigation.apply_navigation(preset)
        logger.debug("nav preset result: %s", res.get("status"))
    except Exception as exc:
        logger.debug("nav apply failed: %s", exc)
