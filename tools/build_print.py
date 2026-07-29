# -*- coding: utf-8 -*-
"""Build printable grid-paper floor plan: 10cm grid, interior + exterior dims, no text."""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = r"C:\Users\v4578469\AppData\Local\Temp\claude\D--Desktop-MyHome\ce0b468f-513f-4a8c-a813-fe5774e254f8\scratchpad"

with open(SCRATCH + r"\base_cm.svg", encoding="utf-8") as f:
    base = f.read()
with open(SCRATCH + r"\plan_data.json", encoding="utf-8") as f:
    plan = json.load(f)

W, H = plan["W"], plan["H"]
wx0, wy0, wx1, wy1 = plan["wallBox"]
CLASS_RE = r"\.(C[0-9A-Fa-f]+) \{([^}]*)\}"

def restyle(m):
    name, body = m.group(1), m.group(2)
    if "stroke: none" not in body:
        body = re.sub(r"stroke: #[0-9a-f]{6}", "stroke: #000000", body)
        body = re.sub(r"stroke-width: [\d.]+;", "stroke-width: 1.4;", body)
    if "fill: #7f9fff" in body:
        body = body.replace("fill: #7f9fff", "fill: #c8c8c8")
    else:
        body = re.sub(r"fill: #[0-9a-f]{6}", "fill: #000000", body)
    return f".{name} {{{body}}}"

psvg = re.sub(CLASS_RE, restyle, base)
psvg = re.sub(r'<rect id="bg" fill="#000000"', '<rect id="bg" fill="#ffffff"', psvg, count=1)

# ---- bounds including exterior chains ----
allpts = []
for d in plan["dims"] + plan["extDims"]:
    allpts += [d["q2"], d["q3"], d["t"], d["o2"], d["o3"]]
minx = min(0, min(p[0] for p in allpts)) - 28
miny = min(0, min(p[1] for p in allpts)) - 28
maxx = max(W, max(p[0] for p in allpts)) + 28
maxy = max(H, max(p[1] for p in allpts)) + 28
sb_y = maxy + 14
TOT_W = maxx - minx
TOT_H = sb_y + 46 - miny
print(f"print area: {TOT_W:.0f} x {TOT_H:.0f} cm")

# ---- 10cm grid over plan area (5=50cm mid, 10=100cm major) ----
# origin anchored at the entry-side bottom-left wall corner so hand sketches
# start counting from the front door (user request)
GOX, GOY = None, None
for d in plan["extDims"]:
    if d.get("overall") and d["rot"] == 0 and d["q2"][1] > H / 2:   # bottom overall chain
        GOX, GOY = d["o2"][0], wy1
        break
assert GOX is not None
print(f"grid origin: ({GOX}, {GOY})")

grid = ['<g id="grid" style="mix-blend-mode: multiply">']
def gline(x1, y1, x2, y2, k):
    if k % 10 == 0:
        col, w = "#9d9d9d", 1.0
    elif k % 5 == 0:
        col, w = "#c4c4c4", 0.7
    else:
        col, w = "#e2e2e2", 0.45
    grid.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{col}" stroke-width="{w}"/>')
import math as _m
for k in range(_m.ceil((0 - GOX) / 10), _m.floor((W - GOX) / 10) + 1):
    gline(GOX + 10 * k, 0, GOX + 10 * k, H, abs(k))
for k in range(_m.ceil((0 - GOY) / 10), _m.floor((H - GOY) / 10) + 1):
    gline(0, GOY + 10 * k, W, GOY + 10 * k, abs(k))
grid.append(f'<rect x="0" y="0" width="{W:g}" height="{H:g}" fill="none" stroke="#8a8a8a" stroke-width="1.4"/>')
grid.append("</g>")
# origin marker: crosshair + label at the entry corner
grid.append(f'<g font-family="Microsoft JhengHei, sans-serif">'
            f'<circle cx="{GOX}" cy="{GOY}" r="6" fill="none" stroke="#000" stroke-width="1.6"/>'
            f'<line x1="{GOX-11}" y1="{GOY}" x2="{GOX+11}" y2="{GOY}" stroke="#000" stroke-width="1.2"/>'
            f'<line x1="{GOX}" y1="{GOY-11}" x2="{GOX}" y2="{GOY+11}" stroke="#000" stroke-width="1.2"/>'
            f'<text x="{GOX-14}" y="{GOY+26}" font-size="15" font-weight="bold" fill="#000" text-anchor="end">0（玄關起算）</text></g>')
grid_svg = "".join(grid)

# ---- dims (interior solid dark, exterior darker outside) ----
def dim_markup(dims, color, fs_base):
    out = [f'<g font-family="Microsoft JhengHei, sans-serif">']
    for d in dims:
        o2, o3, q2, q3, t = d["o2"], d["o3"], d["q2"], d["q3"], d["t"]
        for o, q in ((o2, q2), (o3, q3)):
            vx, vy = q[0] - o[0], q[1] - o[1]
            L = (vx * vx + vy * vy) ** 0.5 or 1
            vx, vy = vx / L, vy / L
            out.append(f'<line x1="{o[0]+vx*2:.2f}" y1="{o[1]+vy*2:.2f}" x2="{q[0]+vx*5:.2f}" y2="{q[1]+vy*5:.2f}" stroke="{color}" stroke-width="0.8" opacity="0.8"/>')
        out.append(f'<line x1="{q2[0]:.2f}" y1="{q2[1]:.2f}" x2="{q3[0]:.2f}" y2="{q3[1]:.2f}" stroke="{color}" stroke-width="1.1"/>')
        for q in (q2, q3):
            out.append(f'<line x1="{q[0]-3:.2f}" y1="{q[1]+3:.2f}" x2="{q[0]+3:.2f}" y2="{q[1]-3:.2f}" stroke="{color}" stroke-width="1.3"/>')
        fs = fs_base * (1.3 if d.get("overall") else 1.0)
        rot = d["rot"] % 360
        tr = f' transform="rotate({-(360-rot) if rot > 180 else -rot} {t[0]:.2f} {t[1]:.2f})"' if rot else ""
        w = "bold" if d.get("overall") else "normal"
        out.append(f'<text x="{t[0]:.2f}" y="{t[1]:.2f}" font-size="{fs}" font-weight="{w}" fill="{color}" text-anchor="middle" dominant-baseline="middle"{tr}>{d["v"]}</text>')
    out.append("</g>")
    return "".join(out)

dims_svg = dim_markup(plan["dims"], "#333333", 19) + dim_markup(plan["extDims"], "#000000", 21)

# ---- scale bar ----
sb_x = 10
sbar = [f'<g font-family="Microsoft JhengHei, sans-serif" font-size="16" fill="#000000">']
for k in range(4):
    fill = "#000000" if k % 2 == 0 else "#ffffff"
    sbar.append(f'<rect x="{sb_x+k*50}" y="{sb_y}" width="50" height="8" fill="{fill}" stroke="#000" stroke-width="0.8"/>')
sbar.append(f'<text x="{sb_x}" y="{sb_y-6}" text-anchor="start">0</text>')
sbar.append(f'<text x="{sb_x+100}" y="{sb_y-6}" text-anchor="middle">1m</text>')
sbar.append(f'<text x="{sb_x+200}" y="{sb_y-6}" text-anchor="middle">2m</text>')
sbar.append("</g>")
sbar_svg = "".join(sbar)

# ---- assemble: expand viewBox; grid ABOVE the drawing (below dims) so room
# fills can never mask it; light-gray lines stay subtle over the gray walls ----
psvg = psvg.replace(f'viewBox="0 0 {W:.3f} {H:.3f}"',
                    f'viewBox="{minx:.2f} {miny:.2f} {TOT_W:.2f} {TOT_H:.2f}"', 1)
psvg = psvg.replace("</g></svg>", "</g>" + grid_svg + dims_svg + sbar_svg + "</svg>", 1)
psvg = psvg.replace("<svg ", '<svg id="printsvg" ', 1)

html = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>A2戶型 列印圖（10cm格線）</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #666; font-family: "Microsoft JhengHei", sans-serif; }
  #toolbar { position: fixed; top: 0; left: 0; right: 0; background: #1c1c22; color: #eee; padding: 8px 14px;
             display: flex; gap: 10px; align-items: center; z-index: 10; flex-wrap: wrap; }
  #toolbar button { background: #33333d; color: #ddd; border: 1px solid #55555f; border-radius: 6px;
                    padding: 6px 14px; cursor: pointer; font-family: inherit; font-size: 13px; }
  #toolbar button.active { background: #2563eb; border-color: #2563eb; color: #fff; }
  #toolbar .note { font-size: 12px; color: #aab; }
  #paper { background: #fff; margin: 76px auto 20px; box-shadow: 0 4px 20px rgba(0,0,0,.5); padding: 5mm; }
  #head { display: flex; justify-content: space-between; align-items: baseline; border-bottom: 1.5px solid #000;
          padding-bottom: 2mm; margin-bottom: 2mm; gap: 4mm; }
  #head .t1 { font-size: 13px; font-weight: 700; white-space: nowrap; }
  #head .t2 { font-size: 9.5px; text-align: right; }
  svg { display: block; margin: 0 auto; }
  @media print {
    body { background: #fff; }
    #toolbar { display: none; }
    #paper { margin: 0; box-shadow: none; padding: 0; }
  }
</style>
<style id="pagestyle">@page { size: A3 portrait; margin: 8mm; }</style>
</head>
<body>
<div id="toolbar">
  <span>列印設定：</span>
  <button id="bA3" class="active">A3 直式・1:50</button>
  <button id="bA4">A4 直式・1:75</button>
  <button id="bPrint">🖨 列印</button>
  <span class="note">格線＝10cm（中線 50cm、粗線 1m）。列印請選「實際大小／100%」，勿選「符合頁面」。</span>
</div>
<div id="paper">
  <div id="head">
    <span class="t1">日安TOKYO・A2戶型平面圖（10~24F）</span>
    <span class="t2">比例 <b id="scaleTxt">1:50</b>｜格線一格＝10cm（中線 50cm・粗線 1m）｜圖內尺寸＝室內淨尺寸（內徑）・圖外尺寸＝外緣尺寸（外徑）｜單位 cm｜依 A2戶型.dwg 製</span>
  </div>
  __SVG__
</div>
<script>
'use strict';
var TW = __TW__, TH = __TH__;
var svg = document.getElementById('printsvg');
function setScale(denom, page) {
  svg.setAttribute('width', (TW * 10 / denom).toFixed(2) + 'mm');
  svg.setAttribute('height', (TH * 10 / denom).toFixed(2) + 'mm');
  document.getElementById('pagestyle').textContent = '@page { size: ' + page + ' portrait; margin: 8mm; }';
  document.getElementById('scaleTxt').textContent = '1:' + denom;
  document.getElementById('paper').style.width = (page === 'A3' ? 297 : 210) + 'mm';
  document.getElementById('bA3').classList.toggle('active', page === 'A3');
  document.getElementById('bA4').classList.toggle('active', page === 'A4');
}
document.getElementById('bA3').addEventListener('click', function () { setScale(50, 'A3'); });
document.getElementById('bA4').addEventListener('click', function () { setScale(75, 'A4'); });
document.getElementById('bPrint').addEventListener('click', function () { window.print(); });
setScale(50, 'A3');
var q = new URLSearchParams(location.search);
if (q.get('p') === 'a4') setScale(75, 'A4');
</script>
</body>
</html>
"""
html = html.replace("__SVG__", psvg).replace("__TW__", f"{TOT_W:.2f}").replace("__TH__", f"{TOT_H:.2f}")

OUT = SCRATCH + r"\A2戶型-列印圖.html"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"written {OUT} ({len(html)} chars)")

# fit check
for denom, page_w, page_h, name in ((50, 281, 404, "A3"), (75, 194, 281, "A4")):
    w_mm = TOT_W * 10 / denom
    h_mm = TOT_H * 10 / denom
    ok = w_mm <= page_w and h_mm + 14 <= page_h
    print(f"{name} 1:{denom}: {w_mm:.0f}x{h_mm:.0f}mm printable {page_w}x{page_h} -> {'OK' if ok else 'OVERFLOW'}")
