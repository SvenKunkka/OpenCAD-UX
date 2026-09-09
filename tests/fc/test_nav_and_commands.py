# -*- coding: utf-8 -*-
"""Console tests - navigation param persistence + command resolution against
the harvested command snapshot (GUI command ids verified offline)."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "fc_commands_1.1.txt")


class TestNavigationParam(unittest.TestCase):
    def test_set_and_read(self):
        from opencad_ux import navigation

        prev = navigation.current_style()
        self.assertTrue(navigation.set_style_param("Gui::RevitNavigationStyle"))
        self.assertEqual(navigation.current_style(),
                         "Gui::RevitNavigationStyle")
        # restore previous to keep the isolated cfg tidy
        navigation.set_style_param(prev or "")

    def test_fusion_not_available_on_this_build(self):
        # FreeCAD 1.1.3 ships no Fusion style (checked against the nav class
        # list); Revit is the documented fallback.
        from opencad_ux import navigation

        self.assertEqual(navigation.DEFAULT_CLOSEST, "Gui::RevitNavigationStyle")


class TestCommandResolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, "r", encoding="utf-8") as fh:
            cls.available = set(line.strip() for line in fh if line.strip())

    def test_fixture_loaded(self):
        self.assertGreater(len(self.available), 400)

    def test_key_samplings_resolve(self):
        from opencad_ux.commands import adapters

        cases = {
            "new_sketch": "Sketcher_NewSketch",
            "line": "Sketcher_CreateLine",
            "rectangle": "Sketcher_CreateRectangle",
            "circle": "Sketcher_CreateCircle",
            "pad": "PartDesign_Pad",
            "fillet": "PartDesign_Fillet",
            "hole": "PartDesign_Hole",
            "measure": "Std_Measure",
            "geometry_check": "Part_CheckGeometry",
            "fit_all": "Std_ViewFitAll",
        }
        for canonical, expected in cases.items():
            got = adapters.resolve_canonical(canonical, self.available)
            self.assertEqual(got, expected, canonical)

    def test_every_button_resolves_or_documented(self):
        from opencad_ux.commands import adapters, registry

        layout = registry.load_ribbon_layout()
        unresolved = []
        for b in layout.all_buttons():
            if adapters.resolve_canonical(b.cmd, self.available):
                continue
            if adapters.python_command_name(b.cmd):
                continue
            if adapters.not_available_reason(b.cmd):
                continue
            unresolved.append((b.id, b.cmd))
        self.assertEqual(
            unresolved, [],
            "buttons with no executable path: %s" % unresolved)

    def test_python_command_names_registered_map(self):
        from opencad_ux.commands import adapters

        for canonical, name in adapters.PYTHON_COMMANDS.items():
            self.assertTrue(name.startswith("OpencadUX_"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
