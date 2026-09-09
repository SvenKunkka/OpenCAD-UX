# -*- coding: utf-8 -*-
"""Global shortcut dispatcher (event-filter overlay).

Why an overlay instead of mutating FreeCAD's own shortcut store: mutating the
built-in command shortcuts requires writing FreeCAD's private parameter
layout per version and can silently clobber the user's custom shortcuts.  The
overlay translates keys only while the Product Design workspace is active and
passes everything through otherwise - the user's FreeCAD shortcuts remain
untouched (see README for details and the limits).

Conflict detection still runs before activation so the user sees which
FreeCAD actions share a key.
"""

import sys

from .. import logger, prefs
from ..compat import QtCore  # noqa
from ..commands import execution, adapters


class KeyDispatcher(QtCore.QObject):
    """Translate shortcut keys into canonical actions while enabled."""

    def __init__(self, key_action_map, runner=None, parent=None):
        """key_action_map: {action_name: canonical_cmd}"""
        super(KeyDispatcher, self).__init__(parent)
        self.key_action_map = dict(key_action_map)
        self.runner = runner or self._default_runner
        self.enabled = False
        self._installed = False

    # ------------------------------------------------------------------
    def _default_runner(self, canonical):
        try:
            result = execution.execute_canonical(canonical)
            logger.debug("dispatcher ran %s -> %s", canonical, result.status)
        except Exception as exc:  # never let a shortcut crash FreeCAD
            logger.debug("dispatcher error %s: %s", canonical, exc)

    def install(self, app):
        if self._installed:
            return
        if app is None:
            return
        app.installEventFilter(self)
        self._installed = True

    def remove(self, app):
        if app is not None and self._installed:
            try:
                app.removeEventFilter(self)
            except Exception:
                pass
        self._installed = False

    # ------------------------------------------------------------------
    def _platform_mod_token(self):
        return "Meta" if sys.platform == "darwin" else "Ctrl"

    def _normalize_preset_key(self, key):
        token = self._platform_mod_token()
        parts = []
        for p in str(key).split("+"):
            p = p.strip()
            if p.lower() == "mod":
                parts.append(token)
            else:
                parts.append(p)
        return "+".join(parts).lower()

    def _event_signature(self, event):
        Qt = QtCore.Qt
        mods = event.modifiers()
        parts = []
        if mods & Qt.ShiftModifier:
            parts.append("Shift")
        if mods & Qt.ControlModifier or mods & Qt.MetaModifier:
            parts.append(self._platform_mod_token())
        if mods & Qt.AltModifier:
            parts.append("Alt")
        key = event.key()
        # letters/digits arrive as their ASCII codes
        if 0x20 <= key <= 0x7E:
            parts.append(chr(key))
        else:
            name = None
            if key == Qt.Key_Delete:
                name = "Delete"
            elif key == Qt.Key_Escape:
                name = "Esc"
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                name = "Enter"
            elif key == Qt.Key_Tab:
                name = "Tab"
            elif key == Qt.Key_Space:
                name = "Space"
            elif Qt.Key_F1 <= key <= Qt.Key_F35:
                name = "F%d" % (key - Qt.Key_F1 + 1)
            if name is None:
                return None
            parts.append(name)
        return "+".join(parts).lower()

    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if not self.enabled:
            return False
        if event.type() != QtCore.QEvent.KeyPress:
            return False
        if event.isAutoRepeat():
            return False
        try:
            if not self._context_allows():
                return False
        except Exception:
            return False
        sig = self._event_signature(event)
        if sig is None:
            return False
        for key, canonical in self.key_action_map.items():
            if self._normalize_preset_key(key) == sig:
                # Esc stays with FreeCAD (it already cancels task dialogs)
                if key.lower() == "esc":
                    return False
                logger.debug("dispatcher hit: %s -> %s", sig, canonical)
                try:
                    self.runner(canonical)
                except Exception as exc:
                    logger.debug("dispatcher run error: %s", exc)
                return True
        return False

    def _context_allows(self):
        QtWidgets = None
        try:
            from ..compat import QtWidgets as QW  # noqa

            QtWidgets = QW
        except Exception:
            return False
        app = QtWidgets.QApplication.instance()
        if app is None:
            return False
        # modal dialogs own the keyboard
        if app.activeModalWidget() is not None:
            return False
        focus = app.focusWidget()
        if focus is not None:
            # never hijack keys while the user is typing into something
            for klass in (QtWidgets.QLineEdit, QtWidgets.QTextEdit,
                          QtWidgets.QPlainTextEdit, QtWidgets.QSpinBox,
                          QtWidgets.QDoubleSpinBox, QtWidgets.QComboBox):
                if isinstance(focus, klass):
                    return False
        # our own search dialog handles its keys itself
        top = focus
        while top is not None:
            if top.objectName() == "OpenCADUXCommandSearchDialog":
                return False
            top = top.parentWidget()
        return True


def build_dispatcher(preset_entries):
    """Map a keymap preset's entries to canonical actions, skipping actions
    without a runner (e.g. 'delete' stays native? -> native used directly)."""
    import sys as _sys

    skip = {"undo", "redo", "save", "open", "new_document", "delete", "cancel"}
    mapping = {}
    for e in preset_entries:
        if e.action in skip:
            continue
        canonical = e.action
        if canonical in adapters.PYTHON_COMMANDS or \
                adapters.candidates_for(canonical):
            mapping[e.action] = canonical
    return KeyDispatcher(mapping)
