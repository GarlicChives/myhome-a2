# -*- coding: utf-8 -*-
"""Extract base SVG (cm, no text), wall segments, snap points, interior dims,
exterior dimension chains, wall-thickness probes from A2 DXF."""
import sys, io, re, json, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import ezdxf
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext, layout
from ezdxf.addons.drawing.svg import SVGBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy

SCRATCH = r"C:\Users\v4578469\AppData\Local\Temp\claude\D--Desktop-MyHome\ce0b468f-513f-4a8c-a813-fe5774e254f8\scratchpad"
PATH = SCRATCH + r"\dxf\A2戶型.dxf"
X0R, X1R, Y0R, Y1R = 375350, 378850, -22800, -21100  # crop region (WCS)

CAL1 = ((376200.0, -22600.0), (376210.0, -22600.0))
CAL2 = ((376790.0, -21300.0), (376800.0, -21300.0))

WALL_LAYERS = {"WALL", "WALL2", "COL", "裝飾柱", "0-塗牆", "BEAM", "HANDRAIL", "裝飾柱-H"}

doc = ezdxf.readfile(PATH)
for style in doc.styles:
    style.dxf.font = "msjh.ttc"
    style.dxf.bigfont = ""
msp = doc.modelspace()

# ---- crop ----
to_delete = []
for e in msp:
    if e.dxf.layer == "0-字":            # title-block underline strokes (text itself removed below)
        to_delete.append(e); continue
    try:
        bb = bbox.extents([e], fast=True)
    except Exception:
        to_delete.append(e); continue
    if not bb.has_data:
        to_delete.append(e); continue
    if bb.extmax.x < X0R or bb.extmin.x > X1R or bb.extmax.y < Y0R or bb.extmin.y > Y1R:
        to_delete.append(e)
    elif bb.extmax.y < -22560:           # title-block decorations far below the unit walls
        to_delete.append(e)
for e in to_delete:
    msp.delete_entity(e)

# ---- extract dimension data, remove dims + ALL text ----
def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")

dims_raw = []
removed_text = 0
for e in list(msp):
    t = e.dxftype()
    if t == "DIMENSION":
        d = e.dxf
        dims_raw.append({
            "measure": e.get_measurement(),
            "angle": float(getattr(d, "angle", 0.0)),
            "defpoint": (d.defpoint.x, d.defpoint.y),
            "p2": (d.defpoint2.x, d.defpoint2.y),
            "p3": (d.defpoint3.x, d.defpoint3.y),
            "tmid": (d.text_midpoint.x, d.text_midpoint.y),
        })
        msp.delete_entity(e)
    elif t in ("TEXT", "MTEXT"):
        msp.delete_entity(e)
        removed_text += 1
print(f"dims extracted: {len(dims_raw)}, text removed: {removed_text}")

for dd in dims_raw:
    a = math.radians(dd["angle"])
    u = (math.cos(a), math.sin(a))
    proj = abs((dd["p3"][0] - dd["p2"][0]) * u[0] + (dd["p3"][1] - dd["p2"][1]) * u[1])
    assert abs(proj - dd["measure"]) < 0.01

# ---- calibration markers ----
for c in (CAL1, CAL2):
    ln = msp.add_line(c[0], c[1])
    ln.rgb = (1, 2, 3)

# ---- render ----
ctx = RenderContext(doc)
backend = SVGBackend()
cfg = Configuration(background_policy=BackgroundPolicy.BLACK, color_policy=ColorPolicy.COLOR)
Frontend(ctx, backend, config=cfg).draw_layout(msp, finalize=True)
svg = backend.get_string(layout.Page(0, 0))

m = re.search(r"\.(C[0-9A-Fa-f]+) \{stroke: #010203;", svg)
assert m, "calib class not found"
cls = m.group(1)
paths = re.findall(r'<path d="M (-?[\d.]+) (-?[\d.]+) l (-?[\d.]+) (-?[\d.]+)" class="%s" />' % cls, svg)
assert len(paths) == 2, paths
paths = [tuple(map(float, p)) for p in paths]
paths.sort(key=lambda p: -p[1])
(c1x, c1y, c1dx, _), (c2x, c2y, c2dx, _) = paths
c1x0 = min(c1x, c1x + c1dx)
c2x0 = min(c2x, c2x + c2dx)
s_y = (c1y - c2y) / (CAL2[0][1] - CAL1[0][1])
s_x = (c2x0 - c1x0) / (CAL2[0][0] - CAL1[0][0])
assert abs(s_x - s_y) < 0.02, (s_x, s_y)
S = (s_x + s_y) / 2
X0a = CAL1[0][0] - c1x0 / S
X0b = CAL2[0][0] - c2x0 / S
YTa = CAL1[0][1] + c1y / S
YTb = CAL2[0][1] + c2y / S
assert abs(X0a - X0b) < 0.02 and abs(YTa - YTb) < 0.02
X0 = (X0a + X0b) / 2
YT = (YTa + YTb) / 2
print(f"scale={S:.6f} X0={X0:.4f} YT={YT:.4f}")

def to_plan(p):
    return (round(p[0] - X0, 3), round(YT - p[1], 3))

svg = re.sub(r'<path d="M -?[\d.]+ -?[\d.]+ l -?[\d.]+ -?[\d.]+" class="%s" />' % cls, "", svg)
svg = re.sub(r"<style>\.%s \{[^}]*\}</style>" % cls, "", svg)

mm = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
VW, VH = int(mm.group(1)), int(mm.group(2))
Wcm, Hcm = VW / S, VH / S
print(f"plan size: {Wcm:.2f} x {Hcm:.2f} cm")
svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
svg = re.sub(r'width="[\d.]+mm" height="[\d.]+mm" ', "", svg, count=1)
svg = svg.replace(f'viewBox="0 0 {VW} {VH}"', f'viewBox="0 0 {Wcm:.3f} {Hcm:.3f}"', 1)
svg = re.sub(r'<rect fill="#000000" x="0" y="0" width="\d+" height="\d+"',
             f'<rect id="bg" fill="#000000" x="0" y="0" width="{Wcm:.3f}" height="{Hcm:.3f}"', svg, count=1)
svg = svg.replace('<g stroke-linecap="round"', f'<g transform="scale({1/S:.9f})"><g stroke-linecap="round"', 1)
svg = svg.replace("</svg>", "</g></svg>", 1)

with open(SCRATCH + r"\base_cm.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"base_cm.svg: {len(svg)} chars")

# ---- geometry walk: snap points, all segments, wall segments ----
def visible(layer_name):
    try:
        lay = doc.layers.get(layer_name)
        return not (lay.is_frozen() or lay.is_off())
    except Exception:
        return True

snap = {}
segs = []
wall_segs = []

def add_snap(p, kind):
    key = (round(p[0], 2), round(p[1], 2))
    pri = {"end": 3, "int": 4, "mid": 2, "cen": 2, "quad": 1}[kind]
    old = snap.get(key)
    if old is None or pri > old[0]:
        snap[key] = (pri, kind)

def seg(a, b, is_wall):
    segs.append((a, b))
    if is_wall:
        wall_segs.append((a, b))
    add_snap(a, "end")
    add_snap(b, "end")
    add_snap(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2), "mid")

def walk(e, depth=0, parent_wall=False):
    if depth > 6:
        return
    t = e.dxftype()
    if not visible(e.dxf.layer):
        return
    is_wall = parent_wall or (e.dxf.layer in WALL_LAYERS)
    if t == "INSERT":
        for v in e.virtual_entities():
            walk(v, depth + 1, is_wall)
    elif t == "LINE":
        seg(to_plan((e.dxf.start.x, e.dxf.start.y)), to_plan((e.dxf.end.x, e.dxf.end.y)), is_wall)
    elif t == "LWPOLYLINE":
        pts = [to_plan((p[0], p[1])) for p in e.get_points()]
        closed = e.closed
        for i in range(len(pts) - (0 if closed else 1)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if a != b:
                seg(a, b, is_wall)
    elif t == "POLYLINE":
        try:
            pts = [to_plan((v.dxf.location.x, v.dxf.location.y)) for v in e.vertices]
            for i in range(len(pts) - 1):
                seg(pts[i], pts[i + 1], is_wall)
        except Exception:
            pass
    elif t == "CIRCLE":
        c = to_plan((e.dxf.center.x, e.dxf.center.y))
        add_snap(c, "cen")
        r = e.dxf.radius
        for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r)):
            add_snap((c[0] + dx, c[1] + dy), "quad")
    elif t == "ARC":
        c = to_plan((e.dxf.center.x, e.dxf.center.y))
        add_snap(c, "cen")
        add_snap(to_plan((e.start_point.x, e.start_point.y)), "end")
        add_snap(to_plan((e.end_point.x, e.end_point.y)), "end")

for e in msp:
    walk(e)
print(f"segments: {len(segs)} (wall: {len(wall_segs)}), snaps: {len(snap)}")

# ---- intersections ----
def isect(a, b, c, d):
    r = (b[0] - a[0], b[1] - a[1]); s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / den
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (a[0] + t * r[0], a[1] + t * r[1])
    return None

N = len(segs)
for i in range(N):
    a, b = segs[i]
    ax0, ax1 = min(a[0], b[0]) - .01, max(a[0], b[0]) + .01
    ay0, ay1 = min(a[1], b[1]) - .01, max(a[1], b[1]) + .01
    for j in range(i + 1, N):
        c, d = segs[j]
        if max(c[0], d[0]) < ax0 or min(c[0], d[0]) > ax1:
            continue
        if max(c[1], d[1]) < ay0 or min(c[1], d[1]) > ay1:
            continue
        p = isect(a, b, c, d)
        if p:
            add_snap(p, "int")
print(f"snaps total: {len(snap)}")

# ---- interior dims ----
dims_out = []
for dd in dims_raw:
    a = math.radians(dd["angle"])
    u_w = (math.cos(a), math.sin(a))
    P = dd["defpoint"]; O2 = dd["p2"]; O3 = dd["p3"]
    def proj(o):
        t = (o[0] - P[0]) * u_w[0] + (o[1] - P[1]) * u_w[1]
        return (P[0] + t * u_w[0], P[1] + t * u_w[1])
    dims_out.append({
        "v": fmt(dd["measure"]), "meas": dd["measure"], "rot": -dd["angle"] % 360,
        "o2": to_plan(O2), "o3": to_plan(O3),
        "q2": to_plan(proj(O2)), "q3": to_plan(proj(O3)),
        "t": to_plan(dd["tmid"]),
    })

# ---- wall geometry analysis: ray casting ----
def ray_hits(p, dx, dy, seg_list):
    """distances t>0 along (dx,dy) where the ray from p crosses a segment"""
    hits = []
    for a, b in seg_list:
        rx, ry = b[0] - a[0], b[1] - a[1]
        den = dx * ry - dy * rx
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - p[0]) * ry - (a[1] - p[1]) * rx) / den
        u_ = ((a[0] - p[0]) * dy - (a[1] - p[1]) * dx) / den
        if t > 1e-9 and -1e-9 <= u_ <= 1 + 1e-9:
            hits.append(t)
    return sorted(hits)

wall_xs = sorted({round(v, 2) for a, b in wall_segs for v in (a[0], b[0])})
wall_ys = sorted({round(v, 2) for a, b in wall_segs for v in (a[1], b[1])})

def snap_val(v, vals, tol=1.5):
    best, bd = v, tol
    for w in vals:
        if abs(w - v) < bd:
            bd = abs(w - v); best = w
    return best

def profile(side):
    """side: 'top'|'bottom'|'left'|'right' -> list of (c0, c1, boundary_val)"""
    STEP = 0.5
    if side in ("top", "bottom"):
        rng, vals = Wcm, wall_xs
        def probe(c):
            hits = ray_hits((c, -10000 if side == "top" else Hcm + 10000),
                            0, 1 if side == "top" else -1, wall_segs)
            if not hits:
                return None
            t = hits[0]
            return (-10000 + t) if side == "top" else (Hcm + 10000 - t)
    else:
        rng, vals = Hcm, wall_ys
        def probe(c):
            hits = ray_hits((-10000 if side == "left" else Wcm + 10000, c),
                            1 if side == "left" else -1, 0, wall_segs)
            if not hits:
                return None
            t = hits[0]
            return (-10000 + t) if side == "left" else (Wcm + 10000 - t)
    samples = []
    c = 0.25
    while c < rng:
        samples.append((c, probe(c)))
        c += STEP
    ivals = []
    cur_v, cur_start = None, None
    breaks = wall_xs if side in ("top", "bottom") else wall_ys
    for c, v in samples + [(rng, None)]:
        if v is None or (cur_v is not None and abs(v - cur_v) > 0.6):
            if cur_v is not None:
                ivals.append((cur_start, snap_val(c - 0.25, breaks), cur_v))
            cur_v, cur_start = None, None
            if v is not None:
                cur_v, cur_start = v, snap_val(c - 0.25, breaks)
        elif cur_v is None and v is not None:
            cur_v, cur_start = v, snap_val(c - 0.25, breaks)
        elif v is not None:
            cur_v = v  # track slight drift
    # merge tiny and snap boundary values
    out = []
    for c0, c1, v in ivals:
        if c1 - c0 < 2.0:
            continue
        vv = snap_val(v, wall_ys if side in ("top", "bottom") else wall_xs, 1.0)
        out.append((round(c0, 2), round(c1, 2), round(vv, 2)))
    return out

def clean_profile(side, ivals):
    """bridge openings (same plane both sides), drop intervals far from the facade extreme"""
    if not ivals:
        return ivals
    # bridge: A | gap-with-inward-jump | B  where A.v == B.v
    out = list(ivals)
    changed = True
    while changed:
        changed = False
        for i in range(len(out) - 2):
            a, g, b = out[i], out[i + 1], out[i + 2]
            if abs(a[2] - b[2]) < 1.0 and (g[1] - g[0]) < 180 and abs(g[2] - a[2]) > 25:
                out[i:i + 3] = [(a[0], b[1], a[2])]
                changed = True
                break
    # merge adjacent same-plane
    merged = [out[0]]
    for iv in out[1:]:
        if abs(iv[2] - merged[-1][2]) < 1.0 and abs(iv[0] - merged[-1][1]) < 1.0:
            merged[-1] = (merged[-1][0], iv[1], merged[-1][2])
        else:
            merged.append(iv)
    # drop far-from-facade intervals
    if side in ("top", "left"):
        extreme = min(i[2] for i in merged)
        merged = [i for i in merged if i[2] - extreme < 500]
    else:
        extreme = max(i[2] for i in merged)
        merged = [i for i in merged if extreme - i[2] < 500]
    return merged

profiles = {s: clean_profile(s, profile(s)) for s in ("top", "bottom", "left", "right")}
for s, iv in profiles.items():
    print(f"{s}: {[(float(a), float(b), float(v)) for a, b, v in iv]}")

# every boundary coordinate must be an exact wall-line coordinate
for s, iv in profiles.items():
    vals = wall_ys if s in ("top", "bottom") else wall_xs
    brks = wall_xs if s in ("top", "bottom") else wall_ys
    for c0, c1, v in iv:
        assert any(abs(v - w) < 0.05 for w in vals), (s, v, "plane not on wall line")
        assert any(abs(c0 - w) < 0.05 for w in brks), (s, c0, "break not on wall coord")
        assert any(abs(c1 - w) < 0.05 for w in brks), (s, c1, "break not on wall coord")
print("all exterior chain coordinates verified on exact wall lines")

# diagnostics for manual review
print("vertical wall lines with x in [90,140]:")
for a, b in wall_segs:
    if abs(a[0] - b[0]) < 0.01 and 90 <= a[0] <= 140:
        print(f"  x={a[0]:.2f} y {min(a[1],b[1]):.1f}..{max(a[1],b[1]):.1f}")
print("horizontal wall lines with y in [60,175]:")
for a, b in wall_segs:
    if abs(a[1] - b[1]) < 0.01 and 60 <= a[1] <= 175:
        print(f"  y={a[1]:.2f} x {min(a[0],b[0]):.1f}..{max(a[0],b[0]):.1f}")

# wall bbox for chain placement
wx0 = min(min(a[0], b[0]) for a, b in wall_segs)
wx1 = max(max(a[0], b[0]) for a, b in wall_segs)
wy0 = min(min(a[1], b[1]) for a, b in wall_segs)
wy1 = max(max(a[1], b[1]) for a, b in wall_segs)
print(f"wall bbox: ({wx0:.2f},{wy0:.2f})-({wx1:.2f},{wy1:.2f})")

# exterior chains -> dim structures
ext_dims = []
OFF1, OFF2 = 55, 100
BOT1, BOT2 = 135, 180   # bottom offsets clear the outward-swinging entry door arc
def add_ext(side, ivals):
    if not ivals:
        return
    lo = min(i[0] for i in ivals)
    hi = max(i[1] for i in ivals)
    for c0, c1, v in ivals:
        L = c1 - c0
        if L < 2:
            continue
        if side == "top":
            line_y = wy0 - OFF1
            ext_dims.append({"v": fmt(L), "meas": L, "rot": 0,
                             "o2": (c0, v), "o3": (c1, v), "q2": (c0, line_y), "q3": (c1, line_y),
                             "t": ((c0 + c1) / 2, line_y - 9)})
        elif side == "bottom":
            line_y = wy1 + BOT1
            ext_dims.append({"v": fmt(L), "meas": L, "rot": 0,
                             "o2": (c0, v), "o3": (c1, v), "q2": (c0, line_y), "q3": (c1, line_y),
                             "t": ((c0 + c1) / 2, line_y + 14)})
        elif side == "left":
            line_x = wx0 - OFF1
            ext_dims.append({"v": fmt(L), "meas": L, "rot": 90,
                             "o2": (v, c0), "o3": (v, c1), "q2": (line_x, c0), "q3": (line_x, c1),
                             "t": (line_x - 9, (c0 + c1) / 2)})
        else:
            line_x = wx1 + OFF1
            ext_dims.append({"v": fmt(L), "meas": L, "rot": 90,
                             "o2": (v, c0), "o3": (v, c1), "q2": (line_x, c0), "q3": (line_x, c1),
                             "t": (line_x + 12, (c0 + c1) / 2)})
    # overall
    T = hi - lo
    if side == "top":
        ext_dims.append({"v": fmt(T), "meas": T, "rot": 0, "o2": (lo, ivals[0][2]), "o3": (hi, ivals[-1][2]),
                         "q2": (lo, wy0 - OFF2), "q3": (hi, wy0 - OFF2), "t": ((lo + hi) / 2, wy0 - OFF2 - 9), "overall": 1})
    elif side == "left":
        ext_dims.append({"v": fmt(T), "meas": T, "rot": 90, "o2": (ivals[0][2], lo), "o3": (ivals[-1][2], hi),
                         "q2": (wx0 - OFF2, lo), "q3": (wx0 - OFF2, hi), "t": (wx0 - OFF2 - 9, (lo + hi) / 2), "overall": 1})
    elif side == "bottom":
        ext_dims.append({"v": fmt(T), "meas": T, "rot": 0, "o2": (lo, ivals[0][2]), "o3": (hi, ivals[-1][2]),
                         "q2": (lo, wy1 + BOT2), "q3": (hi, wy1 + BOT2), "t": ((lo + hi) / 2, wy1 + BOT2 + 14), "overall": 1})
    else:
        ext_dims.append({"v": fmt(T), "meas": T, "rot": 90, "o2": (ivals[0][2], lo), "o3": (ivals[-1][2], hi),
                         "q2": (wx1 + OFF2, lo), "q3": (wx1 + OFF2, hi), "t": (wx1 + OFF2 + 12, (lo + hi) / 2), "overall": 1})

for s in ("top", "bottom", "left", "right"):
    add_ext(s, profiles[s])
print(f"ext dims: {len(ext_dims)}")

# chain sum checks
for s in ("top", "bottom", "left", "right"):
    iv = profiles[s]
    if not iv:
        continue
    total = max(i[1] for i in iv) - min(i[0] for i in iv)
    ssum = sum(i[1] - i[0] for i in iv)
    gaps = total - ssum
    print(f"chain {s}: sum={ssum:.2f} total={total:.2f} gaps={gaps:.2f}")

# ---- wall thickness probes at each interior dim ----
thick = []
for dm in dims_out:
    horiz = dm["rot"] % 180 == 0
    for o_name, direction in (("o2", -1), ("o3", 1)):
        o = dm[o_name]
        other = dm["o3" if o_name == "o2" else "o2"]
        d_vec = (o[0] - other[0], o[1] - other[1])
        L = math.hypot(*d_vec) or 1
        d_vec = (d_vec[0] / L, d_vec[1] / L)
        hits = ray_hits(o, d_vec[0], d_vec[1], wall_segs)
        hits = [h for h in hits if h > 0.5]
        if hits and hits[0] < 60:
            thick.append({"dim": dm["v"], "at": o_name, "t": round(hits[0], 2)})
print("wall thickness probes:")
from collections import Counter
tc = Counter(t["t"] for t in thick)
for v, n in sorted(tc.items()):
    print(f"  {v} cm x{n}")

data = {
    "W": round(Wcm, 3), "H": round(Hcm, 3),
    "wallBox": [round(wx0, 2), round(wy0, 2), round(wx1, 2), round(wy1, 2)],
    "wcsOrigin": [round(X0, 4), round(YT, 4)],
    "dims": dims_out,
    "extDims": ext_dims,
    "snaps": [[k[0], k[1], v[1]] for k, v in snap.items()],
    "walls": [[round(a[0], 2), round(a[1], 2), round(b[0], 2), round(b[1], 2)] for a, b in wall_segs],
    "thickness": thick,
}
with open(SCRATCH + r"\plan_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
print(f"plan_data.json written: snaps={len(snap)} walls={len(wall_segs)} ext={len(ext_dims)}")
