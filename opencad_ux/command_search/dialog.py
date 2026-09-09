# -*- coding: utf-8 -*-
"""Command-search dialog (Qt). Lists matching commands as you type, bilingual,
with icon/name/group/shortcut and recents boost; Enter executes."""

from .. import logger, prefs
from ..command_search.engine import SearchIndex
from ..commands import execution, registry
from ..compat import QtCore, QtGui, QtWidgets  # noqa


class CommandSearchDialog(QtWidgets.QDialog):
    def __init__(self, layout=None, lang="en", theme="light",
                 icon_provider=None, enabled_ids=None, runner=None, parent=None):
        super(CommandSearchDialog, self).__init__(parent)
        self.setObjectName("OpenCADUXCommandSearchDialog")
        self.setWindowTitle("OpenCAD UX - Command Search")
        self._lang = lang
        self._theme = theme
        self._layout = layout or registry.load_ribbon_layout()
        self._provider = icon_provider or _icon_provider(theme)
        self._runner = runner or self._default_run
        self._enabled_ids = enabled_ids  # optional callable returning a set
        self._index = self._build_index()
        self._result_items = []

        self.setMinimumWidth(560)
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(10, 10, 10, 10)
        vbox.setSpacing(6)

        self.search = QtWidgets.QLineEdit(self)
        self.search.setObjectName("OpenCADUXSearchInput")
        self.search.setPlaceholderText("Search commands...  /  输入命令搜索 (e.g. 倒角, 拉伸, 抽壳)")
        self.search.textChanged.connect(self._refresh)
        vbox.addWidget(self.search)

        self.listw = QtWidgets.QListWidget(self)
        self.listw.setAlternatingRowColors(True)
        self.listw.itemActivated.connect(self._activate)
        vbox.addWidget(self.listw, 1)
        self._hint = QtWidgets.QLabel("", self)
        vbox.addWidget(self._hint)

        self.search.setFocus()

    # ------------------------------------------------------------------
    def _build_index(self):
        settings = prefs.Settings()
        recents = settings.get_string("SearchRecents", "")
        items = []
        preset_key = {}
        try:
            from ..keymap import presets as kp  # noqa

            for _name, preset in kp.load_presets().items():
                for e in preset.entries:
                    preset_key[e.action] = e.key
        except Exception:
            pass
        for group in self._layout.groups:
            for btn in group.buttons:
                items.append({
                    "id": btn.id,
                    "canonical": btn.cmd,
                    "label_en": btn.label_en,
                    "label_zh": btn.label_zh,
                    "keywords": btn.keywords,
                    "group_en": group.label_en,
                    "group_zh": group.label_zh,
                    "icon": btn.icon,
                    "shortcut": preset_key.get(btn.id, btn.hint_shortcut),
                    "enabled": True,
                })
        for extra in _extra_items(self._layout, preset_key):
            items.append(extra)
        return SearchIndex(items)

    # ------------------------------------------------------------------
    def _extra_enabled(self):
        if self._enabled_ids is None:
            return None
        try:
            return self._enabled_ids()
        except Exception:
            return None

    def _refresh(self, text):
        enabled = self._extra_enabled()
        if enabled is not None:
            for item in self._index.items:
                item["enabled"] = item["canonical"] in enabled or item["canonical"] in (
                    "command_search", "context_actions", "settings", "help_about")
        results = self._index.search(text, limit=14, only_enabled=False)
        self.listw.clear()
        self._result_items = results
        for item in results:
            entry = QtWidgets.QListWidgetItem()
            entry.setText(self._fmt(item))
            icon = self._provider(item.get("icon", ""))
            if icon is not None:
                entry.setIcon(icon)
            if not item.get("enabled", True):
                entry.setForeground(QtGui.QColor("#8a919c"))
            self.listw.addItem(entry)
        if not results:
            self._hint.setText("No matching command. / 没有匹配的命令。")
        else:
            n = sum(1 for r in results if r.get("enabled", True))
            self._hint.setText("%d result(s), %d available / %d 个结果，%d 个可用"
                               % (len(results), n, len(results), n))

    def _fmt(self, item):
        label = item.get("label_zh") if self._lang == "zh" else item.get("label_en")
        group = item.get("group_zh") if self._lang == "zh" else item.get("group_en")
        shortcut = item.get("shortcut", "")
        parts = [label, "   [%s]" % group]
        if shortcut:
            parts.append("   %s" % shortcut)
        return "".join(parts)

    def _activate(self, item):
        idx = self.listw.row(item)
        if 0 <= idx < len(self._result_items):
            chosen = self._result_items[idx]
            self._run(chosen)

    def _run(self, item):
        if not item.get("enabled", True):
            return
        canonical = item.get("canonical")
        try:
            self._index.record_use(item.get("id"))
        except Exception:
            pass
        self.accept()
        self._runner(canonical)

    def _default_run(self, canonical):
        result = execution.execute_canonical(canonical)
        logger.debug("search executed %s -> %s", canonical, result.status)

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):
        Qt = QtCore.Qt
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            self.listw.setFocus()
            return
        super(CommandSearchDialog, self).keyPressEvent(event)


def _extra_items(layout, preset_key):
    extras = [
        {"id": "command_search", "canonical": "command_search",
         "label_en": "Command Search", "label_zh": "命令搜索",
         "keywords": ["search", "find", "命令", "搜索", "快捷键"],
         "group_en": "OpenCAD UX", "group_zh": "OpenCAD UX",
         "icon": "search", "shortcut": preset_key.get("command_search", "S"),
         "enabled": True},
        {"id": "context_actions", "canonical": "context_actions",
         "label_en": "Context Actions", "label_zh": "上下文操作",
         "keywords": ["context", "right click", "上下文", "右键", "press pull"],
         "group_en": "OpenCAD UX", "group_zh": "OpenCAD UX",
         "icon": "context", "shortcut": preset_key.get("context_actions", "Q"),
         "enabled": True},
    ]
    return extras


def _icon_provider(theme):
    import os

    from ..config import icon_path  # noqa

    cache = {}

    def provide(name):
        if not name:
            return None
        if name in cache:
            return cache[name]
        path = icon_path(name, theme)
        if not os.path.isfile(path):
            return None
        icon = QtGui.QIcon(path)
        cache[name] = icon
        return icon

    return provide


def show_command_search(parent=None, enabled_ids=None):
    """Create, exec and return the dialog (used by the S key + command)."""
    try:
        from .. import workbench as wb  # noqa

        lang = wb.ui_language()
        theme = prefs.Settings().theme
    except Exception:
        lang, theme = "en", "light"
    dlg = CommandSearchDialog(lang=lang, theme=theme,
                              enabled_ids=enabled_ids, parent=parent)
    dlg.exec_()
    return dlg
