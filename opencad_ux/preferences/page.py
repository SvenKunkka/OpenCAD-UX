# -*- coding: utf-8 -*-
"""OpenCAD UX unified settings dialog (Qt)."""

import json
import os
import webbrowser

from .. import __version__, config, logger, prefs
from ..compat import QtCore, QtWidgets  # noqa
from ..commands import registry


def _s():
    return prefs.Settings()


def show_settings(parent=None, on_applied=None):
    dlg = SettingsDialog(parent)
    dlg.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    if on_applied:
        dlg.applied.connect(on_applied)
    dlg.exec_()
    return dlg


class SettingsDialog(QtWidgets.QDialog):
    applied = QtCore.Signal()

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("OpenCAD UX Settings")
        self.resize(620, 560)
        vbox = QtWidgets.QVBoxLayout(self)

        tabs = QtWidgets.QTabWidget(self)
        vbox.addWidget(tabs)
        tabs.addTab(self._tab_appearance(), "Appearance / 外观")
        tabs.addTab(self._tab_ribbon(), "Ribbon")
        tabs.addTab(self._tab_nav(), "Navigation / 导航")
        tabs.addTab(self._tab_keys(), "Shortcuts / 快捷键")
        tabs.addTab(self._tab_workflow(), "Workflow / 工作流")
        tabs.addTab(self._tab_system(), "System / 系统")

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Apply |
            QtWidgets.QDialogButtonBox.Ok |
            QtWidgets.QDialogButtonBox.Cancel, self)
        btns.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self._apply)
        btns.accepted.connect(self._ok)
        btns.rejected.connect(self.reject)
        vbox.addWidget(btns)

    # ------------------------------------------------------------------
    def _tab_appearance(self):
        s = _s()
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        self.theme_combo = QtWidgets.QComboBox(page)
        for tid in ("light", "dark"):
            label = "Light / 浅色" if tid == "light" else "Dark / 深色"
            self.theme_combo.addItem(label, tid)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(s.theme)))
        form.addRow("Theme / 主题", self.theme_combo)

        self.icon_mode = QtWidgets.QComboBox(page)
        for key, label in (("small", "Small / 小"), ("medium", "Medium / 中"),
                           ("large", "Large / 大")):
            self.icon_mode.addItem(label, key)
        self.icon_mode.setCurrentIndex(max(0, self.icon_mode.findData(
            s.get_string(prefs.K["button_size_mode"], "medium"))))
        form.addRow("Ribbon button size / 按钮大小", self.icon_mode)

        self.show_text = QtWidgets.QCheckBox("Show icon text / 显示文字", page)
        self.show_text.setChecked(s.get_bool(prefs.K["ribbon_show_text"], True))
        form.addRow("", self.show_text)

        self.lang_combo = QtWidgets.QComboBox(page)
        for key, label in (("", "Follow FreeCAD / 跟随 FreeCAD"),
                           ("en", "English"), ("zh", "中文")):
            self.lang_combo.addItem(label, key)
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(
            s.get_string(prefs.K["language_override"], ""))))
        form.addRow("Interface language / 界面语言", self.lang_combo)
        return page

    def _tab_ribbon(self):
        s = _s()
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        hidden = s.hidden_groups()
        self.group_checks = {}
        layout = registry.load_ribbon_layout()
        for group in layout.groups:
            cb = QtWidgets.QCheckBox("%s  (%s)" % (group.label_en, group.label_zh), page)
            cb.setChecked(group.id not in hidden)
            self.group_checks[group.id] = cb
            v.addWidget(cb)
        v.addWidget(QtWidgets.QLabel(
            "Hidden groups stay hidden on the ribbon; nothing is deleted. "
            "FreeCAD's own workbenches are never removed."))
        v.addStretch(1)
        return page

    def _tab_nav(self):
        s = _s()
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        form = QtWidgets.QFormLayout()
        self.nav_combo = QtWidgets.QComboBox(page)
        for key, label in (("", "Keep current / 保持现状"),
                           ("revit", "Revit (closest built-in)"),
                           ("fusion", "Fusion style (native if available)"),
                           ("native", "FreeCAD default (CAD)")):
            self.nav_combo.addItem(label, key)
        self.nav_combo.setCurrentIndex(max(0, self.nav_combo.findData(
            s.get_string(prefs.K["nav_preset"], ""))))
        form.addRow("Mouse navigation / 鼠标导航", self.nav_combo)
        v.addLayout(form)
        info = QtWidgets.QLabel(
            "FreeCAD 1.0/1.1 have no Fusion navigation style, so the python "
            "layer applies the closest built-in (Revit). See README for the "
            "python vs native patch differences.", page)
        info.setWordWrap(True)
        v.addWidget(info)
        self.nav_restore = QtWidgets.QPushButton(
            "Restore previous navigation style / 恢复之前导航", page)
        v.addWidget(self.nav_restore)
        v.addStretch(1)
        return page

    def _tab_keys(self):
        s = _s()
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        info = QtWidgets.QLabel(
            "Shortcuts are delivered by an overlay while the Product Design "
            "workspace is active; your FreeCAD shortcuts are never modified. "
            "Conflicts are detected before activation.", page)
        info.setWordWrap(True)
        v.addWidget(info)
        self.key_apply = QtWidgets.QPushButton(
            "Apply Fusion-inspired preset / 应用 Fusion 风格预设", page)
        self.key_apply.clicked.connect(self._apply_fusion_keys)
        v.addWidget(self.key_apply)
        self.key_defaults = QtWidgets.QPushButton(
            "Restore FreeCAD default shortcuts / 恢复 FreeCAD 默认快捷键", page)
        self.key_defaults.clicked.connect(self._restore_default_keys)
        v.addWidget(self.key_defaults)
        row = QtWidgets.QHBoxLayout()
        self.key_import = QtWidgets.QPushButton("Import… / 导入", page)
        self.key_export = QtWidgets.QPushButton("Export… / 导出", page)
        self.key_import.clicked.connect(self._import_keys)
        self.key_export.clicked.connect(self._export_keys)
        row.addWidget(self.key_import)
        row.addWidget(self.key_export)
        v.addLayout(row)
        self.conflict_label = QtWidgets.QLabel("", page)
        self.conflict_label.setWordWrap(True)
        v.addWidget(self.conflict_label)
        v.addStretch(1)
        return page

    def _tab_workflow(self):
        s = _s()
        page = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(page)
        self.panel_combo = QtWidgets.QComboBox(page)
        for key, label in (("left", "Left / 左侧"), ("right", "Right / 右侧")):
            self.panel_combo.addItem(label, key)
        self.panel_combo.setCurrentIndex(max(0, self.panel_combo.findData(
            s.get_string(prefs.K["panel_layout"], "left"))))
        form.addRow("Panels position / 面板位置", self.panel_combo)
        self.context_vis = QtWidgets.QCheckBox(
            "Show context actions panel / 显示上下文操作面板", page)
        self.context_vis.setChecked(
            s.get_bool(prefs.K["context_panel_visible"], False))
        form.addRow("", self.context_vis)
        return page

    def _tab_system(self):
        s = _s()
        page = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(page)
        form = QtWidgets.QFormLayout()
        self.debug_chk = QtWidgets.QCheckBox("Debug logging / 调试日志", page)
        self.debug_chk.setChecked(s.get_bool(prefs.K["debug"], False))
        form.addRow("", self.debug_chk)
        v.addLayout(form)
        row = QtWidgets.QHBoxLayout()
        self.backup_btn = QtWidgets.QPushButton(
            "Back up settings now / 立即备份设置", page)
        self.restore_btn = QtWidgets.QPushButton(
            "Restore from backup / 从备份恢复", page)
        self.reset_btn = QtWidgets.QPushButton(
            "Restore default layout / 恢复默认布局", page)
        self.backup_btn.clicked.connect(self._do_backup)
        self.restore_btn.clicked.connect(self._do_restore_backup)
        self.reset_btn.clicked.connect(self._do_reset)
        row.addWidget(self.backup_btn)
        row.addWidget(self.restore_btn)
        v.addLayout(row)
        v.addWidget(self.reset_btn)
        update_btn = QtWidgets.QPushButton("Check for updates / 检查更新", page)
        update_btn.clicked.connect(self._check_updates)
        v.addWidget(update_btn)
        log = QtWidgets.QLabel("Log file: %s" % config.log_file(), page)
        log.setWordWrap(True)
        v.addWidget(log)
        version = QtWidgets.QLabel(
            "OpenCAD UX %s | FreeCAD parameter group: %s"
            % (__version__, prefs.PARAM_GROUP), page)
        version.setWordWrap(True)
        v.addWidget(version)
        v.addStretch(1)
        return page

    # ------------------------------------------------------------------
    def _collect(self):
        s = _s()
        s.theme = self.theme_combo.currentData()
        s.set_string(prefs.K["button_size_mode"], self.icon_mode.currentData())
        s.set_bool(prefs.K["ribbon_show_text"], self.show_text.isChecked())
        s.set_string(prefs.K["language_override"], self.lang_combo.currentData())
        s.set_string(prefs.K["panel_layout"], self.panel_combo.currentData())
        s.set_bool(prefs.K["context_panel_visible"], self.context_vis.isChecked())
        s.set_bool(prefs.K["debug"], self.debug_chk.isChecked())
        s.set_string(prefs.K["nav_preset"], self.nav_combo.currentData())
        for gid, cb in self.group_checks.items():
            s.toggle_group_hidden(gid, not cb.isChecked())

    def _apply(self):
        self._collect()
        self._apply_live()
        self.applied.emit()

    def _ok(self):
        self._apply()
        self.accept()

    def _apply_live(self):
        s = _s()
        try:
            from ..themes import apply as ta  # noqa

            ta.apply_theme(s.theme, remember=True)
        except Exception as exc:
            logger.debug("theme live apply failed: %s", exc)
        try:
            from .. import workbench  # noqa

            workbench.rebuild_ui()
        except Exception as exc:
            logger.debug("ui rebuild after settings failed: %s", exc)
        nav = self.nav_combo.currentData()
        if nav:
            try:
                from .. import navigation  # noqa

                res = navigation.apply_navigation(nav)
                if res.get("notes"):
                    self.conflict_label.setText("Navigation:\n" +
                                                "\n".join(res["notes"]))
            except Exception as exc:
                logger.debug("nav apply failed: %s", exc)

    # ------------------------------------------------------------------
    def _apply_fusion_keys(self):
        try:
            from ..keymap import presets as kp  # noqa
            from ..keymap import conflicts as kc  # noqa
            from .. import workbench  # noqa

            preset = kp.load_presets().get("fusion_inspired")
            if preset is None:
                return
            issues = kc.internal_conflicts(preset.entries)
            if issues:
                self.conflict_label.setText(
                    "Preset has internal conflicts:\n" +
                    kc.summarize_conflicts(issues))
                return
            s = _s()
            s.set_string(prefs.K["key_preset"], "fusion_inspired")
            workbench.rebuild_dispatcher()
            self.conflict_label.setText("Fusion-inspired preset active (overlay "
                                        "mode; FreeCAD shortcuts untouched).")
        except Exception as exc:
            self.conflict_label.setText("Could not apply preset: %s" % exc)

    def _restore_default_keys(self):
        try:
            from .. import workbench  # noqa

            s = _s()
            s.set_string(prefs.K["key_preset"], "")
            workbench.rebuild_dispatcher()
            self.conflict_label.setText("Overlay disabled - FreeCAD default "
                                        "shortcuts are in effect (they were "
                                        "never modified).")
        except Exception as exc:
            self.conflict_label.setText("Error: %s" % exc)

    def _import_keys(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import shortcut preset", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            entry = data.get("shortcuts")
            if not isinstance(entry, list):
                raise ValueError("no 'shortcuts' list")
            from ..keymap import presets as kp  # noqa

            s = _s()
            s.set_string(prefs.K["custom_keymap"], json.dumps(data))
            self.conflict_label.setText("Imported %d shortcut(s); re-apply the "
                                        "preset in Workflow/Settings." %
                                        len(entry))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Import failed", str(exc))

    def _export_keys(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export shortcut preset", "opencad_ux_shortcuts.json",
            "JSON (*.json)")
        if not path:
            return
        try:
            from ..keymap import presets as kp  # noqa

            preset = kp.load_presets().get("fusion_inspired")
            data = {"schema_version": 1,
                    "shortcuts": [{"action": e.action, "key": e.key}
                                  for e in preset.entries]}
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=1)
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Export failed", str(exc))

    def _do_backup(self):
        files = prefs.backup_config_files("settings",
                                          "manual backup from settings dialog")
        QtWidgets.QMessageBox.information(
            self, "Backup", "Backed up %d config file(s) to:\n%s"
            % (len(files), prefs.backup_dir("settings")))

    def _do_restore_backup(self):
        try:
            restored = prefs.restore_config_files("settings")
            if restored:
                QtWidgets.QMessageBox.information(
                    self, "Restore",
                    "Restored config files. FreeCAD must be restarted for the "
                    "changes to take effect.")
            else:
                QtWidgets.QMessageBox.information(
                    self, "Restore", "No matching backup found.")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Restore", str(exc))

    def _do_reset(self):
        s = _s()
        s.reset_all()
        try:
            from .. import workbench  # noqa

            workbench.disable_ux(full=True)
        except Exception as exc:
            logger.debug("reset UI failed: %s", exc)
        QtWidgets.QMessageBox.information(
            self, "Reset",
            "OpenCAD UX settings reset and UI restored. Restart FreeCAD if "
            "anything looks off.")

    def _check_updates(self):
        QtWidgets.QMessageBox.information(
            self, "Check updates",
            "Current version: %s\n\nReleases are published on GitHub: "
            "https://github.com/OpenCAD-UX/OpenCAD-UX/releases\n\n"
            "Note: 'Check updates' opens the releases page in your browser."
            % __version__)
        webbrowser.open("https://github.com/OpenCAD-UX/OpenCAD-UX/releases")
