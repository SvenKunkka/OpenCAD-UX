# -*- coding: utf-8 -*-
"""Path and platform resolution.  No hard-coded user directories."""

import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# repository/addon root: the folder that contains Init.py + resources/
ADDON_ROOT = os.path.dirname(_THIS_DIR)

RESOURCES_DIR = os.path.join(ADDON_ROOT, "resources")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")
RIBBON_SCHEMA = os.path.join(RESOURCES_DIR, "ribbon.json")
KEYMAP_PRESETS = os.path.join(RESOURCES_DIR, "keymap.json")
THEMES_DIR = os.path.join(RESOURCES_DIR, "themes")

APP_DIR_NAME = "OpenCADUX"


def _freecad():
    try:
        import FreeCAD  # noqa
        return FreeCAD
    except Exception:
        return None


def _freecad_app_data_dir():
    fc = _freecad()
    if fc is not None:
        try:
            return fc.getUserAppDataDir()
        except Exception:
            pass
    return None


def default_user_data_dir():
    """FreeCAD's own per-version user data dir when running inside FreeCAD,
    otherwise a conventional per-OS location (never a hard-coded user name)."""
    fc_dir = _freecad_app_data_dir()
    if fc_dir:
        return os.path.join(fc_dir, APP_DIR_NAME)
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support", "FreeCAD")
    elif os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA", home), "FreeCAD")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.join(home, ".local", "share"))
        base = os.path.join(base, "FreeCAD")
    return os.path.join(base, APP_DIR_NAME)


def user_data_dir(create=True):
    d = default_user_data_dir()
    if create:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
    return d


def log_dir():
    return user_data_dir()


def log_file():
    return os.path.join(log_dir(), "opencad_ux.log")


def resource_path(*parts):
    return os.path.join(RESOURCES_DIR, *parts)


def icon_path(name, theme="light"):
    """Icon path inside resources/icons/<theme>/<name>.svg.  ``name`` may be
    given with or without the .svg suffix."""
    base = name if name.endswith(".svg") else name + ".svg"
    return os.path.join(ICONS_DIR, theme, base)


def theme_resource(name):
    return os.path.join(THEMES_DIR, name)


def resource_json(name):
    return os.path.join(RESOURCES_DIR, name)
