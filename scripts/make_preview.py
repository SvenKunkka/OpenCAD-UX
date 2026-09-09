#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate HTML preview pages of the OpenCAD UX ribbon + themes using the
*real* ribbon.json, theme palettes and SVG icons, then screenshot them with
headless Chrome (no FreeCAD GUI needed).

Usage:
  python3 scripts/make_preview.py [out_dir]     # writes .html and .png
"""
import html
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "screenshots")


def load_json(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return json.load(fh)


def svg_icon(name, theme):
    p = os.path.join(ROOT, "resources", "icons", theme, name + ".svg")
    if not os.path.isfile(p):
        return ""
    with open(p, encoding="utf-8") as fh:
        data = fh.read()
    # size svgs for inline use
    return data.replace('width="30" height="30" viewBox="0 0 30 30"',
                        'width="28" height="28" viewBox="0 0 30 30"')
    # keep style


def build_page(theme):
    ribbon = load_json("resources/ribbon.json")
    tdata = load_json("resources/themes/%s.json" % theme)
    pal = tdata["palette"]
    groups_html = []
    for g in ribbon["groups"]:
        buttons = []
        for b in g["buttons"]:
            icon = svg_icon(b["icon"], theme)
            tip = ""
            if b.get("hint_shortcut"):
                tip = '<span class="sc">%s</span>' % b["hint_shortcut"]
            buttons.append(
                '<div class="btn">%s<div class="lbl">%s%s</div></div>'
                % (icon, html.escape(b["label"]["en"]), tip))
        groups_html.append(
            '<div class="grp"><div class="gh">%s &nbsp;|&nbsp; %s</div>%s</div>'
            % (html.escape(g["label"]["en"]), html.escape(g["label"]["zh"]),
               "".join(buttons)))
    page = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
body{margin:0;background:%(ribbon_bg)s;font-family:-apple-system,'Segoe UI',
    Roboto,sans-serif;color:%(text)s;}
.top{height:64px;background:%(ribbon_bg)s;border-bottom:1px solid %(border)s;
    display:flex;align-items:center;padding:0 12px;gap:10px;}
.top .brand{font-size:15px;font-weight:600;}
.top input{margin-left:auto;width:220px;background:%(base)s;color:%(text)s;
    border:1px solid %(border)s;border-radius:6px;padding:5px 8px;}
.scroll{overflow-x:auto;padding:8px;white-space:nowrap;}
.grp{display:inline-block;vertical-align:top;background:%(grp_bg)s;
    border:1px solid %(border)s;border-radius:8px;padding:6px;margin-right:8px;}
.gh{font-size:11px;text-align:center;opacity:.8;padding-bottom:2px;
    border-bottom:1px dashed %(border)s;margin-bottom:4px;white-space:normal;}
.btn{display:inline-flex;flex-direction:column;align-items:center;margin:2px;
    padding:6px 4px;border-radius:6px;width:64px;white-space:normal;}
.btn:hover{background:%(hover)s;}
.btn .lbl{font-size:10px;text-align:center;line-height:1.1;}
.btn .sc{margin-left:2px;color:%(accent)s;font-weight:bold;}
.cap{margin:10px 16px;font-size:11px;opacity:.7;}
</style></head><body>
<div class="top">
  <img src="file://%(root)s/resources/icons/%(theme)s/product-design.svg"
       width="26" height="26" alt="OpenCAD UX"/>
  <span class="brand">OpenCAD UX - Product Design&nbsp;&nbsp;·&nbsp;&nbsp;%(title)s</span>
  <input type="text" placeholder="Search commands…  /  输入命令搜索"/>
</div>
<div class="scroll">%(groups)s</div>
<div class="cap">UI preview rendered from resources/ribbon.json + resources/themes/%(theme)s.json
  + resources/icons/%(theme)s (headless Chrome). Actual FreeCAD window may differ slightly.</div>
</body></html>""" % {
        "ribbon_bg": pal["ribbon_background"], "grp_bg": pal["ribbon_group_bg"],
        "border": pal["ribbon_border"], "text": pal["windowText"],
        "base": pal["base"], "hover": pal["ribbon_hover"],
        "accent": pal["accent"], "groups": "".join(groups_html),
        "title": tdata["label"]["en"], "theme": theme,
        "root": ROOT.replace(" ", "%20"),
    }
    return page


def main():
    os.makedirs(OUT, exist_ok=True)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    results = []
    for theme in ("light", "dark"):
        page = build_page(theme)
        html_path = os.path.join(OUT, "preview-%s.html" % theme)
        png_path = os.path.join(OUT, "preview-%s.png" % theme)
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(page)
        cmd = [chrome, "--headless=new", "--disable-gpu",
               "--window-size=1680,320",
               "--screenshot=%s" % png_path,
               "file://%s" % html_path]
        try:
            subprocess.run(cmd, check=True, capture_output=True,
                           timeout=60)
            results.append(png_path)
        except Exception as exc:
            print("chrome screenshot failed for %s: %s" % (theme, exc))
    print("previews written:", results or "none")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
