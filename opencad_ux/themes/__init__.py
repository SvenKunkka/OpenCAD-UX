# -*- coding: utf-8 -*-
"""Original light/dark themes: data loading, QSS/palette generation.

The theme JSON only holds colours and fonts; building the stylesheet is a
pure function so it can be unit-tested without Qt.  Applying it to FreeCAD
(live) lives in :mod:`.apply`.
"""

import json
import os

from .. import config


def available_theme_ids():
    ids = []
    for fname in sorted(os.listdir(config.THEMES_DIR)):
        if fname.endswith(".json"):
            ids.append(fname[:-5])
    return ids


def load_theme(theme_id):
    path = os.path.join(config.THEMES_DIR, theme_id + ".json")
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "palette" not in data:
        raise ValueError("theme %s has no palette" % theme_id)
    return data


def build_qss(theme_id):
    """Stylesheet string for a theme id. Pure: no Qt required."""
    data = load_theme(theme_id)
    p = data["palette"]

    def c(key, fallback=""):
        return p.get(key, fallback)

    # Bootstrap the palette-derived vars used below.
    border = c("ribbon_border", c("windowText", "#888"))
    base = c("base", c("window", "#eee"))
    text = c("text", c("windowText", "#111"))
    disabled = c("disabledText", "#999")
    btn = c("button", base)
    hlight = c("highlight", "#2f6fed")
    htext = c("highlightedText", "#fff")

    qss = """
/* ===== OpenCAD UX theme (%(id)s) ===== */
QMainWindow, QDialog, QMessageBox {
    background-color: %(window)s;
    color: %(text)s;
}
QWidget {
    color: %(text)s;
    font-size: 13px;
}
QMenuBar {
    background-color: %(ribbon_bg)s;
    border-bottom: 1px solid %(border)s;
}
QMenuBar::item { padding: 4px 10px; background: transparent; }
QMenuBar::item:selected { background: %(hover)s; border-radius: 4px; }
QMenu {
    background-color: %(base)s;
    border: 1px solid %(border)s;
}
QMenu::item:selected { background-color: %(accent_soft)s; }
QToolBar {
    background-color: %(ribbon_bg)s;
    border-bottom: 1px solid %(border)s;
    spacing: 4px;
    padding: 2px;
}
QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 5px;
    padding: 3px;
}
QToolButton:hover { background-color: %(hover)s; }
QToolButton:pressed { background-color: %(accent_soft)s; }
QToolButton:checked { background-color: %(accent_soft)s; border: 1px solid %(accent)s; }
QPushButton {
    background-color: %(btn)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 4px 12px;
}
QPushButton:hover { background-color: %(hover)s; }
QPushButton:default { border: 1px solid %(accent)s; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit {
    background-color: %(base)s;
    border: 1px solid %(border)s;
    border-radius: 4px;
    padding: 3px 6px;
    selection-background-color: %(accent)s;
    selection-color: %(htext)s;
}
QComboBox QAbstractItemView {
    background-color: %(base)s;
    border: 1px solid %(border)s;
    selection-background-color: %(accent)s;
    selection-color: %(htext)s;
}
QTreeView, QListView, QTableView, QColumnView {
    background-color: %(base)s;
    alternate-background-color: %(alt)s;
    border: 1px solid %(border)s;
}
QTreeView::item:selected, QListView::item:selected, QTableView::item:selected {
    background-color: %(accent)s;
    color: %(htext)s;
}
QHeaderView::section {
    background-color: %(btn)s;
    border: none;
    border-right: 1px solid %(border)s;
    padding: 4px;
}
QStatusBar {
    background-color: %(ribbon_bg)s;
    border-top: 1px solid %(border)s;
}
QDockWidget {
    color: %(text)s;
    titlebar-close-icon: none;
}
QDockWidget::title {
    background-color: %(ribbon_bg)s;
    padding: 4px 8px;
    border-bottom: 1px solid %(border)s;
    text-align: left;
}
QScrollBar:vertical { background: %(ribbon_bg)s; width: 12px; margin: 0; }
QScrollBar::handle:vertical { background: %(btn)s; min-height: 24px; border-radius: 5px; }
QScrollBar::handle:vertical:hover { background: %(hover)s; }
QScrollBar:horizontal { background: %(ribbon_bg)s; height: 12px; margin: 0; }
QScrollBar::handle:horizontal { background: %(btn)s; min-width: 24px; border-radius: 5px; }
QTabWidget::pane { border: 1px solid %(border)s; }
QTabBar::tab { background: transparent; padding: 5px 10px; border: 1px solid transparent; }
QTabBar::tab:selected { background: %(base)s; border: 1px solid %(border)s; border-bottom: none; }
QToolTip {
    background-color: %(tooltip)s;
    color: %(tooltip_text)s;
    border: 1px solid %(border)s;
    padding: 3px;
}
QCheckBox::indicator, QRadioButton::indicator { width: 14px; height: 14px; }
QSlider::groove:horizontal { height: 4px; background: %(btn)s; border-radius: 2px; }
QSlider::handle:horizontal { width: 14px; margin: -5px 0; border-radius: 7px; background: %(accent)s; }

/* ---- OpenCAD UX ribbon parts ---- */
#OpenCADUXRibbon { background-color: %(ribbon_bg)s; }
#OpenCADUXRibbonGroupPanel { background-color: %(ribbon_group)s; border: 1px solid %(border)s; border-radius: 6px; }
#OpenCADUXRibbonGroupLabel { color: %(text)s; font-size: 11px; }
#OpenCADUXRibbonButton { border-radius: 5px; }
#OpenCADUXRibbonButton:hover { background-color: %(hover)s; }
#OpenCADUXRibbonButton:pressed { background-color: %(accent_soft)s; }
#OpenCADUXCommandSearch { background-color: %(ribbon_group)s; border: 1px solid %(border)s; border-radius: 8px; }
#OpenCADUXSearchInput { font-size: 15px; padding: 6px 10px; }
#OpenCADUXContextPanel { background-color: %(ribbon_group)s; }
""".replace("%(id)s", theme_id)
    return qss % {
        "window": c("window", "#1c1f24"),
        "text": c("text", c("windowText", "#ddd")),
        "base": base,
        "alt": c("alternateBase", base),
        "btn": btn,
        "border": border,
        "disabled": disabled,
        "accent": hlight,
        "accent_soft": c("accent_soft", hlight),
        "hover": c("ribbon_hover", hlight),
        "htext": htext,
        "tooltip": c("tooltipBase", c("window", "#222")),
        "tooltip_text": c("tooltipText", text),
        "ribbon_bg": c("ribbon_background", c("window", "#222")),
        "ribbon_group": c("ribbon_group_bg", base),
        "placeholder": c("placeholderText", disabled),
    }


def theme_labels():
    return {tid: load_theme(tid).get("label", {}).get("en", tid) for tid in available_theme_ids()}
