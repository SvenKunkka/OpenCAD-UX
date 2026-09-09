# -*- coding: utf-8 -*-
"""Example 2: mouse concept shell (ergonomic-ish, low poly).

Elliptical base pad -> bottom-open shell -> finger scoop carved on top with a
boolean (sphere) -> scroll-well slot cut.  Pure python/Part API so it runs
headless; all dims are module constants.
"""

from . import model_lib as ml

LENGTH = 118.0        # mouse length (x)
WIDTH = 66.0          # width (y)
HEIGHT = 24.0         # height at the hump
WALL = 2.0
HUMPS = 0.35          # extra height factor of the top scoop geometry


def build(doc=None):
    import FreeCAD as App
    import Part

    doc = doc or ml.new_doc("mouse_shell")
    body = ml.new_body(doc, "MouseShell")
    sk = ml.add_ellipse_sketch(body, "SketchBase", LENGTH / 2.0, WIDTH / 2.0)
    pad = ml.pad_sketch(body, sk, HEIGHT, "PadBase")
    doc.recompute()
    base = pad.Shape
    # shell: remove the bottom face -> hollow shell open at the bottom
    tray = ml.finish_shell(base,
                           lambda f: f.CenterOfMass.z < 0.5 and
                           f.normalAt(0.5, 0.5).z < -0.9,
                           WALL)
    # carve a finger scoop into the top by subtracting an ellipsoid (sphere
    # scaled along x), then cut a scroll-well slot near the front
    scoop_center = App.Vector(LENGTH * 0.05, 0, HEIGHT + 8)
    scoop = Part.makeSphere(16.0, scoop_center)
    m = App.Matrix()
    m.scale(App.Vector(2.0, 1.2, 0.8))
    scoop = scoop.transformGeometry(m)
    carved = tray.cut(scoop)
    slot = Part.makeBox(3.0, 14.0, HEIGHT + 4, App.Vector(LENGTH / 2.0 - 1.5,
                                                          -7.0, -1.0))
    finished = carved.cut(slot)
    ml.make_part_feature(doc, "MouseShell_Finished", finished)
    doc.recompute()
    return {"doc": doc, "body": body, "pad": pad,
            "finished_solid": finished}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    result = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "mouse_shell.FCStd"
    result["doc"].saveAs(out)
    print("saved", out)
