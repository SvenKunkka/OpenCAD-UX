# -*- coding: utf-8 -*-
"""Minimal debug logger with a single enable switch (prefs key ``debug``).

GUI Python ``print`` output inside FreeCAD is redirected to the internal
console and is invisible in log files, so everything that matters for
debugging is written through this module instead.
"""

import os
import time

from . import config

_LOGGER_STATE = {"enabled": None, "fp": None, "path": None}


def _ensure_file():
    if _LOGGER_STATE["fp"] is None:
        try:
            path = config.log_file()
            _LOGGER_STATE["path"] = path
            _LOGGER_STATE["fp"] = open(path, "a", encoding="utf-8", buffering=1)
        except OSError:
            _LOGGER_STATE["fp"] = False
    return _LOGGER_STATE["fp"]


def set_enabled(flag):
    _LOGGER_STATE["enabled"] = bool(flag)
    if not flag and _LOGGER_STATE["fp"] not in (None, False):
        try:
            _LOGGER_STATE["fp"].close()
        except Exception:
            pass
        _LOGGER_STATE["fp"] = None


def enabled():
    return bool(_LOGGER_STATE["enabled"])


def _sync_from_prefs():
    if _LOGGER_STATE["enabled"] is None:
        try:
            from . import prefs  # local import avoids cycles

            set_enabled(prefs.get_settings().get_bool("debug", False))
        except Exception:
            set_enabled(False)
    return _LOGGER_STATE["enabled"]


def debug(msg, *args):
    if not _sync_from_prefs():
        return
    line = "[OpenCAD UX] " + (msg % args if args else msg)
    fp = _ensure_file()
    if fp:
        try:
            fp.write("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), line))
        except Exception:
            pass
    _console(line)


def log_path():
    _ensure_file()
    return _LOGGER_STATE.get("path")


def _console(line):
    try:
        import FreeCAD  # noqa

        FreeCAD.Console.Log(line + "\n")
    except Exception:
        try:
            os.write(2, (line + "\n").encode("utf-8", "replace"))
        except Exception:
            pass
