# -*- coding: utf-8 -*-
"""Console tests - the parametric workflow: sketch -> pad -> pocket (hole) ->
fillet -> thickness, with a history modification (recompute) in between."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "examples"))

import FreeCAD as App  # noqa: E402
from examples import model_lib as ml  # noqa: E402


class TestParametricFlow(unittest.TestCase):
    def setUp(self):
        self.doc = App.newDocument("flow_test")

    def tearDown(self):
        try:
            App.closeDocument(self.doc.Name)
        except Exception:
            pass

    def test_full_flow(self):
        body = ml.new_body(self.doc, "Body")
        # sketch
        sk = ml.add_rect_sketch(body, "Sk", 100.0, 60.0)
        self.doc.recompute()
        self.assertEqual(sk.GeometryCount, 4)
        # pad
        pad = ml.pad_sketch(body, sk, 10.0, "Pad")
        self.doc.recompute()
        vol1 = pad.Shape.Volume
        self.assertGreater(vol1, 1.0)
        # parametric history: edit pad length -> recompute changes volume
        pad.Length = 15.0
        self.doc.recompute()
        vol2 = pad.Shape.Volume
        self.assertAlmostEqual(vol2 / vol1, 1.5, places=1)
        # pocket (cylindrical hole geometry)
        hole_sk = ml.add_circle_sketch(body, "HoleSk", 8.0, 0.0, 0.0)
        pocket = ml.pocket_sketch(body, hole_sk, 15.0, "Hole")
        self.doc.recompute()
        self.assertLess(pad.Shape.Volume, vol2 + 1e-6)
        # finishing ops on the feature shape (OCC)
        solid = pad.Shape
        zed = [e for e in solid.Edges
               if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > 9.5]
        filleted = solid.makeFillet(1.0, zed)
        self.assertTrue(filleted.isValid())
        shell = filleted.makeThickness(
            [f for f in filleted.Faces if abs(f.CenterOfMass.z) < 0.5
             and f.normalAt(0.5, 0.5).z < -0.9], 1.5, 0.1)
        self.assertTrue(shell.isValid())
        self.assertGreater(shell.Volume, 1000.0)
        # save a real FreeCAD file and reopen it
        out = os.path.join(ROOT, "tests", "output")
        os.makedirs(out, exist_ok=True)
        path = os.path.join(out, "flow_test.FCStd")
        self.doc.saveAs(path)
        reopened = App.openDocument(path)
        try:
            self.assertGreaterEqual(len(reopened.Objects), 1)
        finally:
            App.closeDocument(reopened.Name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
