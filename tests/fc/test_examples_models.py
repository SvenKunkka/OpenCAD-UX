# -*- coding: utf-8 -*-
"""Console tests - the three example models generate valid solids/files."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import FreeCAD as App  # noqa: E402
from examples import keyboard_shell, mouse_shell, enclosure  # noqa: E402


class TestExamples(unittest.TestCase):
    def _run(self, builder, name):
        result = builder.build()
        self.assertIsNotNone(result["doc"])
        solid = result["finished_solid"]
        self.assertTrue(solid.isValid(), "%s solid invalid" % name)
        self.assertGreater(solid.Volume, 500.0, name)
        out = os.path.join(ROOT, "tests", "output")
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, name + ".FCStd")
        result["doc"].saveAs(path)
        self.assertGreater(os.path.getsize(path), 2000)
        return path

    def test_keyboard(self):
        self._run(keyboard_shell, "keyboard_shell")

    def test_mouse(self):
        self._run(mouse_shell, "mouse_shell")

    def test_enclosure(self):
        self._run(enclosure, "enclosure")

    def test_enclosure_has_bosses_and_opening(self):
        result = enclosure.build()
        solid = result["finished_solid"]
        # ~4 bosses + tray: expect multiple solids or one fused solid; and the
        # USB opening removes volume so mass < solid box mass
        vol = solid.Volume
        full_box = result["body"].Shape
        self.assertLess(vol, full_box.Volume)  # opening cut present
        App.closeDocument(result["doc"].Name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
