# -*- coding: utf-8 -*-
"""GUI self-test - runs inside a real FreeCAD GUI session.

Executed from the menu (Tools -> OpenCAD UX self-test) or by the maintenance
script.  Writes a JSON report and (optionally) a screenshot, never modifies
the user model.
"""

import json
import os
import time

from .. import config, logger, prefs
from ..compat import get_gui, get_main_window  # noqa


def run_gui_selftest(autoclose=False):
    checks = []
    mw = get_main_window()
    gui = get_gui()

    def add(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:400]})

    try:
        import FreeCAD  # noqa

        add("FreeCADGui available", mw is not None, str(FreeCAD.Version()[0:3]))
    except Exception as exc:
        add("FreeCADGui available", False, repr(exc))

    # 1. schema loads and resolves against the live command list
    try:
        from ..commands import registry, adapters  # noqa

        layout = registry.load_ribbon_layout()
        total = sum(len(g.buttons) for g in layout.groups)
        available = set(gui.listCommands()) if gui is not None else set()
        resolved = 0
        for btn in layout.all_buttons():
            if adapters.resolve_canonical(btn.cmd, available_ids=available) \
                    or adapters.python_command_name(btn.cmd):
                resolved += 1
        add("ribbon schema load (%d buttons)" % total, total > 40,
            "%d/%d resolve to a command or python fallback" % (resolved, total))
    except Exception as exc:
        add("ribbon schema load", False, repr(exc))

    # 2. python commands registered
    try:
        from ..commands import python_commands  # noqa

        classes = python_commands.build_command_classes()
        missing = [n for n in classes
                   if gui is not None and n not in set(gui.listCommands())]
        add("python commands registered", gui is not None and not missing,
            "%d commands, missing=%s" % (len(classes), missing))
    except Exception as exc:
        add("python commands registered", False, repr(exc))

    # 3. ribbon widget construction
    shot = ""
    try:
        from ..ribbon import widgets as rw  # noqa

        widget = rw.make_ribbon()
        widget.setWindowTitle("RibbonProbe")
        ok = widget is not None and len(widget.layout.groups) > 0
        add("ribbon widget build", ok, "groups=%d" % len(widget.layout.groups))
        if ok and mw is not None:
            try:
                shot = os.path.join(config.log_dir(),
                                    "selftest_ribbon_%s.png"
                                    % time.strftime("%Y%m%d_%H%M%S"))
                widget.resize(900, 110)
                widget.show()
                widget.repaint()
                widget.grab().save(shot)
                widget.hide()
            except Exception as exc:
                logger.debug("ribbon screenshot failed: %s", exc)
    except Exception as exc:
        add("ribbon widget build", False, repr(exc))

    # 4. theme stylesheet generation
    try:
        from ..themes import build_qss  # noqa

        qss_dark = build_qss("dark")
        qss_light = build_qss("light")
        add("themes generate QSS", len(qss_dark) > 500 and len(qss_light) > 500,
            "dark=%d light=%d chars" % (len(qss_dark), len(qss_light)))
    except Exception as exc:
        add("themes generate QSS", False, repr(exc))

    # 5. keymap preset sanity
    try:
        from ..keymap import presets as kp  # noqa
        from ..keymap import conflicts as kc  # noqa

        preset = kp.load_presets().get("fusion_inspired")
        issues = kc.internal_conflicts(preset.entries)
        add("keymap preset conflict-free", not issues,
            "%d entries" % len(preset.entries))
    except Exception as exc:
        add("keymap preset conflict-free", False, repr(exc))

    # 6. reference image workflow in a throw-away document
    try:
        import FreeCAD  # noqa

        doc = FreeCAD.newDocument("ocux_selftest")
        png = os.path.join(config.user_data_dir(), "selftest_pixel.png")
        _write_mini_png(png, 40, 20)
        from ..reference_images import (create_reference_image,  # noqa
                                        set_transparency, set_locked,
                                        set_world_width, image_size)
        size = image_size(png)
        obj = create_reference_image(doc, png, plane="XZ")
        set_world_width(obj, 100.0)
        set_transparency(obj, 0.5)
        set_locked(obj, True)
        add("reference image workflow", size == (40, 20)
            and abs(obj.XSize - 100.0) < 1e-6 and obj.RefImageLocked,
            "px=%s XSize=%.1f plane=%s locked=%s"
            % (size, obj.XSize, obj.RefImagePlane, obj.RefImageLocked))
        FreeCAD.closeDocument(doc.Name)
    except Exception as exc:
        add("reference image workflow", False, repr(exc))

    # 7. search engine EN+ZH
    try:
        from ..commands import registry  # noqa
        from ..command_search.engine import SearchIndex  # noqa

        layout = registry.load_ribbon_layout()
        items = [{"id": b.id, "canonical": b.cmd, "label_en": b.label_en,
                  "label_zh": b.label_zh, "keywords": b.keywords,
                  "group_en": g.label_en, "group_zh": g.label_zh,
                  "icon": b.icon, "shortcut": b.hint_shortcut, "enabled": True}
                 for g in layout.groups for b in g.buttons]
        idx = SearchIndex(items)
        r1 = idx.search("chamfer", limit=5)
        r2 = idx.search("倒角", limit=5)
        hit_en = any(i.get("id") == "chamfer" for i in r1)
        hit_zh = any(i.get("id") == "chamfer" for i in r2)
        add("search EN+ZH", hit_en and hit_zh,
            "chamfer=%s 倒角=%s" % (hit_en, hit_zh))
    except Exception as exc:
        add("search EN+ZH", False, repr(exc))

    # 8. context decisions
    try:
        from ..context_menu import context_actions_for  # noqa

        fake = type("O", (), {"TypeId": "Sketcher::SketchObject"})()
        acts = context_actions_for([fake])
        add("context actions (sketch)", "pad" in acts, str(acts))
    except Exception as exc:
        add("context actions (sketch)", False, repr(exc))

    ok_count = sum(1 for c in checks if c["ok"])
    report = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "0.1.0",
        "passed": ok_count,
        "total": len(checks),
        "checks": checks,
        "screenshot": shot or None,
        "summary": "GUI self-test: %d/%d checks passed" % (ok_count, len(checks)),
    }
    out = os.path.join(config.log_dir(), "gui_selftest_report.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    except OSError:
        pass
    logger.debug("gui selftest: %s", report["summary"])
    if autoclose:
        try:
            from ..compat import QtCore  # noqa

            mw2 = get_main_window()
            if mw2 is not None:
                mw2.close()
            QtCore.QTimer.singleShot(400, QtCore.QCoreApplication.instance().quit)
        except Exception:
            pass
    return report


def _write_mini_png(path, w, h):
    import struct
    import zlib

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    row = b"\x00" + b"\xff\x00\x00" * w  # opaque red row
    idat = zlib.compress(row * h)
    with open(path, "wb") as fh:
        fh.write(sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) +
                 chunk(b"IEND", b""))
