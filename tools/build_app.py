# -*- coding: utf-8 -*-
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TOOLS = r"D:\Desktop\MyHome\tools"

with open(TOOLS + r"\base_cm.svg", encoding="utf-8") as f:
    base = f.read()
with open(TOOLS + r"\plan_data.json", encoding="utf-8") as f:
    data = f.read()
with open(TOOLS + r"\app_template.html", encoding="utf-8") as f:
    tpl = f.read()

# light-theme overrides for base svg classes (readability-tuned dark variants)
MAP = {
    "#ffffff": "#1a1a1a",
    "#ffff00": "#8a7500",
    "#00ffff": "#00788a",
    "#00ff00": "#1e7d1e",
    "#ff00ff": "#a800a8",
    "#ffbf00": "#a87800",
    "#c0c0c0": "#6b6b6b",
    "#ff0000": "#c00000",
}
CLASS_RE = r"\.(C[0-9A-Fa-f]+) \{([^}]*)\}"
classes = re.findall(CLASS_RE, base)
print(f"classes found: {len(classes)}")

# 1) rewrite stroke widths to screen-px (AutoCAD-style constant width) + non-scaling stroke
def px_width(units):
    return max(1.1, min(3.2, units / 55.0))

def rewrite_class(m):
    name, body = m.group(1), m.group(2)
    wm = re.search(r"stroke-width: ([\d.]+);", body)
    if wm and "stroke: none" not in body:
        body = body.replace(f"stroke-width: {wm.group(1)};",
                            f"stroke-width: {px_width(float(wm.group(1))):.2f}; vector-effect: non-scaling-stroke;")
    return f".{name} {{{body}}}"

base = re.sub(CLASS_RE, rewrite_class, base)

# 2) light theme color swaps (on the rewritten bodies)
rules = []
for name, body in re.findall(CLASS_RE, base):
    nb, changed = body, False
    for src, dst in MAP.items():
        if f"stroke: {src}" in nb:
            nb = nb.replace(f"stroke: {src}", f"stroke: {dst}"); changed = True
        if f"fill: {src}" in nb:
            nb = nb.replace(f"fill: {src}", f"fill: {dst}"); changed = True
    if changed:
        rules.append(f".light .{name} {{{nb}}}")
light_css = "\n  ".join(rules)
print(f"light overrides: {len(rules)}")

out = tpl.replace("__LIGHT_CSS__", light_css)
out = out.replace("__BASE_SVG__", base)
out = out.replace("__PLAN_DATA__", data)

OUT = r"D:\Desktop\MyHome\A2戶型居家模擬.html"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(out)
print(f"written {OUT} ({len(out)} chars)")
# GitHub Pages 入口（同內容，同源 localStorage 共用）
OUT2 = r"D:\Desktop\MyHome\index.html"
with open(OUT2, "w", encoding="utf-8") as f:
    f.write(out)
print(f"written {OUT2}")
