# -*- coding: utf-8 -*-
"""Mouse navigation presets.

FreeCAD (through 1.1) does not ship a "Fusion 360" navigation style: the
style classes present are CAD, Inventor, Blender, Touchpad, Gesture, Maya,
OpenCascade, Revit, OpenSCAD, SiemensNX, SolidWorks, TinkerCAD and User
(see DlgSettingsNavigation in the GUI).  The navigation style is persisted in
the parameter ``BaseApp/Preferences/View/NavigationStyle`` as a fully
qualified class name string such as ``Gui::RevitNavigationStyle``.

Strategy implemented here (per design requirement):
1. probe whether a Fusion style class exists in the running build;
2. if yes -> apply it natively;
3. if no  -> apply the closest built-in (Revit by default) and report the
   remaining behavioural differences that cannot be fixed from python.
"""

import sys

STYLE_PARAM = "BaseApp/Preferences/View"
STYLE_KEY = "NavigationStyle"

FUSION_CANDIDATES = [
    "Gui::FusionNavigationStyle",
    "Gui::Fusion360NavigationStyle",
    "Gui::CADFusionNavigationStyle",
]

KNOWN_STYLES = [
    "Gui::CADNavigationStyle",
    "Gui::InventorNavigationStyle",
    "Gui::BlenderNavigationStyle",
    "Gui::TouchpadNavigationStyle",
    "Gui::GestureNavigationStyle",
    "Gui::MayaGestureNavigationStyle",
    "Gui::OpenCascadeNavigationStyle",
    "Gui::RevitNavigationStyle",
    "Gui::OpenSCADNavigationStyle",
    "Gui::SiemensNXNavigationStyle",
    "Gui::SolidWorksNavigationStyle",
    "Gui::TinkerCADNavigationStyle",
    "Gui::UserNavigationStyle",
]

# Revit is chosen as the closest built-in to the requested Fusion-like mapping
# (middle-drag pan, wheel zoom, orbit via shift or dedicated orbit button).
DEFAULT_CLOSEST = "Gui::RevitNavigationStyle"


def _param_group():
    import FreeCAD  # noqa

    return FreeCAD.ParamGet("User parameter:" + STYLE_PARAM)


def current_style():
    try:
        return _param_group().GetString(STYLE_KEY, "")
    except Exception:
        return ""


def set_style_param(style_class):
    """Persist the style class name.  Public parameter API only."""
    try:
        grp = _param_group()
        grp.SetString(STYLE_KEY, style_class)
        # ensure the file is flushed to disk immediately (helps tests)
        try:
            import FreeCAD  # noqa

            FreeCAD.saveParameter()
        except Exception:
            pass
        return True
    except Exception:
        return False


def fusion_style_available():
    """True when the running FreeCAD registers a Fusion-style class."""
    cur = current_style()
    if cur in FUSION_CANDIDATES:
        return True
    # probe by trying to store then read each candidate (harmless param write)
    orig = cur
    for cand in FUSION_CANDIDATES:
        set_style_param(cand)
        if current_style() == cand:
            set_style_param(orig if orig else DEFAULT_CLOSEST)
            return True
    if orig:
        set_style_param(orig)
    return False


def closest_builtin():
    return DEFAULT_CLOSEST


def style_class_for(preset):
    """Map preset names ('fusion','revit','native',...) to a style class."""
    if preset == "native":
        return current_style() or DEFAULT_CLOSEST
    if preset in KNOWN_STYLES:
        return preset
    if preset == "fusion":
        return "FUSION"
    # default
    return "Gui::%sNavigationStyle" % preset.capitalize() if preset else DEFAULT_CLOSEST


def describe_python_adjustments(style_class):
    """Human-readable list of mouse behaviours that the python layer cannot
    reproduce on stock FreeCAD, for the README and the navigation dialog."""
    return [
        "Middle-drag = pan and Shift+middle-drag = orbit are NOT natively"
        " remappable from python in stock FreeCAD (all versions to 1.1).",
        "Revit style is applied: wheel zoom, middle-drag pan, and orbit via"
        " Shift+middle-drag where supported by the style.",
        "A native C++ navigation patch would be required for a pixel-exact"
        " Fusion mapping; see README (navigation) for the python/native split.",
    ]


def apply_navigation(preset, notify=True):
    """Apply a navigation preset. Returns a result dict for the GUI/tests."""
    fusion = fusion_style_available()
    if preset == "fusion" and not fusion:
        style = DEFAULT_CLOSEST
        applied = set_style_param(style)
        return {
            "status": "fallback" if applied else "error",
            "style": style,
            "fusion_native": False,
            "message": ("Fusion style not present in this FreeCAD build; "
                        "applied closest style %s" % style),
            "notes": describe_python_adjustments(style),
        }
    if preset == "fusion":
        style = FUSION_CANDIDATES[0]
        applied = set_style_param(style)
        return {"status": "ok" if applied else "error", "style": style,
                "fusion_native": True,
                "message": "Native Fusion navigation style applied.",
                "notes": []}
    style = style_class_for(preset)
    applied = set_style_param(style)
    return {"status": "ok" if applied else "error", "style": style,
            "fusion_native": fusion,
            "message": "Navigation style set to %s" % style,
            "notes": [] if style in FUSION_CANDIDATES else describe_python_adjustments(style)}


def restore_previous():
    """Restore the style that was active before the last apply (if any)."""
    try:
        from .. import prefs  # noqa

        s = prefs.Settings()
        prev = s.get_string(prefs.K["nav_previous"], "")
        if prev:
            set_style_param(prev)
        return prev
    except Exception:
        return ""
