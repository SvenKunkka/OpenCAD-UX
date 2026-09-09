# -*- coding: utf-8 -*-
"""Document/geometry exporters and analysis helpers.

Everything in this module runs with the *public* FreeCAD python API and no
GUI, so it is exercised by the headless test-suite and reused by the GUI
commands (export STEP/STL/OBJ/DXF, bounding box, mass properties,
interference check).
"""

import os


class ExportError(RuntimeError):
    pass


def get_exportable_objects(doc, selected=None, only_solids=True):
    """Return document objects that carry a usable ``Shape``."""
    out = []
    objs = selected if selected else list(doc.Objects)
    for obj in objs:
        if not hasattr(obj, "Shape") or obj.Shape is None:
            continue
        if only_solids and obj.Shape.ShapeType not in ("Solid", "Compound", "CompSolid"):
            # allow compounds that contain solids (Bodies export their final shape)
            if obj.Shape.Solids is None or not obj.Shape.Solids:
                continue
        out.append(obj)
    return out


def _require_doc(doc):
    if doc is None:
        raise ExportError("no active document")


# --- STEP / IGES -----------------------------------------------------------

def export_step(doc, path, selected=None):
    _require_doc(doc)
    objs = get_exportable_objects(doc, selected)
    if not objs:
        raise ExportError("nothing to export (no shape objects)")
    import Part  # noqa

    Part.export(objs, path)
    return path


# --- STL / OBJ (mesh based) ------------------------------------------------

def _meshes_for(objs, deflection=0.1):
    """Build a Mesh per object from OCC tessellation (no MeshPart dependency;
    MeshPart.meshFromShape aborts on some 1.1 builds)."""
    import FreeCAD as App  # noqa
    import Mesh  # noqa

    meshes = []
    for obj in objs:
        shape = obj.Shape
        if shape.isNull():
            continue
        pts, tris = shape.tessellate(deflection)
        if not tris:
            continue
        mesh = Mesh.Mesh()
        facets = [[App.Vector(*pts[i]) for i in t] for t in tris]
        mesh.addFacets(facets)
        meshes.append(mesh)
    return meshes


def export_stl(doc, path, selected=None):
    _require_doc(doc)
    objs = get_exportable_objects(doc, selected)
    if not objs:
        raise ExportError("nothing to export (no shape objects)")
    import Mesh  # noqa

    meshes = _meshes_for(objs)
    if not meshes:
        raise ExportError("failed to build mesh from shapes")
    combined = meshes[0]
    for m in meshes[1:]:
        combined.addMesh(m)
    combined.write(path)
    return path


def export_obj(doc, path, selected=None):
    _require_doc(doc)
    objs = get_exportable_objects(doc, selected)
    if not objs:
        raise ExportError("nothing to export (no shape objects)")
    import Mesh  # noqa

    meshes = _meshes_for(objs)
    if not meshes:
        raise ExportError("failed to build mesh from shapes")
    combined = meshes[0]
    for m in meshes[1:]:
        combined.addMesh(m)
    combined.write(path, "OBJ")
    return path


# --- DXF (2D outlines) ------------------------------------------------------

def export_dxf(doc, path, selected=None):
    """Export 2D geometry to DXF through the Draft module (headless-safe)."""
    _require_doc(doc)
    objs = selected or [o for o in doc.Objects
                        if hasattr(o, "Shape") and o.Shape is not None and not o.Shape.isNull()]
    if not objs:
        raise ExportError("nothing to export")
    try:
        import Draft  # noqa

        Draft.export(objs, path)
    except Exception as exc:
        # Draft import/export of DXF needs the (older) ODA converter on some
        # platforms; report the real cause instead of pretending success.
        raise ExportError("DXF export failed: %s" % exc)
    return path


# --- STEP import ------------------------------------------------------------

def import_step(path, doc=None):
    if not os.path.isfile(path):
        raise ExportError("file not found: %s" % path)
    import Import  # noqa

    if doc is None:
        name = os.path.splitext(os.path.basename(path))[0]
        doc = __import__("FreeCAD", fromlist=["newDocument"]).newDocument(name)
    Import.insert(path, doc.Name)
    doc.recompute()
    return doc


# --- inspection reports -----------------------------------------------------

def report_bounding_box(objects):
    if not objects:
        raise ExportError("no objects selected")
    lines = ["Bounding boxes:"]
    for obj in objects:
        bb = obj.Shape.BoundBox
        lines.append("  %s : X %.3f..%.3f  Y %.3f..%.3f  Z %.3f..%.3f"
                     % (obj.Label, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    return "\n".join(lines)


def report_mass_properties(objects, density_g_cm3=1.02):
    """density default 1.02 g/cm^3 (ABS). Returns rows + text."""
    if not objects:
        raise ExportError("no objects selected")
    rows = []
    for obj in objects:
        shape = obj.Shape
        volume_mm3 = shape.Volume  # mm^3
        area_mm2 = shape.Area
        cm3 = volume_mm3 / 1000.0
        mass_g = cm3 * density_g_cm3
        rows.append({
            "label": obj.Label, "volume_mm3": volume_mm3, "area_mm2": area_mm2,
            "mass_g": mass_g, "density_g_cm3": density_g_cm3,
        })
    lines = ["Mass properties (density %.2f g/cm^3):" % density_g_cm3]
    for r in rows:
        lines.append("  %s: volume %10.1f mm^3 | area %10.1f mm^2 | mass %8.2f g"
                     % (r["label"], r["volume_mm3"], r["area_mm2"], r["mass_g"]))
    return "\n".join(lines)


def report_interference(objects, tolerance=1e-6):
    """Detect overlapping volume between solid objects (public API only)."""
    if len(objects) < 2:
        raise ExportError("select at least two solids to check interference")
    pairs = []
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            a, b = objects[i], objects[j]
            common = a.Shape.common(b.Shape)
            vol = common.Volume if common and not common.isNull() else 0.0
            if vol > tolerance:
                pairs.append((a.Label, b.Label, vol))
    if not pairs:
        return "No interference detected between the selected solids."
    lines = ["Interference detected:"]
    for a, b, vol in pairs:
        lines.append("  %s <-> %s : overlapping volume %.3f mm^3" % (a, b, vol))
    return "\n".join(lines)
