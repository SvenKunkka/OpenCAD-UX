#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build all three example models and export STEP/STL next to the .FCStd.

Run inside FreeCAD (console or GUI):
    freecadcmd -P <repo root> -c "exec(open('examples/build_all.py').read())"
or
    bash scripts/run_examples.sh
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from opencad_ux.commands import exporters  # noqa: E402

MODELS = [
    ("examples.keyboard_shell", "keyboard_shell"),
    ("examples.mouse_shell", "mouse_shell"),
    ("examples.enclosure", "enclosure"),
]


def main(out_dir=None):
    out_dir = out_dir or os.path.join(ROOT, "examples", "output")
    os.makedirs(out_dir, exist_ok=True)
    report = {}
    for mod_name, short in MODELS:
        mod = __import__(mod_name, fromlist=["build"])
        try:
            result = mod.build()
            doc = result["doc"]
            fc = os.path.join(out_dir, short + ".FCStd")
            doc.saveAs(fc)
            solid = result["finished_solid"]
            bb = solid.BoundBox
            step = os.path.join(out_dir, short + ".step")
            stl = os.path.join(out_dir, short + ".stl")
            exporters.export_step(doc, step, selected=[result["feature"]] if "feature" in result else None)
            exporters.export_stl(doc, stl)
            report[short] = {
                "ok": True,
                "fcstd": fc,
                "step": step,
                "stl": stl,
                "volume_mm3": round(solid.Volume, 1),
                "bbox_mm": [round(bb.XLength, 1), round(bb.YLength, 1),
                            round(bb.ZLength, 1)],
            }
            print("%s: OK  volume=%.0f mm^3  size=%s"
                  % (short, solid.Volume,
                     [round(bb.XLength, 1), round(bb.YLength, 1),
                      round(bb.ZLength, 1)]))
        except Exception as exc:  # report and continue with the next model
            report[short] = {"ok": False, "error": repr(exc)}
            print("%s: FAILED %s" % (short, repr(exc)[:200]))
    with open(os.path.join(out_dir, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    ok = sum(1 for v in report.values() if v.get("ok"))
    print("examples: %d/%d ok -> %s" % (ok, len(MODELS), out_dir))
    return 0 if ok == len(MODELS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
