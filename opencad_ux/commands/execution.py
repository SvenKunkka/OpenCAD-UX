# -*- coding: utf-8 -*-
"""Safe execution of ribbon/keymap actions against the running FreeCAD.

Every path is guarded: no active document, nothing selected, command missing,
or a python fallback raising an exception all produce a clear message instead
of a crash.  GUI bits (message boxes) are created lazily and only when a main
window exists.
"""

import traceback

from .. import logger
from . import adapters, exporters


class ActionResult(object):
    def __init__(self, status="ok", message="", detail=""):
        self.status = status  # ok | native | python | unavailable | error
        self.message = message
        self.detail = detail

    def __bool__(self):
        return self.status in ("ok", "native", "python")


class GuiEnvironment(object):
    """Facade over the parts of FreeCADGui the executor needs.

    Pass a stub for console/unit tests.
    """

    def __init__(self, gui=None, main_window=None, run_command=None,
                 list_commands=None, active_document=None, selected=None):
        self.gui = gui
        self.main_window = main_window
        self._run = run_command
        self._list = list_commands
        self._doc = active_document
        self._selected = selected

    @classmethod
    def live(cls):
        from ..compat import get_gui, get_main_window  # noqa

        gui = get_gui()
        mw = get_main_window()

        def run(cmd):
            if gui is None:
                return False
            gui.runCommand(cmd)
            return True

        def lst():
            if gui is None:
                return set()
            try:
                return set(gui.listCommands())
            except Exception:
                return set()

        def doc():
            if gui is None:
                return None
            try:
                import FreeCAD  # noqa

                return FreeCAD.ActiveDocument
            except Exception:
                return None

        def selected():
            if gui is None:
                return []
            try:
                sel = gui.Selection.getSelection()
                return sel if sel else []
            except Exception:
                return []
        return cls(gui=gui, main_window=mw, run_command=run, list_commands=lst,
                   active_document=doc, selected=selected)


class ExecutionError(Exception):
    pass


def _selected_shapes(env):
    sel = env._selected() if env._selected else []
    return sel if sel else []


def _active_doc(env):
    if env._doc:
        return env._doc()
    return None


def _notice(env, title, text):
    logger.debug("notice: %s - %s", title, text)
    if env.main_window is not None:
        try:
            from ..compat import QtWidgets  # noqa

            QtWidgets.QMessageBox.information(env.main_window, title, text)
        except Exception:
            pass


def _warn(env, title, text):
    logger.debug("warning: %s - %s", title, text)
    if env.main_window is not None:
        try:
            from ..compat import QtWidgets  # noqa

            QtWidgets.QMessageBox.warning(env.main_window, title, text)
        except Exception:
            pass


def execute_button(button, env=None):
    """Run a ribbon button (``cmd`` field) through native/python/fallback."""
    env = env or GuiEnvironment.live()
    return execute_canonical(button.cmd, env, label_en=button.label_en)


def execute_canonical(canonical, env=None, label_en=None):
    """Run a canonical command id through the environment."""
    env = env or GuiEnvironment.live()
    name = label_en or canonical

    # 1) native FreeCAD command, resolved by availability
    available = set(env._list()) if env._list else None
    native_id = adapters.resolve_canonical(canonical, available_ids=available)
    if native_id and env._run:
        try:
            ok = env._run(native_id)
            return ActionResult("native", "Ran %s (%s)" % (name, native_id))
        except Exception as exc:
            logger.debug("native command %s failed: %s", native_id, exc)
            return ActionResult("error", "Command '%s' failed: %s" % (native_id, exc),
                                traceback.format_exc())

    # 2) python command registered in the GUI
    py_name = adapters.python_command_name(canonical)
    if py_name and env._run and available is not None and py_name in available:
        try:
            env._run(py_name)
            return ActionResult("python", "Ran %s (%s)" % (name, py_name))
        except Exception as exc:
            return ActionResult("error", "Command '%s' failed: %s" % (py_name, exc),
                                traceback.format_exc())

    # 3) headless python implementations (used by console tests too)
    try:
        msg = _run_python_impl(canonical, env)
        return ActionResult("python", msg)
    except _NotSupported:
        _warn(env, name, adapters.not_available_reason(canonical) or
              "This action is not available through FreeCAD's public API.")
        return ActionResult("unavailable", adapters.not_available_reason(canonical) or name)
    except Exception as exc:
        return ActionResult("error", "%s failed: %s" % (name, exc), traceback.format_exc())


class _NotSupported(RuntimeError):
    pass


def _run_python_impl(canonical, env):
    doc = _active_doc(env)
    selection = _selected_shapes(env)
    if canonical in ("move_face", "offset_face"):
        raise _NotSupported(canonical)
    if canonical == "bounding_box":
        _notice(env, "Bounding Box", exporters.report_bounding_box(selection or _doc_shapes(doc)))
        return "bounding box reported"
    if canonical == "mass_properties":
        _notice(env, "Mass Properties", exporters.report_mass_properties(selection or _doc_shapes(doc)))
        return "mass properties reported"
    if canonical == "interference":
        _notice(env, "Interference Check", exporters.report_interference(selection or _doc_shapes(doc)))
        return "interference reported"
    raise ExecutionError("no executable path for canonical '%s'" % canonical)


def _doc_shapes(doc):
    if doc is None:
        raise ExecutionError("no active document and nothing selected")
    try:
        return exporters.get_exportable_objects(doc)
    except Exception:
        return []
