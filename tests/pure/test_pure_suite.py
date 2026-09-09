# -*- coding: utf-8 -*-
"""Pure python tests (no FreeCAD, no Qt). Run with:
python3 -m unittest discover -s tests/pure -v
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))  # fixtures import helper

from opencad_ux.commands import registry, adapters  # noqa: E402
from opencad_ux.keymap import presets as kp, conflicts as kc  # noqa: E402
from opencad_ux.command_search.engine import SearchIndex  # noqa: E402
from opencad_ux.context_menu import context_actions_for, classify_object  # noqa: E402
from opencad_ux.themes import build_qss, available_theme_ids  # noqa: E402
from opencad_ux.reference_images import (png_size, jpeg_size,  # noqa: E402
                                         scale_from_pixels,
                                         dimensions_from_calibration)
from opencad_ux import navigation  # noqa: E402


class FakeObj(object):
    """Object look-alike with a TypeId."""

    def __init__(self, type_id):
        self.TypeId = type_id


class TestRibbonSchema(unittest.TestCase):
    def setUp(self):
        self.layout = registry.load_ribbon_layout()

    def test_groups_present(self):
        ids = [g.id for g in self.layout.groups]
        for wanted in ("sketch", "constraints", "create", "modify",
                       "combine", "inspect", "insert_export"):
            self.assertIn(wanted, ids)

    def test_buttons_count(self):
        total = sum(len(g.buttons) for g in self.layout.groups)
        self.assertGreaterEqual(total, 40)

    def test_bilingual_labels(self):
        for b in self.layout.all_buttons():
            self.assertTrue(b.label_en)
            self.assertTrue(b.label_zh)

    def test_keywords_include_zh_sampling(self):
        b = self.layout.by_id("chamfer")
        self.assertTrue(any("\u4e00" <= ch <= "\u9fff" for k in b.keywords
                            for ch in k))

    def test_icons_exist(self):
        for theme in ("light", "dark"):
            for b in self.layout.all_buttons():
                p = os.path.join(ROOT, "resources", "icons", theme,
                                 b.icon + ".svg")
                self.assertTrue(os.path.isfile(p),
                                "missing icon %s (%s)" % (b.icon, theme))

    def test_unique_ids(self):
        seen = set()
        for b in self.layout.all_buttons():
            self.assertNotIn(b.id, seen)
            seen.add(b.id)


class TestAdapters(unittest.TestCase):
    def test_resolution_modern_first(self):
        avail = {"Sketcher_CreateLine"}
        self.assertEqual(adapters.resolve_canonical("line", avail),
                         "Sketcher_CreateLine")

    def test_resolution_legacy_fallback(self):
        avail = {"Sketcher_Line", "Sketcher_Line_length"}
        self.assertEqual(adapters.resolve_canonical("line", avail),
                         "Sketcher_Line")

    def test_resolution_none(self):
        self.assertIsNone(adapters.resolve_canonical("line", set()))

    def test_every_ribbon_button_has_path(self):
        layout = registry.load_ribbon_layout()
        for b in layout.all_buttons():
            reason = adapters.not_available_reason(b.cmd)
            py = adapters.python_command_name(b.cmd)
            has_native = bool(adapters.candidates_for(b.cmd))
            self.assertTrue(reason or py or has_native,
                            "button %s has no executable path" % b.id)

    def test_move_offset_are_documented_unavailable(self):
        self.assertTrue(adapters.not_available_reason("move_face"))
        self.assertTrue(adapters.not_available_reason("offset_face"))


class TestKeymap(unittest.TestCase):
    def setUp(self):
        self.presets = kp.load_presets()

    def test_fusion_preset_exists(self):
        self.assertIn("fusion_inspired", self.presets)

    def test_no_internal_conflicts(self):
        preset = self.presets["fusion_inspired"]
        self.assertEqual(kc.internal_conflicts(preset.entries), [])

    def test_mod_expansion_platforms(self):
        entries = [kp.ShortcutEntry({"action": "undo", "key": "mod+Z"})]
        self.assertEqual(kc.internal_conflicts(entries), [])
        conflicts = kc.external_conflicts(entries, {"open": "Ctrl+Z"})
        found = [c for c in conflicts if c["platform"] == "win/linux"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["other_action"], "open")

    def test_no_mod_shortcut_identical_both_platforms(self):
        preset = self.presets["fusion_inspired"]
        for e in preset.entries:
            if "mod" not in e.key:
                self.assertEqual(kc.expand_keys(e.key)[0][0], "any")


class TestSearchEngine(unittest.TestCase):
    def _index(self):
        layout = registry.load_ribbon_layout()
        items = [{"id": b.id, "canonical": b.cmd, "label_en": b.label_en,
                  "label_zh": b.label_zh, "keywords": b.keywords,
                  "group_en": g.label_en, "group_zh": g.label_zh,
                  "icon": b.icon, "shortcut": b.hint_shortcut, "enabled": True}
                 for g in layout.groups for b in g.buttons]
        return SearchIndex(items)

    def _ids(self, results):
        return [i["id"] for i in results]

    def test_chamfer_by_english(self):
        ids = self._ids(self._index().search("chamfer", limit=8))
        self.assertIn("chamfer", ids)

    def test_chamfer_by_chinese(self):
        ids = self._ids(self._index().search("\u5012\u89d2", limit=8))
        self.assertIn("chamfer", ids)

    def test_thickness_by_chinese_shell(self):
        ids = self._ids(self._index().search("\u5916\u58f3", limit=8))
        self.assertIn("thickness", ids)

    def test_pad_by_chinese(self):
        ids = self._ids(self._index().search("\u62c9\u4f38", limit=8))
        self.assertIn("pad", ids)

    def test_union_by_chinese(self):
        ids = self._ids(self._index().search("\u5408\u5e76", limit=8))
        self.assertTrue(any(i in ("boolean_union",) for i in ids))

    def test_recents_boost(self):
        idx = self._index()
        plain = self._ids(idx.search("dim", limit=10))
        idx.record_use("dimension")
        boosted = self._ids(idx.search("dim", limit=10))
        self.assertIn("dimension", boosted)
        self.assertLessEqual(boosted.index("dimension"),
                             max(0, plain.index("dimension")))

    def test_disabled_filtered(self):
        idx = self._index()
        for item in idx.items:
            if item["id"] == "chamfer":
                item["enabled"] = False
        results = self._ids(idx.search("chamfer", limit=10))
        self.assertNotIn("chamfer", results)


class TestContext(unittest.TestCase):
    def test_sketch(self):
        acts = context_actions_for([FakeObj("Sketcher::SketchObject")])
        self.assertIn("pad", acts)

    def test_single_solid(self):
        acts = context_actions_for([FakeObj("Part::Box")])
        self.assertIn("mass_properties", acts)

    def test_two_solids_boolean(self):
        acts = context_actions_for([FakeObj("Part::Box"),
                                    FakeObj("Part::Cylinder")])
        self.assertIn("boolean_union", acts)

    def test_body(self):
        acts = context_actions_for([FakeObj("PartDesign::Body")])
        self.assertIn("fillet", acts)

    def test_nothing(self):
        acts = context_actions_for([])
        self.assertIn("new_sketch", acts)

    def test_image(self):
        acts = context_actions_for([FakeObj("Image::ImagePlane")])
        self.assertIn("calibrate_ref_image", acts)


class TestThemes(unittest.TestCase):
    def test_both_themes(self):
        self.assertEqual(set(available_theme_ids()), {"light", "dark"})

    def test_qss_nonempty_and_colored(self):
        for theme in ("light", "dark"):
            qss = build_qss(theme)
            self.assertGreater(len(qss), 500)
            self.assertIn("#", qss)
            self.assertIn("OpenCADUXRibbon", qss)


class TestRefImageMath(unittest.TestCase):
    def test_png_size(self):
        import struct
        import zlib

        def chunk(tag, data):
            c = struct.pack(">I", len(data)) + tag + data
            return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

        w, h = 40, 20
        row = b"\x00" + b"\xff\x00\x00" * w
        png = (b"\x89PNG\r\n\x1a\n" +
               chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
               chunk(b"IDAT", zlib.compress(row * h)) +
               chunk(b"IEND", b""))
        path = os.path.join(ROOT, "tests", "tmp_pixel.png")
        with open(path, "wb") as fh:
            fh.write(png)
        try:
            self.assertEqual(png_size(path), (40, 20))
            self.assertIsNone(jpeg_size(path))
        finally:
            os.remove(path)

    def test_scale_math(self):
        mm = scale_from_pixels((0, 0), (100, 0), 300.0)
        self.assertAlmostEqual(mm, 3.0)
        x, y = dimensions_from_calibration(1000, 500, mm)
        self.assertAlmostEqual(x, 3000.0)
        self.assertAlmostEqual(y, 1500.0)

    def test_scale_errors(self):
        with self.assertRaises(Exception):
            scale_from_pixels((5, 5), (5, 5), 10)
        with self.assertRaises(Exception):
            scale_from_pixels((0, 0), (10, 0), 0)


class TestNavigationMapping(unittest.TestCase):
    def test_closest_is_revit(self):
        self.assertEqual(navigation.DEFAULT_CLOSEST, "Gui::RevitNavigationStyle")

    def test_style_class_for(self):
        self.assertEqual(navigation.style_class_for("revit"),
                         "Gui::RevitNavigationStyle")
        self.assertIn("Gui::", navigation.style_class_for("blender"))

    def test_python_adjustment_docs_exist(self):
        notes = navigation.describe_python_adjustments("Gui::RevitNavigationStyle")
        self.assertGreater(len(notes), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
