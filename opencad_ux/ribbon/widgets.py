# -*- coding: utf-8 -*-
"""Ribbon widget (Qt). Builds group panels from a RibbonLayout + prefs.

Pure Qt - no FreeCADGui calls here, so it can be shown inside a plain
QMainWindow for screenshots/tests as well as inside FreeCAD's main window.
"""

from .. import prefs as _prefs
from .. import logger
from ..commands import registry as _registry
from ..commands import adapters, execution
from ..compat import QtCore, QtGui, QtWidgets  # noqa
from ..config import icon_path

ENUM_ICON_ONLY = getattr(QtWidgets.QToolButton, "ToolButtonIconOnly")
ENUM_TEXT_UNDER = getattr(QtWidgets.QToolButton, "ToolButtonTextUnderIcon")


class FlowLayout(QtWidgets.QLayout):
    """Left-to-right wrapping layout (original implementation)."""

    def __init__(self, parent=None, margin=0, spacing=4):
        super(FlowLayout, self).__init__(parent)
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(width, True)

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self._do_layout(rect.width(), False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QtCore.QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, width, test_only):
        m = self.contentsMargins()
        eff = width - m.left() - m.right()
        x, y = m.left(), m.top()
        row_height = 0
        for item in self._items:
            hint = item.sizeHint()
            next_x = x + hint.width() + self.spacing()
            if next_x - self.spacing() > eff + m.right() and row_height > 0:
                x = m.left()
                y += row_height + self.spacing()
                row_height = 0
                next_x = x + hint.width() + self.spacing()
            if not test_only:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), hint))
            x = next_x
            row_height = max(row_height, hint.height())
        return y + row_height + m.bottom()


class _GroupPanel(QtWidgets.QFrame):
    def __init__(self, group, layout_ctx, parent=None):
        super(_GroupPanel, self).__init__(parent)
        self.group = group
        self.ctx = layout_ctx
        self.setObjectName("OpenCADUXRibbonGroupPanel")
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setContentsMargins(8, 6, 8, 8)
        vbox.setSpacing(4)
        head = QtWidgets.QLabel(group.label(layout_ctx.lang))
        head.setObjectName("OpenCADUXRibbonGroupLabel")
        head.setAlignment(QtCore.Qt.AlignHCenter)
        vbox.addWidget(head)
        self.flow = FlowLayout(self, margin=2, spacing=3)
        vbox.addLayout(self.flow)

    def add_button(self, btn):
        tb = QtWidgets.QToolButton(self)
        tb.setObjectName("OpenCADUXRibbonButton")
        tb.setToolButtonStyle(self.ctx.button_style)
        icon_size = self.ctx.icon_size
        tb.setIconSize(QtCore.QSize(icon_size, icon_size))
        icon = self.ctx.icon_for(btn.icon)
        if icon is not None:
            tb.setIcon(icon)
        tb.setText(btn.label(self.ctx.lang))
        tip = btn.label(self.ctx.lang)
        if btn.hint_shortcut:
            tip += "  [%s]" % btn.hint_shortcut
        tip += "\nFreeCAD: %s" % (adapters.candidates_for(btn.cmd) or "OpenCAD UX python command")
        tb.setToolTip(tip)
        tb.clicked.connect(lambda checked=False, b=btn: self.ctx.run_button(b))
        self.flow.addWidget(tb)
        return tb


class LayoutContext(object):
    """Carries per-build settings into the widget tree (easy to test)."""

    def __init__(self, lang="en", icon_size=24, show_text=True,
                 icon_provider=None, runner=None, hidden_groups=None):
        self.lang = lang
        self.icon_size = int(icon_size)
        self.show_text = bool(show_text)
        self._icons = icon_provider or (lambda name: None)
        self.runner = runner or (lambda btn: None)
        self.hidden_groups = set(hidden_groups or ())
        self.button_style = (ENUM_TEXT_UNDER if self.show_text
                             else ENUM_ICON_ONLY)

    def icon_for(self, name):
        return self._icons(name)


def default_icon_provider(theme=None):
    """QIcon factory reading our SVG icon set for a theme."""
    theme = theme or "light"
    import os

    cache = {}

    def provide(name):
        if name in cache:
            return cache[name]
        path = icon_path(name, theme)
        if not os.path.isfile(path):
            return None
        icon = QtGui.QIcon(path)
        cache[name] = icon
        return icon

    return provide


def make_ribbon(layout=None, prefs=None, lang="en", theme="light",
                runner=None, parent=None):
    """Build the ribbon widget honoring prefs (hidden groups, sizes)."""
    settings = prefs or _prefs.Settings()
    layout = layout or _registry.load_ribbon_layout()
    show_text = settings.get_bool(_prefs.K["ribbon_show_text"], True)
    mode = settings.get_string(_prefs.K["button_size_mode"], "medium")
    icon_px = {"small": 18, "medium": 24, "large": 32}.get(mode, 24)
    provider = default_icon_provider(theme)
    ctx = LayoutContext(lang=lang, icon_size=icon_px, show_text=show_text,
                        icon_provider=provider, runner=runner,
                        hidden_groups=settings.hidden_groups())
    widget = RibbonWidget(layout, ctx, parent)
    return widget


class RibbonWidget(QtWidgets.QFrame):
    """Top-level scrollable ribbon with one panel per group."""

    def __init__(self, layout, ctx, parent=None):
        super(RibbonWidget, self).__init__(parent)
        self.layout = layout
        self.ctx = ctx
        self.setObjectName("OpenCADUXRibbon")
        self._panels = []
        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(4, 2, 4, 2)
        outer.setSpacing(0)
        brand = QtWidgets.QLabel(" OpenCAD UX ")
        brand.setObjectName("OpenCADUXBrand")
        outer.addWidget(brand, 0, QtCore.Qt.AlignVCenter)
        scroll = QtWidgets.QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("OpenCADUXRibbonInner")
        hbox = QtWidgets.QHBoxLayout(inner)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)
        for group in layout.groups:
            if group.id in ctx.hidden_groups:
                continue
            panel = _GroupPanel(group, ctx, inner)
            for btn in group.buttons:
                panel.add_button(btn)
            hbox.addWidget(panel)
        hbox.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll, 1)
        self._scroll = scroll

    def rebuild(self):
        """Rebuild after preference changes (sizes/themes/groups)."""
        parent = self.parentWidget()
        if parent is not None:
            try:
                idx = parent.indexOf(self)
                new_widget = make_ribbon(parent=parent)
                parent.removeWidget(self)
                self.deleteLater()
                if idx >= 0:
                    parent.insertWidget(min(idx, parent.count()), new_widget)
            except Exception as exc:
                logger.debug("ribbon rebuild failed: %s", exc)

    def execute(self, canonical):
        """Run a button by canonical id; returns ActionResult."""
        btn = self.layout.by_id(canonical)
        if btn is None:
            return None
        return self.ctx.runner(btn)


class RibbonSearchButton(QtWidgets.QToolButton):
    """Convenient search trigger placed next to the ribbon."""
