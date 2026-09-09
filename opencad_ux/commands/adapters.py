# -*- coding: utf-8 -*-
"""Canonical command id -> real FreeCAD command candidates.

FreeCAD has renamed commands over 0.20 .. 1.1 (e.g. ``Sketcher_CreateLine``
vs legacy ``Sketcher_Line``, ``Sketcher_Projection`` vs legacy
``Sketcher_External``).  Each canonical id used by the UI is resolved at
runtime to the *first candidate present in the running FreeCAD* so one
ribbon/keymap definition works across versions.

Commands that FreeCAD cannot perform natively (or only through the GUI) get a
python fallback implemented in :mod:`opencad_ux.commands.python_commands` or
a clearly-messaged "not available via public API" handler.
"""

# canonical -> ordered native FreeCAD command candidates (newest first)
NATIVE = {
    # ---- sketch ---------------------------------------------------------
    "new_sketch": ["Sketcher_NewSketch"],
    "line": ["Sketcher_CreateLine", "Sketcher_Line"],
    "rectangle": ["Sketcher_CreateRectangle", "Sketcher_Rectangle"],
    "circle": ["Sketcher_CreateCircle", "Sketcher_Circle"],
    "arc": ["Sketcher_CreateArc", "Sketcher_Arc"],
    "spline": ["Sketcher_CreateBSpline", "Sketcher_BSpline"],
    "trim": ["Sketcher_Trimming"],
    "offset": ["Sketcher_Offset"],
    "project": ["Sketcher_Projection", "Sketcher_External"],
    "dimension": ["Sketcher_Dimension", "Sketcher_ConstrainDistance"],
    # ---- constraints (direct ids) --------------------------------------
    "Sketcher_ConstrainCoincident": ["Sketcher_ConstrainCoincident"],
    "Sketcher_ConstrainHorizontal": ["Sketcher_ConstrainHorizontal"],
    "Sketcher_ConstrainVertical": ["Sketcher_ConstrainVertical"],
    "Sketcher_ConstrainTangent": ["Sketcher_ConstrainTangent"],
    "Sketcher_ConstrainPerpendicular": ["Sketcher_ConstrainPerpendicular"],
    "Sketcher_ConstrainParallel": ["Sketcher_ConstrainParallel"],
    "Sketcher_ConstrainLock": ["Sketcher_ConstrainLock"],
    "Sketcher_NewSketch": ["Sketcher_NewSketch"],
    "PartDesign_Pad": ["PartDesign_Pad"],
    # ---- create ---------------------------------------------------------
    "box": ["PartDesign_AdditiveBox", "Part_Box", "Part_Box_Parametric"],
    "cylinder": ["PartDesign_AdditiveCylinder", "Part_Cylinder", "Part_Cylinder_Parametric"],
    "sphere": ["PartDesign_AdditiveSphere", "Part_Sphere", "Part_Sphere_Parametric"],
    "pad": ["PartDesign_Pad"],
    "revolve": ["PartDesign_Revolution", "Part_Revolve"],
    "sweep": ["PartDesign_AdditivePipe", "Part_Sweep"],
    "loft": ["PartDesign_AdditiveLoft", "Part_Loft"],
    "hole": ["PartDesign_Hole"],
    # ---- modify ---------------------------------------------------------
    "fillet": ["PartDesign_Fillet", "Part_Fillet"],
    "chamfer": ["PartDesign_Chamfer", "Part_Chamfer"],
    "thickness": ["PartDesign_Thickness", "Part_Thickness"],
    "draft_angle": ["PartDesign_Draft", "Part_Draft"],
    "mirror": ["PartDesign_Mirrored"],
    "linear_pattern": ["PartDesign_LinearPattern"],
    "circular_pattern": ["PartDesign_PolarPattern"],
    "move_face": [],
    "offset_face": [],
    "transform": ["Std_Transform"],
    # ---- combine --------------------------------------------------------
    "boolean_union": ["Part_Union", "Part_Boolean"],
    "boolean_cut": ["Part_Cut", "Part_Boolean"],
    "boolean_intersection": ["Part_Common", "Part_Boolean"],
    "split_body": ["Part_SliceApart", "Part_Slice"],
    "slice": ["Part_Slice", "Part_SliceApart"],
    "refine": ["Part_RefineShape"],
    # ---- inspect --------------------------------------------------------
    "measure": ["Std_Measure"],
    "section_view": ["Part_SectionCut", "Part_CrossSections"],
    "bounding_box": [],
    "mass_properties": [],
    "geometry_check": ["Part_CheckGeometry"],
    "interference": [],
    # ---- insert/export --------------------------------------------------
    "import_ref_image": [],
    "import_step": ["Std_Import"],
    "export_step": ["Std_Export"],
    "export_stl": ["Std_Export"],
    "export_obj": ["Std_Export"],
    "export_dxf": ["Std_Export"],
    # ---- keyboard preset targets ----------------------------------------
    "fit_all": ["Std_ViewFitAll"],
    "delete": ["Std_Delete"],
    "undo": ["Std_Undo"],
    "redo": ["Std_Redo"],
    "save": ["Std_Save"],
    "open": ["Std_Open"],
    "new_document": ["Std_New"],
}

# canonical ids implemented by OpenCAD UX python commands
PYTHON_COMMANDS = {
    "command_search": "OpencadUX_CommandSearch",
    "context_actions": "OpencadUX_ContextMenu",
    "move_face": "OpencadUX_MoveFace",
    "offset_face": "OpencadUX_OffsetFace",
    "bounding_box": "OpencadUX_BoundingBox",
    "mass_properties": "OpencadUX_MassProperties",
    "interference": "OpencadUX_Interference",
    "import_ref_image": "OpencadUX_ImportReferenceImage",
    "import_step": "OpencadUX_ImportStep",
    "export_step": "OpencadUX_ExportStep",
    "export_stl": "OpencadUX_ExportStl",
    "export_obj": "OpencadUX_ExportObj",
    "export_dxf": "OpencadUX_ExportDxf",
}

# canonical ids that have no public-API implementation on stock FreeCAD
NOT_AVAILABLE_MSG = {
    "move_face": (
        "FreeCAD (stock, through 1.1) exposes no public-API command that "
        "moves a single face of a solid the way Fusion 360 does. Please use "
        "'Transform' (M) or edit the source sketch instead."
    ),
    "offset_face": (
        "FreeCAD (stock, through 1.1) exposes no public-API command that "
        "offsets a single face of a solid. The closest features are "
        "'Shell/Thickness' and editing the source sketch."
    ),
}


def candidates_for(canonical):
    """Ordered FreeCAD command ids to try for a canonical id (may be empty)."""
    if canonical in NATIVE:
        return list(NATIVE[canonical])
    # assume the canonical itself is a real FreeCAD command id
    return [canonical]


def python_command_name(canonical):
    return PYTHON_COMMANDS.get(canonical)


def not_available_reason(canonical):
    return NOT_AVAILABLE_MSG.get(canonical)


def resolve_canonical(canonical, available_ids=None):
    """Pick the first candidate id present in ``available_ids``.

    With ``available_ids=None`` the first candidate is assumed available
    (callers that run a command receive FreeCAD's own feedback when it is
    not); the GUI checks availability through ``FreeCADGui.listCommands()``.
    """
    for cand in candidates_for(canonical):
        if available_ids is None or cand in available_ids:
            return cand
    return None
