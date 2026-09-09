# -*- coding: utf-8 -*-
"""Example 3: electronics enclosure with screw bosses and a USB opening.

Open-top tray (shelled), four screw bosses fused to the floor, USB-C opening
cut through the front wall, small locating rib.  All dims are constants.
"""

from . import model_lib as ml

W = 96.0
D = 60.0
H = 24.0
WALL = 2.0
BOSS_R = 3.0
BOSS_H = 12.0
USB_W = 12.0
USB_H = 5.0


def _corners():
    inset = 7.0
    xs = (W / 2.0 - inset, -W / 2.0 + inset)
    ys = (D / 2.0 - inset, -D / 2.0 + inset)
    return [(x, y) for x in xs for y in ys]


def build(doc=None):
    import FreeCAD as App
    import Part

    doc = doc or ml.new_doc("enclosure")
    body = ml.new_body(doc, "EnclosureBody")
    sk = ml.add_rect_sketch(body, "SketchOutline", W, D)
    pad = ml.pad_sketch(body, sk, H, "PadWall")
    doc.recompute()
    box = pad.Shape
    # open-top tray: remove the top face, shell inward
    tray = ml.finish_shell(box,
                           lambda f: f.CenterOfMass.z > H - 0.5 and
                           f.normalAt(0.5, 0.5).z > 0.9,
                           WALL)
    # four screw bosses standing on the floor
    bosses = []
    for (x, y) in _corners():
        cyl = Part.makeCylinder(BOSS_R, BOSS_H, App.Vector(x, y, 0),
                                App.Vector(0, 0, 1))
        bosses.append(cyl)
    with_bosses = tray
    for b in bosses:
        with_bosses = with_bosses.fuse(b)
    # USB-C opening: pierce the front wall from just inside to outside
    usb = Part.makeBox(USB_W, WALL * 3.0, USB_H,
                       App.Vector(-USB_W / 2.0, D / 2.0 - WALL,
                                  H * 0.4))
    with_usb = with_bosses.cut(usb)
    ml.make_part_feature(doc, "Enclosure_Finished", with_usb)
    doc.recompute()
    return {"doc": doc, "body": body, "finished_solid": with_usb}


if __name__ == "__main__":
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    result = build()
    out = sys.argv[1] if len(sys.argv) > 1 else "enclosure.FCStd"
    result["doc"].saveAs(out)
    print("saved", out)
