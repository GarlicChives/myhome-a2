# -*- coding: utf-8 -*-
"""A2戶型.dxf → mep_data.json（水電配置圖層，唯讀顯示用）

從建商 CAD 抽取「本戶視窗內」可證實的水電/給排水圖元（座標＝平面 cm，與主系統同座標系）：
  - toilet：馬桶排水定位（TOIL 層 PCOM006 器具插入點＝糞管/器具基準）
  - drain ：排水立管（TOIL 層 CIRCLE，r＝CAD 實際半徑）
  - shaft ：管道間（SP-PROJ 層 X 交叉框，取外框）
註：此份建商 DWG 內【沒有】插座/開關/弱電/網路孔/配電箱圖元（已全層掃描含凍結層與區塊）。
    未來取得水電圖 CAD 後在此擴充 kind：outlet/switch/net/panel/water…，前端會自動顯示。
    schema：{k, name, x, y, z(離地cm), rot, r?, w?, d?, note?}
"""
import ezdxf, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

X0, YT = 376137.7685, -21196.2788   # 平面座標系原點（與 extract.py 相同）
XR = (-100, 820)
YR = (-110, 1330)

def plan(p):
    return (round(p[0] - X0, 2), round(YT - p[1], 2))

def inwin(x, y):
    return XR[0] <= x <= XR[1] and YR[0] <= y <= YR[1]

d = ezdxf.readfile(r"D:\Desktop\MyHome\A2戶型.dxf")
msp = d.modelspace()
items = []

sp_pts = []
for e in msp:
    lay = e.dxf.layer
    t = e.dxftype()
    if lay == "TOIL" and t == "INSERT" and e.dxf.name == "PCOM006":
        x, y = plan(e.dxf.insert)
        if inwin(x, y):
            items.append({"k": "toilet", "name": "馬桶排水(糞管)", "x": x, "y": y, "z": 0,
                          "rot": round(e.dxf.rotation, 1)})
    elif lay == "TOIL" and t == "CIRCLE":
        x, y = plan(e.dxf.center)
        if inwin(x, y):
            items.append({"k": "drain", "name": "排水立管", "x": x, "y": y, "z": 0,
                          "r": round(e.dxf.radius, 2)})
    elif lay == "SP-PROJ" and t == "LINE":
        for p in (e.dxf.start, e.dxf.end):
            x, y = plan(p)
            if inwin(x, y):
                sp_pts.append((x, y))

if sp_pts:
    xs = [p[0] for p in sp_pts]; ys = [p[1] for p in sp_pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    items.append({"k": "shaft", "name": "管道間(貫穿樓層)", "x": round((x0 + x1) / 2, 2),
                  "y": round((y0 + y1) / 2, 2), "z": 0,
                  "w": round(x1 - x0, 2), "d": round(y1 - y0, 2)})

items.sort(key=lambda m: (m["k"], m["y"]))
out = r"D:\Desktop\MyHome\tools\mep_data.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=1)
print(f"written {out}: {len(items)} items")
for m in items:
    print(" ", m)
