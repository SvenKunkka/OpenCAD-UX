# -*- coding: utf-8 -*-
"""Shared parametric building blocks for the example consumer-electronics
models.  Uses the public FreeCAD python API (PartDesign features for the
editable history + OCC shape finishing via Part.Shape.makeThickness /
makeFillet for shell/fillets that have no headless feature API).
"""

import math


def new_doc(name):
    import FreeCAD as App

    return App.newDocument(name)


def body_plane(body, suffix="XY_Plane"):
    origin = body.getObject("Origin")
    for p in origin.OutList:
        if p.Name.endswith(suffix):
            return p
    raise RuntimeError("origin plane %s not found" % suffix)


def new_body(doc, name):
    body = doc.addObject("PartDesign::Body", name)
    doc.recompute()
    return body


def add_rect_sketch(body, name, width, height, plane="XY", center=(0, 0)):
    """Rectangle sketch (4 lines, closed with coincident constraints)."""
    import FreeCAD as App
    import Part
    import Sketcher

    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(body_plane(body, plane + "_Plane"), "")]
    sk.MapMode = "FlatFace"
    cx, cy = center
    x0, y0 = cx - width / 2.0, cy - height / 2.0
    x1, y1 = cx + width / 2.0, cy + height / 2.0
    segs = [Part.LineSegment(App.Vector(x0, y0, 0), App.Vector(x1, y0, 0)),
            Part.LineSegment(App.Vector(x1, y0, 0), App.Vector(x1, y1, 0)),
            Part.LineSegment(App.Vector(x1, y1, 0), App.Vector(x0, y1, 0)),
            Part.LineSegment(App.Vector(x0, y1, 0), App.Vector(x0, y0, 0))]
    for s in segs:
        sk.addGeometry(s, False)
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
    return sk


def add_circle_sketch(body, name, r, cx, cy, plane="XY"):
    import FreeCAD as App
    import Part
    import Sketcher

    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(body_plane(body, plane + "_Plane"), "")]
    sk.MapMode = "FlatFace"
    sk.addGeometry(Part.Circle(App.Vector(cx, cy, 0),
                               App.Vector(0, 0, 1), r), False)
    return sk


def add_ellipse_sketch(body, name, rx, ry, plane="XY"):
    import FreeCAD as App
    import Part
    import Sketcher

    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(body_plane(body, plane + "_Plane"), "")]
    sk.MapMode = "FlatFace"
    sk.addGeometry(Part.Ellipse(App.Vector(0, 0, 0), rx, ry), False)
    return sk


def pad_sketch(body, sketch, length, name="Pad"):
    pad = body.newObject("PartDesign::Pad", name)
    pad.Profile = sketch
    pad.Length = float(length)
    try:
        pad.SideType = "One side"
    except Exception:
        pass
    return pad


def pocket_sketch(body, sketch, length, name="Pocket"):
    pocket = body.newObject("PartDesign::Pocket", name)
    pocket.Profile = sketch
    pocket.Length = float(length)
    return pocket


def finish_fillet(shape, radius, edge_filter=None, max_edges=None,
                   safe=True):
    """Return a new solid with the selected edges filleted (OCC).  In safe
    mode a failing OCC operation returns the input shape unchanged instead of
    aborting the whole model."""
    edges = list(shape.Edges)
    if edge_filter is not None:
        edges = [e for e in edges if edge_filter(e)]
    if max_edges:
        edges = edges[:max_edges]
    if not edges:
        return shape
    try:
        return shape.makeFillet(float(radius), edges)
    except Exception:
        if safe:
            return shape
        raise


def finish_shell(shape, remove_face_filter, thickness, tolerance=0.1):
    """Return a shelled solid: remove face(s) matching the filter, then
    offset ``thickness`` (positive shrinks inward)."""
    faces = [f for f in shape.Faces if remove_face_filter(f)]
    if not faces:
        return shape
    return shape.makeThickness(faces, float(thickness), float(tolerance))


def face_by_z(shape, z, tol=0.5):
    out = []
    for i, f in enumerate(shape.Faces):
        if abs(f.CenterOfMass.z - z) < tol:
            out.append(f)
    return out


def edge_vertical(shape, length, tol=0.1):
    return [e for e in shape.Edges
            if abs(e.Vertexes[0].Point.z - e.Vertexes[1].Point.z) > length - tol]


def make_part_feature(doc, label, solid):
    """Wrap a plain solid into a document Part::Feature (non-parametric copy,
    used for OCC finishing steps)."""
    obj = doc.addObject("Part::Feature", label)
    obj.Shape = solid
    obj.Label = label
    return obj
