# -*- coding: utf-8 -*-
"""Context-actions dock panel (Qt)."""

from .. import logger, prefs
from ..commands import registry
from ..compat import QtCore, QtWidgets  # noqa
from ..context_menu import context_actions_for
from ..config import icon_path  # noqa


class ContextActionsPanel(QtWidgets.QFrame):
    """Shows the most relevant actions for the current selection."""

    def __init__(self, parent=None, runner=None, icon_provider=None):
        super(ContextActionsPanel, self).__init__(parent)
        self.setObjectName("OpenCADUXContextPanel")
        self._runner = runner or self._default_runner
        self._icons = icon_provider or _provider()
        self._layout_obj = registry.load_ribbon_layout()
        self._selection_objects = []
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(4)
        title = QtWidgets.QLabel("Selection actions")
        title.setStyleSheet("font-weight: bold;")
        vbox.addWidget(title)
        self._actions_box = QtWidgets.QVBoxLayout()
        vbox.addLayout(self._actions_box)
        vbox.addStretch(1)

    def refresh(self, selection=None):
        """Rebuild buttons from the current (or given) selection."""
        if selection is None:
            selection = self._selection_objects
        # clear
        while self._actions_box.count():
            item = self._actions_box.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        if not selection:
            self._add_action("new_sketch")
            self._add_action("import_ref_image")
            self._add_action("command_search")
            return
        canonicals = context_actions_for(selection)
        for canonical in canonicals:
            self._add_action(canonical)

    def set_selection_objects(self, objects):
        self._selection_objects = list(objects or [])
        self.refresh()

    def _add_action(self, canonical):
        btn = self._layout_obj.by_id(canonical)
        label = btn.label_en if btn else canonical
        b = QtWidgets.QToolButton(self)
        b.setText(label)
        b.setToolButtonStyle(QtWidgets.Qt.ToolButtonTextBesideIcon)
        b.setIconSize(QtCore.QSize(16, 16))
        icon = self._icons(canonical)
        if icon is not None:
            b.setIcon(icon)
        b.clicked.connect(lambda checked=False, c=canonical: self._runner(c))
        self._actions_box.addWidget(b)

    def _default_runner(self, canonical):
        from ..commands.execution import execute_canonical  # noqa

        try:
            execute_canonical(canonical)
        except Exception as exc:
            logger.debug("context action failed %s: %s", canonical, exc)


def _provider():
    cache = {}

    def provide(name):
        if name in cache:
            return cache[name]
        from ..compat import QtGui  # noqa
        from ..config import icon_path  # noqa
        import os  # noqa

        theme = "light"
        try:
            theme = prefs.Settings().theme
        except Exception:
            pass
        p = icon_path(name or "product-design", theme)
        if not os.path.isfile(p):
            cache[name] = None
            return None
        icon = QtGui.QIcon(p)
        cache[name] = icon
        return icon

    return provide
