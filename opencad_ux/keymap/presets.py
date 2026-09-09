# -*- coding: utf-8 -*-
"""Shortcut preset data loading (pure)."""

import json

from .. import config


class ShortcutEntry(object):
    __slots__ = ("action", "key", "label_en", "label_zh")

    def __init__(self, data):
        self.action = data.get("action")
        self.key = data.get("key")
        label = data.get("label") or {}
        self.label_en = label.get("en") or self.action
        self.label_zh = label.get("zh") or self.label_en


class KeymapPreset(object):
    def __init__(self, name, data):
        self.name = name
        label = data.get("label") or {}
        self.label_en = label.get("en") or name
        self.label_zh = label.get("zh") or self.label_en
        self.entries = [ShortcutEntry(e) for e in (data.get("shortcuts") or [])]

    def by_action(self):
        return {e.action: e for e in self.entries}


def load_presets(path=None):
    path = path or config.KEYMAP_PRESETS
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    presets = {}
    for name, pdata in (data.get("presets") or {}).items():
        presets[name] = KeymapPreset(name, pdata)
    return presets
