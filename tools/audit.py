# -*- coding: utf-8 -*-
"""Audit the A2 CAD drawing for unreasonable / sloppy dimensions:
1. label vs true geometry of every DIMENSION
2. dimension defpoints not exactly on wall faces
3. near-miss wall coordinates (lines that differ by tiny offsets)
4. non-orthogonal wall segments
5. chain arithmetic: interior dims + wall thicknesses vs exterior spans
"""
import sys, io, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from collections import defaultdict

SCRATCH = r"C:\Users\v4578469\AppData\Local\Temp\claude\D--Desktop-MyHome\ce0b468f-513f-4a8c-a813-fe5774e254f8\scratchpad"
plan = json.load(open(SCRATCH + r"\plan_data.json", encoding="utf-8"))
WALLS = plan["walls"]

print("=" * 60)
print("① 標註顯示值 vs 實際幾何")
print("=" * 60)
for d in plan["dims"]:
    diff = d["meas"] - float(d["v"])
    flag = "  ⚠" if abs(diff) > 0.005 else ""
    print(f'  標註 {d["v"]:>6} | 實際 {d["meas"]:.4f} | 差 {diff:+.4f}{flag}')

print()
print("=" * 60)
print("② 標註端點是否精準落在牆線上（距最近牆線距離）")
print("=" * 60)
def dist_pt_seg(p, s):
    ax, ay, bx, by = s
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0, min(1, ((p[0] - ax) * vx + (p[1] - ay) * vy) / L2))
    return math.hypot(p[0] - ax - t * vx, p[1] - ay - t * vy)

for d in plan["dims"]:
    for name in ("o2", "o3"):
        o = d[name]
        dm = min(dist_pt_seg(o, s) for s in WALLS)
        if dm > 0.005:
            print(f'  ⚠ 標註 {d["v"]:>6} 的端點 {name}=({o[0]:.3f},{o[1]:.3f}) 距最近牆線 {dm:.3f} cm')
print("  （其餘端點皆 < 0.005 cm）")

print()
print("=" * 60)
print("③ 疑似「畫歪」的牆座標（相近但不相等，差距 0.005~2cm）")
print("=" * 60)
xs = sorted({round(v, 3) for s in WALLS for v in (s[0], s[2])})
ys = sorted({round(v, 3) for s in WALLS for v in (s[1], s[3])})
def near_miss(vals, axis):
    found = False
    for i in range(len(vals) - 1):
        gap = vals[i + 1] - vals[i]
        if 0.005 < gap < 2.0:
            print(f"  ⚠ {axis}={vals[i]} 與 {axis}={vals[i+1]}（差 {gap:.3f} cm）")
            found = True
    if not found:
        print(f"  {axis} 方向無近似重合座標")
near_miss(xs, "x")
near_miss(ys, "y")

print()
print("=" * 60)
print("④ 非正交（歪斜）的牆段")
print("=" * 60)
skew = 0
for s in WALLS:
    dx, dy = abs(s[2] - s[0]), abs(s[3] - s[1])
    if dx > 0.01 and dy > 0.01:
        ang = math.degrees(math.atan2(min(dx, dy), max(dx, dy)))
        print(f"  ⚠ 牆段 ({s[0]:.1f},{s[1]:.1f})-({s[2]:.1f},{s[3]:.1f}) 偏斜 {ang:.3f}°")
        skew += 1
if not skew:
    print("  全部牆段皆水平或垂直，無歪斜")

print()
print("=" * 60)
print("⑤ 內徑＋牆厚 vs 外徑 加總驗算（沿主要斷面）")
print("=" * 60)
# vertical section along left zone x~132 (客餐廳帶): exterior left overall 1225
# use wall y-coordinates crossing at x=300 (through 臥室x2 + 客餐廳)
def wall_lines_at(x=None, y=None):
    """collect crossing coordinates of walls at a probe line"""
    cs = []
    for s in WALLS:
        if x is not None and abs(s[1] - s[3]) < 0.01:  # horizontal seg
            if min(s[0], s[2]) - 1e-9 <= x <= max(s[0], s[2]) + 1e-9:
                cs.append(s[1])
        if y is not None and abs(s[0] - s[2]) < 0.01:  # vertical seg
            if min(s[1], s[3]) - 1e-9 <= y <= max(s[1], s[3]) + 1e-9:
                cs.append(s[0])
    return sorted(set(round(c, 3) for c in cs))

sec = wall_lines_at(x=300)
print(f"  垂直斷面 x=300 的牆面 y 座標：{sec}")
runs = [round(sec[i + 1] - sec[i], 3) for i in range(len(sec) - 1)]
print(f"  區段（淨空/牆厚交錯）：{runs}")
print(f"  總和 {sum(runs):.1f}（應= 外徑鏈同斷面總長）")
sec2 = wall_lines_at(y=700)
print(f"  水平斷面 y=700 的牆面 x 座標：{sec2}")
runs2 = [round(sec2[i + 1] - sec2[i], 3) for i in range(len(sec2) - 1)]
print(f"  區段：{runs2}")
print(f"  總和 {sum(runs2):.1f}")

print()
print("=" * 60)
print("⑥ 標註值本身的模數檢查（建築慣用 2.5/5cm 模數）")
print("=" * 60)
for d in plan["dims"] + plan["extDims"]:
    m = d["meas"]
    r = m % 2.5
    if min(r, 2.5 - r) > 0.01:
        print(f'  ⚠ {("外徑" if d in plan["extDims"] else "內徑")} {d["v"]}：實際 {m:.4f} 非 2.5cm 模數')
print("  （未列出者皆符合 2.5cm 模數）")
