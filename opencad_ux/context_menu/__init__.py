# -*- coding: utf-8 -*-
"""Selection -> contextual actions (pure decision logic).

Given the current selection (objects and optional sub-element names such as
face/edge hints) this module decides which canonical commands are the most
relevant, mirroring Fusion 360's context toolbar.  GUI rendering lives in
:mod:`opencad_ux.context_menu.panel`.
"""

# canonical ids considered "create from sketch/body" candidates
SKETCH_ACTIONS = ["pad", "revolve", "loft", "sweep"]
BODY_ACTIONS = ["pad", "fillet", "chamfer", "thickness", "hole", "mirror",
                "linear_pattern", "circular_pattern"]
SOLID_ACTIONS = ["boolean_union", "boolean_cut", "boolean_intersection",
                 "interference", "mass_properties", "bounding_box", "refine"]
FACE_ACTIONS = ["pad", "pocket", "hole", "offset_face", "fillet"]
EDGE_ACTIONS = ["fillet", "chamfer"]
IMAGE_ACTIONS = ["calibrate_ref_image", "ref_image_transparency",
                 "ref_image_lock", "ref_image_hide"]

OBJECT_IMAGE_TYPES = ("Image::ImagePlane",)


def classify_object(obj):
    """Return a set of semantic tags for a FreeCAD object (string-safe)."""
    tags = set()
    type_name = getattr(obj, "TypeId", None) or ""
    if type_name == "Sketcher::SketchObject" or type_name.endswith("SketchObject"):
        tags.add("sketch")
    if type_name.startswith("PartDesign::Body"):
        tags.add("body")
    if type_name.startswith("PartDesign::") and type_name != "PartDesign::Body":
        tags.add("pd_feature")
    if type_name.startswith("Part::") or type_name.startswith("PartDesign::"):
        tags.add("shape")
    if type_name in OBJECT_IMAGE_TYPES:
        tags.add("image")
    return tags


def _subelement_kinds(subelements):
    kinds = set()
    for sub in subelements or []:
        s = str(sub or "").lower()
        if s.startswith("face"):
            kinds.add("face")
        elif s.startswith("edge"):
            kinds.add("edge")
        elif s.startswith("vertex"):
            kinds.add("vertex")
    return kinds


def context_actions_for(selection, subelements=None):
    """selection: list of objects (possibly []). Returns an ordered list of
    canonical command ids relevant for the current selection."""
    sub = _subelement_kinds(subelements)
    tags = set()
    for obj in selection or []:
        tags |= classify_object(obj)

    if not selection:
        actions = ["new_sketch", "import_ref_image", "box", "cylinder", "sphere",
                   "command_search"]
    elif "image" in tags:
        actions = list(IMAGE_ACTIONS)
    elif len(selection) >= 2:
        multi = True
        for o in selection:
            ot = classify_object(o)
            if not ({"shape", "body"} & ot):
                multi = False
                break
        if multi:
            actions = ["boolean_union", "boolean_cut", "boolean_intersection",
                       "interference"]
        else:
            actions = ["command_search"]
    elif sub and "face" in sub and "shape" in tags:
        actions = ["pad", "hole", "offset_face", "fillet"]
    elif sub and "edge" in sub:
        actions = ["fillet", "chamfer"]
    elif "sketch" in tags:
        actions = ["pad", "pocket", "revolve", "loft", "sweep", "new_sketch"]
    elif "body" in tags:
        actions = list(BODY_ACTIONS)
    elif "shape" in tags:
        actions = list(SOLID_ACTIONS)
    else:
        actions = ["command_search"]
    seen = set()
    return [a for a in actions if not (a in seen or seen.add(a))]
