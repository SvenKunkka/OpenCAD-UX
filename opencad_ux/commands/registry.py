# -*- coding: utf-8 -*-
"""Ribbon/keymap schema loading and validation (pure logic, no Qt/FreeCAD)."""

import json
import os

from .. import config, logger


class SchemaError(ValueError):
    pass


class RibbonButton(object):
    __slots__ = (
        "id", "label_en", "label_zh", "cmd", "icon", "keywords", "hint_shortcut", "group",
    )

    def __init__(self, group, data):
        self.group = group
        self.id = str(data.get("id") or "").strip()
        label = data.get("label") or {}
        if isinstance(label, str):
            label = {"en": label, "zh": label}
        self.label_en = label.get("en") or self.id
        self.label_zh = label.get("zh") or self.label_en
        self.cmd = str(data.get("cmd") or self.id).strip()
        self.icon = str(data.get("icon") or self.id).strip()
        self.keywords = data.get("keywords") or []
        self.hint_shortcut = str(data.get("hint_shortcut") or "")

    def label(self, lang="en"):
        return self.label_zh if lang == "zh" else self.label_en


class RibbonGroup(object):
    __slots__ = ("id", "label_en", "label_zh", "buttons")

    def __init__(self, data):
        self.id = str(data.get("id") or "").strip()
        label = data.get("label") or {}
        if isinstance(label, str):
            label = {"en": label, "zh": label}
        self.label_en = label.get("en") or self.id
        self.label_zh = label.get("zh") or self.label_en
        raw_buttons = data.get("buttons") or []
        if not self.id:
            raise SchemaError("ribbon group without id")
        self.buttons = []
        seen = set()
        for b in raw_buttons:
            btn = RibbonButton(self.id, b)
            if not btn.id:
                raise SchemaError("ribbon button without id in group %s" % self.id)
            if btn.id in seen:
                raise SchemaError("duplicate ribbon button id %s" % btn.id)
            seen.add(btn.id)
            self.buttons.append(btn)

    def label(self, lang="en"):
        return self.label_zh if lang == "zh" else self.label_en


class RibbonLayout(object):
    def __init__(self, groups, schema_version, source):
        self.groups = groups
        self.schema_version = schema_version
        self.source = source

    def by_id(self, button_id):
        for g in self.groups:
            for b in g.buttons:
                if b.id == button_id:
                    return b
        return None

    def all_buttons(self):
        for g in self.groups:
            for b in g.buttons:
                yield b


def load_ribbon_layout(path=None, validate=True):
    path = path or config.RIBBON_SCHEMA
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if validate:
        _validate_root(data)
    groups = []
    for gdata in data.get("groups") or []:
        try:
            groups.append(RibbonGroup(gdata))
        except SchemaError as exc:
            if validate:
                raise
            logger.debug("skipping bad group: %s", exc)
    return RibbonLayout(groups, data.get("schema_version"), path)


def _validate_root(data):
    if not isinstance(data, dict) or "groups" not in data:
        raise SchemaError("ribbon.json must contain a 'groups' list")
    if not isinstance(data["groups"], list) or not data["groups"]:
        raise SchemaError("ribbon.json 'groups' must be a non-empty list")


def layout_summary(layout):
    """Counts for test reports: total buttons per group."""
    return {g.id: len(g.buttons) for g in layout.groups}
