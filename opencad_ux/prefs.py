# -*- coding: utf-8 -*-
"""One settings namespace for OpenCAD UX.

Storage back-ends
-----------------
* Inside FreeCAD : the parameter group ``BaseApp/Preferences/OpenCADUX``
  (written to user.cfg by FreeCAD itself - no manual ini handling).
* Standalone    : an in-memory dict (unit tests / tooling).

No code in this module ever *requires* FreeCAD to be importable.
"""

import json
import os
import time
from collections import OrderedDict

from . import config, logger

PARAM_GROUP = "User parameter:BaseApp/Preferences/OpenCADUX"

# Key names (kept stable; never reuse a name with a new meaning)
K = {
    "theme": "Theme",                 # 'light' | 'dark'
    "icon_size": "IconSize",          # px used for ribbon buttons
    "ribbon_show_text": "RibbonShowText",
    "button_size_mode": "ButtonSizeMode",   # 'small'|'medium'|'large'
    "hidden_groups": "HiddenGroups",  # json list of ribbon group ids
    "nav_preset": "NavPreset",        # ''|'fusion'|'revit'|'native'|'blender'...
    "nav_previous": "NavPrevious",    # snapshot for restore
    "key_preset": "KeyPreset",        # 'fusion'|'defaults'
    "key_overlay": "KeyOverlayEnabled",
    "panel_layout": "PanelLayout",    # 'left'|'right'
    "language_override": "LanguageOverride",  # ''|'zh-CN'|'en-US'
    "debug": "Debug",
    "show_status_hints": "ShowStatusHints",
    "context_panel_visible": "ContextPanelVisible",
    "context_panel_position": "ContextPanelPosition",
    "startup_restore_nav": "StartupRestoreNav",
    "settings_version": "SettingsVersion",
    "installed_version": "InstalledVersion",
}

DEFAULTS = {
    K["theme"]: "dark",
    K["icon_size"]: 24,
    K["ribbon_show_text"]: True,
    K["button_size_mode"]: "medium",
    K["hidden_groups"]: "[]",
    K["nav_preset"]: "",
    K["nav_previous"]: "",
    K["key_preset"]: "",
    K["key_overlay"]: True,
    K["panel_layout"]: "left",
    K["language_override"]: "",
    K["debug"]: False,
    K["show_status_hints"]: True,
    K["context_panel_visible"]: False,
    K["context_panel_position"]: "Right",
    K["startup_restore_nav"]: True,
    K["settings_version"]: 1,
    K["installed_version"]: "",
}


class DictStore(object):
    """In-memory stand-in for FreeCAD's ParamGet (used by tests/tooling)."""

    def __init__(self):
        self._d = {}

    def GetBool(self, key, default=False):
        return bool(self._d.get(key, default))

    def GetInt(self, key, default=0):
        return int(self._d.get(key, default))

    def GetFloat(self, key, default=0.0):
        return float(self._d.get(key, default))

    def GetString(self, key, default=""):
        return str(self._d.get(key, default))

    def SetBool(self, key, value):
        self._d[key] = bool(value)

    def SetInt(self, key, value):
        self._d[key] = int(value)

    def SetFloat(self, key, value):
        self._d[key] = float(value)

    def SetString(self, key, value):
        self._d[key] = str(value)

    def snapshot(self):
        return dict(self._d)

    def apply_snapshot(self, data):
        self._d = dict(data or {})

    def clear(self):
        self._d = {}


_store = {"group": None}


def _make_freecad_group():
    try:
        import FreeCAD  # noqa

        return FreeCAD.ParamGet(PARAM_GROUP)
    except Exception:
        return None


def get_store():
    """Return the current storage back-end (param group or dict)."""
    g = _store["group"]
    if g is None or not hasattr(g, "GetBool"):
        fc = _make_freecad_group()
        if fc is not None:
            _store["group"] = fc
        else:
            _store["group"] = DictStore()
    return _store["group"]


def reset_backend():
    """Re-detect the back-end (used by tests to switch between modes)."""
    _store["group"] = None


class Settings(object):
    """Typed access to the OpenCAD UX settings namespace."""

    def __init__(self, store=None):
        self.store = store or get_store()
        if not hasattr(self.store, "GetString"):
            raise TypeError("invalid settings store")

    # -- typed getters/setters (json aware) -------------------------------
    def get_bool(self, key, default=False):
        if key not in DEFAULTS and not isinstance(default, bool):
            raise KeyError(key)
        return bool(self.store.GetBool(key, bool(DEFAULTS.get(key, default))))

    def get_int(self, key, default=0):
        return int(self.store.GetInt(key, int(DEFAULTS.get(key, default))))

    def get_float(self, key, default=0.0):
        return float(self.store.GetFloat(key, float(DEFAULTS.get(key, default))))

    def get_string(self, key, default=""):
        return str(self.store.GetString(key, str(DEFAULTS.get(key, default))))

    def get_list(self, key):
        raw = self.store.GetString(key, str(DEFAULTS.get(key, "[]")))
        try:
            return json.loads(raw)
        except Exception:
            return []

    def set_bool(self, key, value):
        self.store.SetBool(key, bool(value))

    def set_int(self, key, value):
        self.store.SetInt(key, int(value))

    def set_float(self, key, value):
        self.store.SetFloat(key, float(value))

    def set_string(self, key, value):
        self.store.SetString(key, str(value))

    def set_list(self, key, values):
        self.store.SetString(key, json.dumps(list(values or []), ensure_ascii=False))

    # -- convenience -------------------------------------------------------
    @property
    def theme(self):
        return self.get_string(K["theme"], "dark")

    @theme.setter
    def theme(self, value):
        self.set_string(K["theme"], value)

    @property
    def debug(self):
        return self.get_bool(K["debug"], False)

    def hidden_groups(self):
        return set(self.get_list(K["hidden_groups"]))

    def toggle_group_hidden(self, group_id, hidden):
        groups = self.get_list(K["hidden_groups"])
        if hidden and group_id not in groups:
            groups.append(group_id)
        elif not hidden and group_id in groups:
            groups.remove(group_id)
        self.set_list(K["hidden_groups"], groups)

    def snapshot(self):
        """Deep copy of every key currently present in the store."""
        try:
            return self.store.snapshot()
        except Exception:
            out = OrderedDict()
            for key in sorted(self.store._d if hasattr(self.store, "_d") else []):  # pragma: no cover
                out[key] = self.store._d[key]
            return out

    def apply_snapshot(self, data):
        try:
            self.store.apply_snapshot(data)
            return True
        except Exception:
            return False

    def ensure_defaults(self):
        """Write any missing default key so the file store is explicit."""
        for key, value in DEFAULTS.items():
            if key not in (K["installed_version"],):
                if not hasattr(self.store, "GetString") or key not in self._keys():
                    pass
        self._write_missing()

    def _write_missing(self):
        present = self._keys()
        for key, value in DEFAULTS.items():
            if key in present:
                continue
            if isinstance(value, bool):
                self.set_bool(key, value)
            elif isinstance(value, int):
                self.set_int(key, value)
            elif isinstance(value, float):
                self.set_float(key, value)
            else:
                self.set_string(key, value)

    def _keys(self):
        try:
            return self.store.GetStrings() + self.store.GetBools() + self.store.GetInts() + self.store.GetFloats()
        except Exception:
            return []

    def reset_all(self):
        try:
            self.store.clear()
        except Exception:
            for key in DEFAULTS:
                try:
                    self.set_bool(key, None)  # no-op keeps API stable
                except Exception:
                    pass
        self._write_missing()


_settings_cache = {"instance": None}


def get_settings():
    s = _settings_cache["instance"]
    if s is None:
        s = Settings()
        _settings_cache["instance"] = s
    return s


# ---------------------------------------------------------------------------
# Backups: config files + param-group snapshots
# ---------------------------------------------------------------------------

def backup_dir(tag):
    d = os.path.join(config.user_data_dir(), "backups", tag or "misc")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    return d


def _cfg_paths():
    paths = []
    try:
        import FreeCAD  # noqa

        for cfgkey in ("UserParameter", "SystemParameter"):
            p = FreeCAD.ConfigGet(cfgkey)
            if p:
                paths.append((cfgkey, p))
    except Exception:
        pass
    return paths


def backup_config_files(tag, note=""):
    """Copy FreeCAD's user/system.cfg into our backups dir. Returns file list."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved = []
    for name, path in _cfg_paths():
        if not os.path.isfile(path):
            continue
        dst = os.path.join(backup_dir(tag), "%s_%s_%s.cfg" % (name, tag, stamp))
        try:
            with open(path, "rb") as src, open(dst, "wb") as out:
                out.write(src.read())
            saved.append(dst)
        except OSError as exc:
            logger.debug("backup failed %s: %s", path, exc)
    meta = os.path.join(backup_dir(tag), "%s_%s.json" % (tag, stamp))
    try:
        with open(meta, "w", encoding="utf-8") as fh:
            json.dump({"note": note, "files": saved}, fh, indent=1)
    except OSError:
        pass
    return saved


def restore_config_files(tag):
    """Restore the most recent backup for ``tag`` over the live cfg files."""
    d = backup_dir(tag)
    if not os.path.isdir(d):
        return []
    candidates = {}
    for fname in sorted(os.listdir(d)):
        if fname.startswith("UserParameter_%s_" % tag) and fname.endswith(".cfg"):
            candidates["UserParameter"] = os.path.join(d, fname)
        elif fname.startswith("SystemParameter_%s_" % tag) and fname.endswith(".cfg"):
            candidates["SystemParameter"] = os.path.join(d, fname)
    restored = []
    for name, path in _cfg_paths():
        src = candidates.get(name)
        if src and os.path.isfile(src):
            try:
                with open(src, "rb") as fh:
                    data = fh.read()
                with open(path, "wb") as out:
                    out.write(data)
                restored.append(path)
            except OSError as exc:
                logger.debug("restore failed %s: %s", path, exc)
    return restored


def list_backups(tag=None):
    d = config.user_data_dir()
    root = os.path.join(d, "backups")
    out = []
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".cfg") or f.endswith(".json"):
                p = os.path.join(dirpath, f)
                out.append((p, os.path.getmtime(p)))
    return sorted(out, key=lambda x: x[1])
