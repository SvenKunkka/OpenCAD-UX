# -*- coding: utf-8 -*-
"""Example 1: simple mechanical keyboard shell (open-bottom tray).

A 60%-style rectangular case: parametric outline pad -> shelled (bottom
removed) -> filleted top edges.  Sizes are module constants so the model is
easy to change (units: mm).
"""

from . import model_lib as ml

# --- editable parameters ---------------------------------------------------
WIDTH = 300.0          # overall width of the case
DEPTH = 100.0          # overall depth
HEIGHT = 14.0          # overall height
WALL = 2.0             # wall/floor thickness after shelling
VERTEX_RADIUS = 2.0    # vertical corner fillet radius
TOP_RADIUS = 1.5       # top-edge fillet radius


def build(doc=None):
    """Build the keyboard shell inside ``doc`` (new doc when None)."""
    doc = doc or ml.new_doc("keyboard_shell")
    body = ml.new_body(doc, "KeyboardShell")
    sketch = ml.add_rect_sketch(body, "SketchCaseOutline", WIDTH, DEPTH)
    pad = ml.pad_sketch(body, sketch, HEIGHT, "PadCase")
    doc.recompute()
    solid = pad.Shape
    # shell with the bottom face removed -> open-bottom tray
    tray = ml.finish_shell(
        solid,
        lambda f: f.CenterOfMass.z < 0.5 and f.normalAt(0.5, 0.5).z < -0.9,
        WALL)
    # fillet the vertical corners (safe: never aborts the model), then the
    # top ring with a gentler radius suited to the wall thickness
    verts = ml.edge_vertical(tray, HEIGHT * 0.6)
    cornered = ml.finish_fillet(tray, VERTEX_RADIUS,
                                edge_filter=lambda e: e in verts)
    top_ring = [e for e in cornered.Edges
                if e.Vertexes[0].Point.z > HEIGHT - WALL + 0.01 and
                e.Vertexes[1].Point.z > HEIGHT - WALL + 0.01]
    finished = ml.finish_fillet(cornered, TOP_RADIUS,
                                edge_filter=lambda e: e in top_ring,
                                max_edges=8)
    feature = ml.make_part_feature(doc, "KeyboardShell_Finished", finished)
    doc.recompute()
    return {"doc": doc, "body": body, "pad": pad, "feature": feature,
            "finished_solid": finished}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    result = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "keyboard_shell.FCStd"
    result["doc"].saveAs(out)
    print("saved", out)
