#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate the original SVG icon set (light + dark) for OpenCAD UX.

The glyphs are simple geometric drawings authored here - no Autodesk or other
proprietary assets.  Regenerate any time ribbon.json / icon names change:

    python3 scripts/make_icons.py [output_root]
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RIBBON = os.path.join(ROOT, "resources", "ribbon.json")
ICON_ROOT = os.path.join(ROOT, "resources", "icons")

STROKES = {"light": "#3d4552", "dark": "#c3cad4"}

# icon name -> list of explicit tuples:
#   ("l", (x1,y1), (x2,y2))            line
#   ("c", cx, cy, r)                   circle
#   ("r", x, y, w, h)                  rect
#   ("p", [(x,y), ...])                polyline (open)
#   ("g", [(x,y), ...])                polygon  (closed)
#   ("a", cx, cy, rx, ry, start, end)  arc
SHAPES = {
    # ---- sketch -------------------------------------------------------
    "new_sketch": [("p", [(14, 2), (20, 8), (8, 20), (2, 14)]),
                   ("p", [(2, 14), (4, 10), (14, 2)]),
                   ("r", 12, 12, 8, 8)],
    "line": [("l", (6, 24), (24, 6))],
    "rectangle": [("r", 5, 6, 20, 16)],
    "circle": [("c", 15, 15, 9)],
    "arc": [("a", 13, 20, 10, 10, 205, 335), ("l", (13, 20), (15, 4)),
            ("p", [(10, 7), (15, 1), (20, 7)])],
    "spline": [("p", [(4, 19), (10, 5), (16, 25), (26, 9)])],
    "trim": [("l", (14, 4), (26, 20)), ("l", (26, 4), (14, 20)),
             ("l", (4, 26), (24, 6))],
    "offset": [("p", [(2, 22), (8, 10), (14, 14), (18, 8)]),
               ("p", [(6, 26), (12, 14), (18, 18), (24, 10)])],
    "project": [("p", [(5, 15), (5, 26), (26, 26), (26, 15)]),
                ("l", (15, 15), (15, 5)),
                ("c", 15, 3, 2),
                ("p", [(10, 15), (10, 22), (20, 22), (20, 15)])],
    "dimension": [("l", (5, 5), (5, 24)), ("l", (22, 5), (22, 24)),
                  ("l", (5, 15), (22, 15)),
                  ("l", (9, 11), (9, 19)), ("l", (18, 11), (18, 19))],
    # ---- constraints ---------------------------------------------------
    "constrain_coincident": [("c", 9, 9, 4), ("c", 20, 20, 4)],
    "constrain_horizontal": [("l", (4, 8), (24, 8)),
                             ("p", [(19, 3), (24, 8), (19, 13)])],
    "constrain_vertical": [("l", (8, 4), (8, 24)),
                           ("p", [(3, 19), (8, 24), (13, 19)])],
    "constrain_tangent": [("p", [(4, 18), (12, 4), (16, 4)]),
                          ("p", [(24, 10), (24, 18), (16, 24)]),
                          ("l", (16, 4), (24, 10))],
    "constrain_perpendicular": [("l", (4, 20), (20, 4)),
                                ("l", (14, 8), (16, 10)),
                                ("l", (4, 20), (26, 24))],
    "constrain_parallel": [("l", (4, 6), (20, 12)), ("l", (4, 18), (24, 24)),
                           ("l", (20, 12), (24, 14))],
    "constrain_lock": [("r", 8, 12, 14, 11), ("p", [(11, 12), (11, 8),
                                                    (13, 5), (17, 5), (19, 8), (19, 12)])],
    # ---- create --------------------------------------------------------
    "box": [("p", [(5, 5), (22, 5), (22, 18), (5, 18)]),
            ("p", [(5, 5), (2, 21), (19, 25), (22, 18)]),
            ("l", (5, 18), (2, 21))],
    "cylinder": [("a", 14, 8, 9, 5, 0, 360), ("a", 14, 22, 9, 5, 0, 360),
                 ("l", (5, 8), (5, 22)), ("l", (23, 8), (23, 22))],
    "sphere": [("c", 15, 15, 10), ("a", 15, 15, 5, 10, 90, 270),
               ("a", 15, 15, 10, 5, 0, 360)],
    "pad": [("p", [(6, 25), (6, 10), (14, 4), (22, 10), (22, 25)]),
            ("l", (6, 10), (22, 10))],
    "revolve": [("p", [(14, 26), (14, 6)]), ("a", 14, 20, 9, 5, 195, 340),
                ("p", [(9, 8), (14, 2), (19, 8)])],
    "sweep": [("p", [(6, 22), (6, 14), (19, 14)]), ("c", 20, 14, 3.4),
              ("l", (23, 14), (26, 14)),
              ("p", [(9, 4), (5, 8), (9, 12)])],
    "loft": [("p", [(5, 5), (12, 5), (12, 23), (5, 23)]),
             ("p", [(14, 8), (24, 10), (20, 21), (12, 21)]),
             ("l", (12, 5), (14, 8)), ("l", (12, 23), (12, 21))],
    "hole": [("c", 15, 15, 9), ("c", 15, 15, 4.5)],
    # ---- modify ---------------------------------------------------------
    "fillet": [("p", [(5, 26), (5, 10), (10, 5), (26, 5), (26, 26)]),
               ("a", 5, 26, 21, 21, 90, 180)],
    "chamfer": [("p", [(5, 5), (23, 5), (23, 23), (5, 23)]),
                ("l", (5, 5), (23, 23))],
    "thickness": [("p", [(4, 7), (24, 7), (24, 25), (4, 25)]),
                  ("p", [(9, 7), (9, 19), (20, 19), (20, 7)]),
                  ("l", (4, 2), (24, 2))],
    "draft_angle": [("p", [(7, 4), (18, 4), (24, 25), (9, 25)]),
                    ("p", [(12, 8), (17, 8), (20, 20)]),
                    ("l", (4, 25), (26, 25))],
    "mirror": [("p", [(4, 6), (12, 6), (12, 22), (4, 22)]),
               ("p", [(14, 6), (26, 6), (26, 22), (14, 22)]),
               ("l", (14, 4), (14, 24))],
    "linear_pattern": [("p", [(6, 13), (6, 24), (17, 24), (17, 13)]),
                       ("p", [(16, 9), (16, 4), (25, 4), (25, 12)]),
                       ("p", [(10, 6), (13, 2), (20, 2), (23, 6)])],
    "circular_pattern": [("c", 15, 15, 10),
                         ("p", [(15, 15), (15, 4)]),
                         ("p", [(15, 4), (24, 9), (15, 15)])],
    "move_face": [("p", [(3, 16), (9, 3), (20, 8), (20, 18)]),
                  ("l", (20, 8), (26, 6)),
                  ("p", [(20, 18), (22, 23), (25, 21)])],
    "offset_face": [("p", [(4, 13), (12, 4), (24, 4), (24, 16), (16, 24), (4, 24)]),
                    ("p", [(10, 13), (14, 9), (21, 9)])],
    "transform": [("p", [(7, 3), (7, 21), (15, 26)]),
                  ("c", 9, 9, 2),
                  ("p", [(11, 5), (24, 12)]),
                  ("c", 20, 16, 2.6)],
    # ---- combine ---------------------------------------------------------
    "boolean_union": [("c", 11, 15, 8), ("c", 19, 15, 8)],
    "boolean_cut": [("c", 11, 15, 8),
                    ("p", [(14, 9), (24, 9), (24, 24), (14, 24)]),
                    ("l", (16, 13), (22, 20))],
    "boolean_intersection": [("c", 11, 15, 8), ("c", 19, 15, 8),
                             ("c", 15, 15, 3.4)],
    "split_body": [("r", 5, 5, 18, 18), ("l", (5, 5), (23, 23)),
                   ("c", 23, 5, 2.6), ("c", 5, 23, 2.6)],
    "slice": [("p", [(5, 4), (23, 4), (23, 24), (5, 24)]),
              ("p", [(9, 4), (20, 24)])],
    "refine": [("p", [(3, 21), (3, 7), (27, 7), (27, 21)]),
               ("l", (6, 14), (24, 14)),
               ("c", 9, 10, 2), ("c", 21, 10, 2), ("c", 15, 18, 2)],
    # ---- inspect ---------------------------------------------------------
    "measure": [("l", (4, 24), (22, 6)),
                ("p", [(18, 6), (22, 6), (22, 10)]),
                ("p", [(4, 20), (4, 24), (8, 24)])],
    "section_view": [("c", 15, 15, 11), ("l", (15, 4), (15, 26)),
                     ("l", (4, 15), (26, 15))],
    "bounding_box": [("p", [(7, 7), (24, 7), (24, 24), (7, 24)]),
                     ("p", [(7, 7), (2, 2), (19, 2), (24, 7)]),
                     ("l", (2, 22), (7, 24))],
    "mass_properties": [("c", 15, 15, 10), ("l", (15, 15), (22, 9))],
    "geometry_check": [("c", 15, 15, 11), ("c", 15, 15, 7), ("c", 15, 15, 2.6)],
    "interference": [("c", 11, 15, 8), ("c", 19, 15, 8), ("c", 15, 15, 3.2)],
    # ---- insert / export ------------------------------------------------
    "import_ref_image": [("r", 4, 10, 18, 12), ("r", 8, 14, 10, 8),
                         ("l", (4, 10), (22, 22)),
                         ("c", 12, 13, 1.8),
                         ("p", [(25, 2), (25, 9)]),
                         ("p", [(22, 5), (25, 9), (28, 5)])],
    "import_step": [("p", [(3, 10), (10, 3), (10, 10)]),
                    ("p", [(3, 10), (3, 25), (25, 25), (25, 10)]),
                    ("p", [(21, 3), (21, 10), (10, 10)])],
    "export_step": [("p", [(4, 14), (12, 4), (12, 24), (4, 14)]),
                    ("l", (12, 14), (26, 14)),
                    ("p", [(20, 10), (25, 14), (20, 18)])],
    "export_stl": [("g", [(4, 18), (15, 24), (15, 9)]),
                   ("g", [(15, 24), (26, 17), (15, 9)]),
                   ("l", (15, 24), (15, 9))],
    "export_obj": [("c", 14, 13, 7),
                   ("p", [(2, 4), (2, 18), (10, 24), (22, 24), (28, 12), (28, 4)])],
    "export_dxf": [("p", [(3, 4), (17, 4), (17, 24), (3, 24)]),
                   ("p", [(4, 21), (9, 8), (13, 16), (16, 6)]),
                   ("c", 22, 15, 3.2)],
    # ---- extras -----------------------------------------------------------
    "search": [("c", 12, 12, 8), ("l", (18, 18), (26, 26))],
    "context": [("c", 9, 8, 2.7), ("c", 21, 8, 2.7), ("c", 15, 22, 2.7)],
    "settings": [("c", 15, 15, 5),
                 ("p", [(12, 2), (18, 2), (19, 5), (22, 6), (26, 4), (28, 8),
                        (25, 11), (26, 15), (25, 19), (28, 22), (26, 26), (22, 24),
                        (19, 25), (18, 28), (12, 28), (11, 25), (8, 24), (4, 26),
                        (2, 22), (5, 19), (4, 15), (5, 11), (2, 8), (4, 4), (8, 6),
                        (11, 5)])],
    "calibrate": [("l", (5, 19), (19, 5)),
                  ("p", [(19, 13), (22, 13), (22, 22)]),
                  ("p", [(13, 22), (13, 19)]),
                  ("c", 19, 5, 2.1), ("c", 5, 19, 2.1)],
    "selftest": [("p", [(8, 22), (8, 10), (15, 10), (15, 14), (24, 14), (24, 4),
                        (15, 4)]),
                 ("c", 12, 18, 2.6)],
    "product-design": [("p", [(6, 3), (24, 3), (24, 21), (15, 27), (6, 21)]),
                       ("l", (6, 3), (6, 21)),
                       ("p", [(4, 7), (15, 1), (26, 7)])],
    "pocket": [("p", [(6, 25), (6, 10), (14, 4), (22, 10), (22, 25)]),
               ("c", 14, 14, 4)],
    "edit_sketch": [("p", [(8, 22), (4, 25), (5, 20)]),
                    ("p", [(15, 6), (23, 14)]),
                    ("p", [(16, 4), (24, 12), (14, 22), (4, 22), (4, 12)]),
                    ("l", (16, 4), (24, 12))],
}

EXTRA_NAMES = [
    "search", "context", "settings", "calibrate", "selftest",
    "product-design", "pocket", "edit_sketch",
]


def _emit(path, name, theme):
    stroke = STROKES[theme]
    parts = []
    for shape in SHAPES[name]:
        kind = shape[0]
        if kind == "l":
            _, (x1, y1), (x2, y2) = shape
            parts.append('<line x1="%g" y1="%g" x2="%g" y2="%g"/>'
                         % (x1, y1, x2, y2))
        elif kind == "c":
            _, cx, cy, r = shape
            parts.append('<circle cx="%g" cy="%g" r="%g"/>' % (cx, cy, r))
        elif kind == "r":
            _, x, y, w, h = shape
            parts.append('<rect x="%g" y="%g" width="%g" height="%g"/>'
                         % (x, y, w, h))
        elif kind in ("p", "g"):
            _, pts = shape
            d = " ".join("%g,%g" % pt for pt in pts)
            parts.append('<%s points="%s"/>' % ("polyline" if kind == "p"
                                                else "polygon", d))
        elif kind == "a":
            _, cx, cy, rx, ry, a1, a2 = shape
            def pt(a):
                r = math.radians(a)
                return cx + rx * math.cos(r), cy - ry * math.sin(r)
            x1, y1 = pt(a1)
            x2, y2 = pt(a2)
            large = 1 if (a2 - a1) > 180 else 0
            sweep = 1 if (a2 - a1) > 0 else 0
            parts.append('<path d="M %g,%g A %g %g 0 %d %d %g,%g" />'
                         % (x1, y1, rx, ry, large, sweep, x2, y2))
        else:
            raise ValueError("unknown kind %r" % kind)
    body = "\n".join(parts)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" '
           'viewBox="0 0 30 30">\n'
           '<g stroke="%s" stroke-width="2" stroke-linecap="round" '
           'stroke-linejoin="round" fill="none">\n%s\n</g>\n</svg>\n'
           % (stroke, body))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)


def collect_names():
    with open(RIBBON, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    names = []
    for g in data["groups"]:
        for b in g["buttons"]:
            names.append(b["icon"])
    names += EXTRA_NAMES
    return sorted(set(names))


def main(out_root=None):
    out_root = out_root or ICON_ROOT
    names = collect_names()
    missing = [n for n in names if n not in SHAPES]
    for theme in ("light", "dark"):
        d = os.path.join(out_root, theme)
        os.makedirs(d, exist_ok=True)
        for name in names:
            _emit(os.path.join(d, name + ".svg"), name, theme)
    print("generated %d icons x2 themes in %s" % (len(names), out_root))
    if missing:
        print("MISSING GLYPHS:", missing)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
