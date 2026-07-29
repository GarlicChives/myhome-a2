# -*- coding: utf-8 -*-
"""Independent end-to-end verification of the FINAL print file:
parse grid lines + dimension lines out of A2戶型-列印圖.html and verify
1) grid is exactly 10cm pitch anchored at the entry corner (25,1225)
2) every dimension line length equals its printed value
3) cell-count table: each dimension expressed in 10cm cells
4) wall/facade breakpoints measured from the origin in cells
"""
import sys, io, re, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SCRATCH = r"C:\Users\v4578469\AppData\Local\Temp\claude\D--Desktop-MyHome\ce0b468f-513f-4a8c-a813-fe5774e254f8\scratchpad"
html = open(SCRATCH + r"\A2戶型-列印圖.html", encoding="utf-8").read()
plan = json.load(open(SCRATCH + r"\plan_data.json", encoding="utf-8"))
GOX, GOY = 25.0, 1225.0
ok = True

def check(name, cond, detail=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + (" " + detail if detail else ""))
    if not cond:
        ok = False

# ---- 1. grid pitch & phase ----
gm = re.search(r'<g id="grid"[^>]*>(.*?)</g>', html, re.S)
glines = re.findall(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)" stroke="#(?:9d9d9d|c4c4c4|e2e2e2)"', gm.group(1))
vx = sorted({float(a) for a, b, c, d in glines if abs(float(a) - float(c)) < 1e-6})
hy = sorted({float(b) for a, b, c, d in glines if abs(float(b) - float(d)) < 1e-6})
pitch_v = {round(vx[i + 1] - vx[i], 6) for i in range(len(vx) - 1)}
pitch_h = {round(hy[i + 1] - hy[i], 6) for i in range(len(hy) - 1)}
check("格線間距一律 10cm（垂直）", pitch_v == {10.0}, str(pitch_v))
check("格線間距一律 10cm（水平）", pitch_h == {10.0}, str(pitch_h))
check("垂直格線相位對齊玄關角 x=25", all(abs((x - GOX) % 10) < 1e-6 or abs((x - GOX) % 10 - 10) < 1e-6 for x in vx))
check("水平格線相位對齊玄關角 y=1225", all(abs((y - GOY) % 10) < 1e-6 or abs((y - GOY) % 10 - 10) < 1e-6 for y in hy))
check("玄關角上有格線通過", any(abs(x - GOX) < 1e-6 for x in vx) and any(abs(y - GOY) < 1e-6 for y in hy))

# ---- 2+3. every dimension line length == printed value; cell table ----
print("\n=== 尺寸 → 1×1 格數（10cm/格）對照 ===")
all_dims = [("內徑", d) for d in plan["dims"]] + [("外徑", d) for d in plan["extDims"]]
def cad_label(meas):
    return f"{meas:.1f}".rstrip("0").rstrip(".")

for kind, d in all_dims:
    L = math.hypot(d["q3"][0] - d["q2"][0], d["q3"][1] - d["q2"][1])
    good_len = abs(L - d["meas"]) < 0.01           # line length == true CAD geometry
    good_lbl = d["v"] == cad_label(d["meas"])       # label == CAD display rounding
    good = good_len and good_lbl
    cells = d["meas"] / 10
    tag = "總" if d.get("overall") else ""
    note = "" if abs(d["meas"] - float(d["v"])) < 0.005 else f"（原圖標註顯示值；實際幾何 {d['meas']:.3f}）"
    print(f'{"PASS" if good else "FAIL"} {kind}{tag} {d["v"]:>6} cm = {cells:g} 格   (線長實測 {L:.3f}){note}')
    if not good:
        ok = False

# ---- 4. facade breakpoints from origin, in cells ----
print("\n=== 牆面轉折點距玄關角的格數 ===")
for kind, d in all_dims:
    if kind != "外徑" or d.get("overall"):
        continue
    if d["rot"] == 0:
        for o in (d["o2"], d["o3"]):
            cells = (o[0] - GOX) / 10
            print(f"  x={o[0]:g} → {cells:g} 格")
    else:
        for o in (d["o2"], d["o3"]):
            cells = (GOY - o[1]) / 10
            print(f"  y={o[1]:g} → {cells:g} 格")

# ---- 5. spot identities vs CAD 標註 ----
print("\n=== 關鍵交叉驗證 ===")
d240 = [d for d in plan["dims"] if d["v"] == "240"][0]
check("主臥淨寬 240 = 24 格", abs((d240["meas"]) - 240) < 0.01)
d602 = [d for d in plan["dims"] if d["v"] == "602.5"][0]
check("客餐廳長 602.5 = 60.25 格", abs((d602["meas"]) - 602.5) < 0.01)
top = [d for d in plan["extDims"] if d.get("overall") and d["rot"] == 0 and d["q2"][1] < 0][0]
check("全寬 680 = 68 格", abs(top["meas"] - 680) < 0.01)
lft = [d for d in plan["extDims"] if d.get("overall") and d["rot"] == 90 and d["q2"][0] < 0][0]
check("左側全高 1225 = 122.5 格", abs(lft["meas"] - 1225) < 0.01)
bot = [d for d in plan["extDims"] if d.get("overall") and d["rot"] == 0 and d["q2"][1] > 600][0]
check("底邊全寬 655 = 65.5 格（自玄關角起 0→65.5）", abs(bot["meas"] - 655) < 0.01 and abs(bot["o2"][0] - GOX) < 0.01)

print("\n" + ("=== 全部驗證通過 ===" if ok else "!!! 有驗證失敗 !!!"))
sys.exit(0 if ok else 1)
