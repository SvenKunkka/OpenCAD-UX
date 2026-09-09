# -*- coding: utf-8 -*-
"""Apply/restore themes on the live Qt application (GUI only).

The original application stylesheet is preserved (backup) so a later
"disable / restore" call brings FreeCAD back to the state before the addon
touched it.
"""

import os

from .. import config, logger, prefs
from ..compat import QtWidgets  # noqa
from . import build_qss, load_theme

_BACKUP_FILE = os.path.join(config.user_data_dir(), "styles_backup.qss")


def _app():
    return QtWidgets.QApplication.instance() if QtWidgets is not None else None


def apply_theme(theme_id, remember=True):
    """Apply theme stylesheet application-wide and record previous state."""
    qss = build_qss(theme_id)
    app = _app()
    if app is None:
        return False
    previous = app.styleSheet() or ""
    if remember:
        try:
            with open(_BACKUP_FILE, "w", encoding="utf-8") as fh:
                fh.write(previous)
        except OSError as exc:
            logger.debug("theme backup write failed: %s", exc)
    app.setStyleSheet(qss)
    try:
        s = prefs.Settings()
        s.theme = theme_id
    except Exception:
        pass
    logger.debug("theme %s applied", theme_id)
    return True


def restore_previous():
    """Restore the stylesheet that was active before apply_theme()."""
    app = _app()
    if app is None:
        return False
    previous = ""
    if os.path.isfile(_BACKUP_FILE):
        try:
            with open(_BACKUP_FILE, "r", encoding="utf-8") as fh:
                previous = fh.read()
        except OSError:
            previous = ""
    app.setStyleSheet(previous)
    return True


def theme_meta(theme_id):
    try:
        return load_theme(theme_id)
    except Exception:
        return None
