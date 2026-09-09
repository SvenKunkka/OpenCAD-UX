# -*- coding: utf-8 -*-
"""Glue between the addon UI pieces and FreeCAD's main window."""

from .. import logger, prefs
from ..compat import QtCore, QtWidgets, get_main_window  # noqa
from ..ribbon.widgets import make_ribbon, default_icon_provider
from .context_panel import ContextActionsPanel  # noqa


class _SelectionWatcher(QtCore.QObject):
    """Qt glue on top of FreeCADGui.Selection.Observer."""
    changed = QtCore.Signal()

    def __init__(self):
        super(_SelectionWatcher, self).__init__()
        self._observer = None

    def _emit(self, *args):
        self.changed.emit()

    def attach(self):
        try:
            from ..compat import get_gui  # noqa

            gui = get_gui()
            if gui is None:
                return False
            observer = _ObserverBridge(self._emit)
            self._observer = observer
            gui.Selection.addObserver(observer)
            return True
        except Exception as exc:
            logger.debug("selection watcher attach failed: %s", exc)
            return False

    def detach(self):
        try:
            if self._observer is not None:
                from ..compat import get_gui  # noqa

                gui = get_gui()
                if gui is not None:
                    gui.Selection.removeObserver(self._observer)
        except Exception:
            pass
        self._observer = None


class _ObserverBridge(object):
    def __init__(self, cb):
        self._cb = cb

    def setSelection(self, *a):
        self._cb()

    def addSelection(self, *a):
        self._cb()

    def removeSelection(self, *a):
        self._cb()

    def clearSelection(self, *a):
        self._cb()

    def setPreselection(self, *a):
        pass

    def removePreselection(self, *a):
        pass


class UxController(object):
    """Attaches/detaches the ribbon + context panel to FreeCAD's main window."""

    def __init__(self):
        self.ribbon_dock = None
        self.context_dock = None
        self.context_panel = None
        self.watcher = _SelectionWatcher()
        self.dispatcher = None

    # -- ribbon ----------------------------------------------------------
    def attach(self, mw=None):
        mw = mw or get_main_window()
        if mw is None:
            return False
        if self.ribbon_dock is not None:
            return True
        try:
            lang = _ui_lang()
            theme = prefs.Settings().theme
            settings = prefs.Settings()
            widget = make_ribbon(prefs=settings, lang=lang, theme=theme,
                                 runner=self._run_button)
            dock = QtWidgets.QDockWidget("OpenCAD UX", mw)
            dock.setObjectName("OpenCADUXRibbonDock")
            dock.setWidget(widget)
            dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable |
                             QtWidgets.QDockWidget.DockWidgetFloatable)
            dock.setAllowedAreas(QtCore.Qt.TopDockWidgetArea |
                                 QtCore.Qt.BottomDockWidgetArea)
            mw.addDockWidget(QtCore.Qt.TopDockWidgetArea, dock)
            # keep the ribbon above FreeCAD's per-workbench toolbars: set it
            # tall enough to show the largest button style
            mode = settings.get_string(prefs.K["button_size_mode"], "medium")
            heights = {"small": 74, "medium": 96, "large": 118}
            dock.setMinimumHeight(heights.get(mode, 96))
            self.ribbon_dock = dock
            logger.debug("ribbon dock attached")
            return True
        except Exception as exc:
            logger.debug("ribbon attach failed: %s", exc)
            return False

    def detach(self):
        mw = get_main_window()
        if mw is not None and self.ribbon_dock is not None:
            try:
                mw.removeDockWidget(self.ribbon_dock)
                self.ribbon_dock.deleteLater()
            except Exception:
                pass
        self.ribbon_dock = None

    def set_ribbon_visible(self, visible):
        if self.ribbon_dock is not None:
            self.ribbon_dock.setVisible(visible)

    # -- context panel ----------------------------------------------------
    def attach_context_panel(self):
        mw = get_main_window()
        if mw is None or self.context_dock is not None:
            return False
        try:
            panel = ContextActionsPanel(parent=None)
            self.context_panel = panel
            dock = QtWidgets.QDockWidget("Context Actions", mw)
            dock.setObjectName("OpenCADUXContextDock")
            dock.setWidget(panel)
            dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable |
                             QtWidgets.QDockWidget.DockWidgetFloatable |
                             QtWidgets.QDockWidget.DockWidgetClosable)
            side = QtCore.Qt.RightDockWidgetArea if \
                prefs.Settings().get_string(prefs.K["panel_layout"], "left") == "right" \
                else QtCore.Qt.LeftDockWidgetArea
            mw.addDockWidget(side, dock)
            dock.hide()
            self.context_dock = dock
            self.watcher.attach()
            self.watcher.changed.connect(self._on_selection_changed)
            panel.refresh()
            return True
        except Exception as exc:
            logger.debug("context panel attach failed: %s", exc)
            return False

    def _on_selection_changed(self):
        try:
            from ..compat import get_gui  # noqa

            gui = get_gui()
            if gui is not None and self.context_panel is not None:
                self.context_panel.set_selection_objects(
                    gui.Selection.getSelection())
        except Exception:
            pass

    def detach_context_panel(self):
        self.watcher.detach()
        mw = get_main_window()
        if mw is not None and self.context_dock is not None:
            try:
                mw.removeDockWidget(self.context_dock)
                self.context_dock.deleteLater()
            except Exception:
                pass
        self.context_dock = None
        self.context_panel = None

    def toggle_context_panel(self):
        if self.context_dock is None:
            self.attach_context_panel()
            if self.context_dock is not None:
                self.context_dock.show()
        else:
            self.context_dock.setVisible(not self.context_dock.isVisible())

    # -- key dispatcher ---------------------------------------------------
    def install_dispatcher(self):
        try:
            from ..keymap import presets as kp  # noqa
            from ..keymap.dispatcher import KeyDispatcher  # noqa

            for _name, preset in kp.load_presets().items():
                mapping = {}
                for e in preset.entries:
                    mapping[e.action] = e.action
                self.dispatcher = KeyDispatcher(mapping)
                break
            app = QtWidgets.QApplication.instance()
            if self.dispatcher is not None and app is not None:
                self.dispatcher.install(app)
                return True
        except Exception as exc:
            logger.debug("dispatcher install failed: %s", exc)
        return False

    def set_dispatcher_active(self, active):
        if self.dispatcher is not None:
            self.dispatcher.enabled = bool(active)

    def remove_dispatcher(self):
        app = QtWidgets.QApplication.instance()
        if self.dispatcher is not None:
            self.dispatcher.remove(app)
        self.dispatcher = None

    # -- internal ---------------------------------------------------------
    def _run_button(self, button):
        from ..commands.execution import execute_button  # noqa

        res = execute_button(button)
        mw = get_main_window()
        if mw is not None and mw.statusBar() is not None:
            mw.statusBar().showMessage(res.message or res.status, 5000)


def _ui_lang():
    try:
        from .. import workbench  # noqa

        return workbench.ui_language()
    except Exception:
        return "en"
