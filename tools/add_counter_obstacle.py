# -*- coding: utf-8 -*-
"""流理台外框 → 障礙物（WALLS）。

外框座標不手打，一律從 plan_data.json 的 CAD 抓點推導（保持與 DWG 一致）；
洗手槽（內框）維持純圖面、不進 WALLS。冪等：重跑不會重複加入。
注意：重跑 extract.py 產生新 plan_data.json 後，需再跑一次本腳本。
"""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PATH = r"D:\Desktop\MyHome\tools\plan_data.json"
plan = json.load(open(PATH, encoding="utf-8"))
snaps = plan["snaps"]

def exact(vals, approx, tol=0.05):
    c = [v for v in vals if abs(v - approx) <= tol]
    assert c, f"找不到座標 {approx}"
    assert max(c) - min(c) < 0.001, f"{approx} 附近座標不唯一: {c}"
    return c[0]

kx = [p[0] for p in snaps if 1000 <= p[1] <= 1195]
ky = [p[1] for p in snaps if 345 <= p[0] <= 420]
xL = exact(kx, 354.53)   # 流理台外框左（審查：354.527，非模數）
xR = exact(kx, 414.53)
yT = exact(ky, 1010.0)
yB = exact(ky, 1170.0)
print(f"流理台外框: x {xL:.4f}~{xR:.4f}, y {yT:.4f}~{yB:.4f}（寬 {xR-xL:.3f}×長 {yB-yT:.3f}）")

segs = [
    [xL, yT, xL, yB],
    [xR, yT, xR, yB],
    [xL, yT, xR, yT],
    [xL, yB, xR, yB],
]
def has(seg):
    return any(all(abs(a - b) < 0.01 for a, b in zip(w, seg)) for w in plan["walls"])

added = 0
for s in segs:
    if not has(s):
        plan["walls"].append([round(v, 4) for v in s])
        added += 1
print(f"walls: +{added}（共 {len(plan['walls'])}）")

# 斷言：洗手槽內框（x≈364.5/399.5）不得進 WALLS
for w in plan["walls"]:
    for v in (w[0], w[2]):
        assert not (abs(v - 364.53) < 0.2 or abs(v - 399.53) < 0.2), "洗手槽線誤入 WALLS"

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(plan, f, ensure_ascii=False)
print("plan_data.json 已更新")
