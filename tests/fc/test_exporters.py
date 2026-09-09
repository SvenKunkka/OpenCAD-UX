# -*- coding: utf-8 -*-
"""Console tests - exporters, STEP/STL/OBJ, import STEP, analysis reports."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import FreeCAD as App  # noqa: E402
from opencad_ux.commands import exporters  # noqa: E402


class TestExporters(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("exp")
        self.a = self.doc.addObject("Part::Box", "A")
        self.a.Length = 20
        self.a.Width = 20
        self.a.Height = 20
        self.b = self.doc.addObject("Part::Cylinder", "B")
        self.b.Radius = 8
        self.b.Height = 30
        self.b.Placement.Base = App.Vector(30, 0, 0)
        self.doc.recompute()
        self.out = os.path.join(ROOT, "tests", "output")
        os.makedirs(self.out, exist_ok=True)

    def tearDown(self):
        try:
            App.closeDocument(self.doc.Name)
        except Exception:
            pass

    def test_step(self):
        p = os.path.join(self.out, "exp.step")
        exporters.export_step(self.doc, p)
        self.assertGreater(os.path.getsize(p), 1000)
        # round-trip import
        doc2 = exporters.import_step(p)
        try:
            self.assertGreaterEqual(len(doc2.Objects), 1)
        finally:
            App.closeDocument(doc2.Name)

    def test_stl_and_obj(self):
        p = os.path.join(self.out, "exp.stl")
        exporters.export_stl(self.doc, p)
        self.assertGreater(os.path.getsize(p), 1000)
        po = os.path.join(self.out, "exp.obj")
        exporters.export_obj(self.doc, po)
        self.assertGreater(os.path.getsize(po), 1000)

    def test_reports(self):
        shapes = exporters.get_exportable_objects(self.doc)
        self.assertEqual(len(shapes), 2)
        bb = exporters.report_bounding_box(shapes)
        self.assertIn("A", bb)
        mass = exporters.report_mass_properties(shapes)
        self.assertIn("volume", mass.lower())
        inter = exporters.report_interference(shapes)
        self.assertIn("No interference", inter)
        # overlapping pair -> detected
        self.b.Placement.Base = App.Vector(0, 0, 0)
        self.doc.recompute()
        inter2 = exporters.report_interference(shapes)
        self.assertIn("Interference detected", inter2)


class TestErrors(unittest.TestCase):
    def test_no_doc(self):
        with self.assertRaises(Exception):
            exporters.export_step(None, "/tmp/x.step")

    def test_missing_file(self):
        with self.assertRaises(Exception):
            exporters.import_step("/nonexistent/file.step")


if __name__ == "__main__":
    unittest.main(verbosity=2)
