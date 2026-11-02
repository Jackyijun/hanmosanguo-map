# -*- coding: utf-8 -*-
"""疆域计算：代价栅格 + 多源最短路 + 平滑等值线。

1. 海陆栅格化（大湖不可通行）。
2. 代价栅格：平地 1；ETOPO20 地形起伏、高原海拔加代价；山脉脊线“烧”出高斯形高代价带；
   江、河、淮、汉加界河代价；再乘一层固定种子的平滑噪声，让界线带自然弯曲。
3. 以全部种子为源点跑一次多源 Dijkstra，每格归“代价距离”最近的种子；
   超出该种子可达距离的格子算无主地（草原深处、高原腹地）。
   这是一种加权 Voronoi：边界被山脊、河道吸过去，不再是直线和圆弧。
4. 每个节点按“种子 → 单位”合并格子，高斯平滑后用 marching squares 描出 0.5 等值线。
"""
import gzip, math
import numpy as np
from scipy import ndimage, sparse
from scipy.sparse.csgraph import dijkstra
from scipy.interpolate import RegularGridInterpolator
from skimage.draw import polygon as draw_polygon, line as draw_line
from skimage.measure import find_contours
from shapely.geometry import Polygon, MultiPolygon, LineString
from shapely.ops import unary_union, polygonize, linemerge
from shapely.strtree import STRtree
import shapely

import config as C


def dec(flat):
    out = []; x = y = 0
    for i in range(0, len(flat), 2):
        x += flat[i]; y += flat[i + 1]; out.append((x / 100, y / 100))
    return out


def enc(pts):
    out = []; px = py = 0
    for lo, la in pts:
        X = int(round(lo * 100)); Y = int(round(la * 100))
        out += [X - px, Y - py]; px, py = X, Y
    return out


def densify(pts, step=0.04):
    out = []
    for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.ceil(math.hypot(c - a, d - b) / step)))
        for k in range(n): out.append((a + (c - a) * k / n, b + (d - b) * k / n))
    out.append(tuple(pts[-1]))
    return out


class Grid:
    def __init__(self):
        self.lon0, self.lon1 = C.GRID_LON
        self.lat0, self.lat1 = C.GRID_LAT
        self.res = C.RES
        self.W = int(round((self.lon1 - self.lon0) / self.res))
        self.H = int(round((self.lat1 - self.lat0) / self.res))
        self.lons = self.lon0 + (np.arange(self.W) + 0.5) * self.res
        self.lats = self.lat1 - (np.arange(self.H) + 0.5) * self.res
        self.coslat = np.cos(np.radians(self.lats))

    def rc(self, lon, lat):
        return (self.lat1 - lat) / self.res - 0.5, (lon - self.lon0) / self.res - 0.5

    def ll(self, r, c):
        return self.lon0 + (c + 0.5) * self.res, self.lat1 - (r + 0.5) * self.res

    def fill_rings(self, arr, rings, value):
        for ring in rings:
            rr, cc = zip(*[self.rc(lo, la) for lo, la in ring])
            pr, pc = draw_polygon(np.array(rr), np.array(cc), shape=arr.shape)
            arr[pr, pc] = value

    def burn_lines(self, lines):
        m = np.zeros((self.H, self.W), bool)
        for pts in lines:
            pts = densify(pts)
            for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
                r0, c0 = self.rc(a, b); r1, c1 = self.rc(c, d)
                rr, cc = draw_line(int(round(r0)), int(round(c0)), int(round(r1)), int(round(c1)))
                ok = (rr >= 0) & (rr < self.H) & (cc >= 0) & (cc < self.W)
                m[rr[ok], cc[ok]] = True
        return m

    def dist_deg(self, mask):
        """到 mask 的距离（°，经向按 cos(纬度) 缩放的近似）。"""
        d = ndimage.distance_transform_edt(~mask, sampling=(1.0, 0.82))
        return d * self.res


def load_land(G, base):
    land = np.zeros((G.H, G.W), bool)
    for poly in base["land"]:
        rings = [dec(r) for r in poly]
        G.fill_rings(land, rings[:1], True)
        G.fill_rings(land, rings[1:], False)
    lake = np.zeros_like(land)
    for lk in base["lakes"]:
        ring = dec(lk["r"])
        if Polygon(ring).area >= C.BIG_LAKE_AREA:
            G.fill_rings(lake, [ring], True)
    return land, lake & land


def load_dem(G):
    d = C.GEODATA / "etopo20"
    z = np.loadtxt(gzip.open(d / "etopo20data.gz"))
    lo = np.loadtxt(gzip.open(d / "etopo20lons.gz"))
    la = np.loadtxt(gzip.open(d / "etopo20lats.gz"))
    # 地形起伏：米 / 度（经向按纬度缩放）
    zs = ndimage.gaussian_filter(z, 0.6)
    gy, gx = np.gradient(zs, la, lo)
    gx = gx / np.cos(np.radians(la))[:, None].clip(0.2)
    relief = np.hypot(gx, gy)
    LO, LA = np.meshgrid(G.lons, G.lats)
    pts = np.stack([LA.ravel(), LO.ravel()], 1)
    elev = RegularGridInterpolator((la, lo), z)(pts).reshape(LA.shape)
    rel = RegularGridInterpolator((la, lo), relief)(pts).reshape(LA.shape)
    return elev, rel


def smooth_noise(G):
    rng = np.random.default_rng(C.NOISE_SEED)
    acc = np.zeros((G.H, G.W))
    for s in C.NOISE_SIGMAS:
        n = ndimage.gaussian_filter(rng.standard_normal((G.H, G.W)), s, mode="wrap")
        acc += n / n.std()
    acc /= acc.std()
    return np.clip(acc / 2.2, -1, 1)


def wiggle(pts, k):
    """手绘山脊是几段直线；按固定种子给它加一点平滑的横向摆动，免得界线被吸成直线。"""
    p = np.array(densify(pts, 0.03))
    if len(p) < 3: return p.tolist()
    seg = np.diff(p, axis=0)
    s = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
    t = np.gradient(p, axis=0); t /= np.hypot(t[:, 0], t[:, 1])[:, None].clip(1e-9)
    nrm = np.stack([-t[:, 1], t[:, 0]], 1)
    rng = np.random.default_rng(C.NOISE_SEED * 1000 + k)
    off = np.zeros(len(p))
    for wl, amp in zip(C.RIDGE_WAVES, C.RIDGE_AMPS):
        off += amp * np.sin(2 * np.pi * s / wl + rng.uniform(0, 2 * np.pi))
    taper = np.clip(np.minimum(s, s[-1] - s) / 0.3, 0, 1)      # 两端收回原位
    return (p + nrm * (off * taper)[:, None]).tolist()


def cost_raster(G, land, lake, elev, relief, ranges, rivers):
    cost = np.ones((G.H, G.W))
    cost += np.clip(relief / C.RELIEF_SCALE, 0, C.RELIEF_MAX)
    a, b, c = C.PLATEAU
    cost += c * np.clip((elev - a) / (b - a), 0, 1)
    for major in (True, False):
        lines = [wiggle(r["geo"], k) for k, r in enumerate(ranges) if bool(r.get("major")) == major]
        if lines:
            d = G.dist_deg(G.burn_lines(lines))
            cost += C.RANGE_PEAK[major] * np.exp(-(d / C.RANGE_WIDTH) ** 2)
    for peak, lines in rivers:
        d = G.dist_deg(G.burn_lines(lines))
        cost += peak * np.exp(-(d / C.RIVER_WIDTH) ** 2)
    cost *= 1 + C.NOISE_AMP * smooth_noise(G)
    passable = land & ~lake
    cost[~passable] = np.inf
    return cost, passable


def partition(G, cost, passable, seeds):
    """多源 Dijkstra：返回每格的种子号（-1 无主）与代价距离。"""
    H, W = G.H, G.W
    idx = np.arange(H * W).reshape(H, W)
    rows, cols, wts = [], [], []
    dy = G.res
    flat = cost.ravel()
    # 16 邻接（含“马步”）：比 8 邻接更接近各向同性，平地上的分界不会顺着格网走成横平竖直
    for (di, dj) in ((0, 1), (1, 0), (1, 1), (1, -1), (1, 2), (2, 1), (1, -2), (2, -1)):
        c0, c1 = max(0, -dj), W - max(0, dj)
        a = idx[0:H - di, c0:c1]
        b = idx[di:H, c0 + dj:c1 + dj]
        ra = a // W
        lat_mid = G.lats[ra] - di * G.res / 2
        dx = G.res * np.cos(np.radians(lat_mid)) * abs(dj)
        L = np.hypot(dx, dy * di)
        ca = flat[a]; cb = flat[b]
        if abs(di) + abs(dj) == 3:      # 马步跨过的两格也计入，免得跳过窄的山脊、界河
            if abs(dj) == 2:
                sg = 1 if dj > 0 else -1
                s1, s2 = a + sg, a + W + sg
            else:
                s1, s2 = a + W, a + W + dj
            m = 0.25 * (ca + cb + flat[s1] + flat[s2])
        else:
            m = 0.5 * (ca + cb)
        ok = np.isfinite(m)
        rows.append(a[ok]); cols.append(b[ok]); wts.append(m[ok] * L[ok])
    g = sparse.csr_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))), shape=(H * W, H * W))
    # 种子落到最近的可通行格
    dmap, (ii, jj) = ndimage.distance_transform_edt(~passable, return_indices=True)
    src_nodes, used = [], {}
    for k, s in enumerate(seeds):
        r, c = G.rc(s["lon"], s["lat"])
        r = int(round(min(max(r, 0), H - 1))); c = int(round(min(max(c, 0), W - 1)))
        r, c = ii[r, c], jj[r, c]
        n = r * W + c
        step = 0
        while n in used:          # 两点落在同一格时挪到旁边的可通行格
            step += 1
            for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                r2, c2 = r + dr * step, c + dc * step
                if 0 <= r2 < H and 0 <= c2 < W and passable[r2, c2] and r2 * W + c2 not in used:
                    n = r2 * W + c2; break
        used[n] = k; src_nodes.append(n)
    dist, pred, src = dijkstra(g, directed=False, indices=src_nodes, return_predecessors=True, min_only=True)
    node2seed = np.full(H * W, -1, np.int32)
    lut = np.full(H * W, -1, np.int64)
    lut[np.array(src_nodes)] = np.arange(len(seeds))
    ok = src >= 0
    node2seed[ok] = lut[src[ok]]
    reach = np.array([(s.get("R") or C.REACH_DEFAULT[s["t"]]) * C.REACH_MULT for s in seeds])
    lab = node2seed.copy()
    far = ((lab >= 0) & (dist > reach[np.maximum(lab, 0)])).reshape(H, W)
    # 只有连成大片的“够不到”才算无主地；夹在疆域中间的小块（山脊上的空隙）仍归最近的种子
    comp, n = ndimage.label(far, structure=np.ones((3, 3)))
    if n:
        sizes = ndimage.sum(far, comp, range(1, n + 1))
        big = np.zeros(n + 1, bool); big[1:] = sizes >= C.MIN_WILD_CELLS
        far = big[comp]
    lab = lab.reshape(H, W)
    lab[far] = -1
    # 外缘：每个种子的可达范围各自是一圈等代价线，连起来是一串圆弧。
    # 先做形态学闭运算填平圆弧之间的凹口，再高斯平滑削掉小凸起，得到一条连贯的外缘。
    nearest = node2seed.reshape(H, W)
    claimed = lab >= 0
    r = C.FRONTIER_CLOSE / G.res
    grown = ndimage.distance_transform_edt(~claimed) <= r
    closed = ~(ndimage.distance_transform_edt(grown) <= r)
    closed = ndimage.gaussian_filter(closed.astype(float), C.FRONTIER_SMOOTH) > 0.5
    closed &= passable & (nearest >= 0)
    add = closed & ~claimed
    lab[add] = nearest[add]
    lab[claimed & ~closed] = -1
    return lab, dist.reshape(H, W)


def extend_into_water(G, lab, land, passable):
    """把归属向海面外延若干格、向湖面全部外延，海岸由前端剪裁。"""
    water = ~passable
    d, (ii, jj) = ndimage.distance_transform_edt(water, return_indices=True)
    lake = land & ~passable
    ext = water & ((d <= C.SEA_FILL_CELLS) | lake)
    out = lab.copy()
    out[ext] = lab[ii[ext], jj[ext]]
    return out


def warp(G, lab):
    """平原上两点之间的分界是一条直的中垂线；给整张归属栅格加一层平滑的位移场，
    让所有分界都带上河曲一样的小弯。位移远小于平滑尺度，不会撕裂或折叠。"""
    rng = np.random.default_rng(C.NOISE_SEED + 7)
    dr = np.zeros((G.H, G.W)); dc = np.zeros((G.H, G.W))
    for sigma, amp in C.WARP:
        for d in (dr, dc):
            n = ndimage.gaussian_filter(rng.standard_normal((G.H, G.W)), sigma, mode="wrap")
            d += amp * n / n.std()
    rr, cc = np.mgrid[0:G.H, 0:G.W].astype(float)
    return ndimage.map_coordinates(lab, [rr + dr, cc + dc], order=0, mode="nearest").astype(lab.dtype)


# ---------------------------------------------------------------- 多边形
def _even_odd(rings):
    polys = []
    for ring in rings:
        if len(ring) < 4: continue
        p = Polygon(ring)
        if not p.is_valid: p = p.buffer(0)
        if p.is_empty or p.area < 1e-6: continue
        polys.append(p)
    polys.sort(key=lambda p: -p.area)
    acc = None
    for p in polys:
        acc = p if acc is None else acc.symmetric_difference(p)
    return acc


def mask_geom(G, mask, sigma=None):
    """布尔栅格 → 平滑后的 shapely 多边形（经纬度）。"""
    sigma = C.SMOOTH_SIGMA if sigma is None else sigma
    rr, cc = np.nonzero(mask)
    if not len(rr): return None
    pad = int(3 * sigma) + 3
    r0, r1 = max(rr.min() - pad, 0), min(rr.max() + pad + 1, G.H)
    c0, c1 = max(cc.min() - pad, 0), min(cc.max() + pad + 1, G.W)
    sub = np.pad(mask[r0:r1, c0:c1].astype(float), 1)
    f = ndimage.gaussian_filter(sub, sigma, mode="constant")
    rings = []
    for cn in find_contours(f, 0.5):
        r = cn[:, 0] - 1 + r0; c = cn[:, 1] - 1 + c0
        lon = G.lon0 + (c + 0.5) * G.res; lat = G.lat1 - (r + 0.5) * G.res
        rings.append(list(zip(lon, lat)))
    g = _even_odd(rings)
    if g is None or g.is_empty: return None
    return shapely.set_precision(g, 1e-6)


def _parts(g):
    if g is None or g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    return [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]


def coverage(G, label_geoms, seedlab, seed2label, tol):
    """把各单位独立平滑出的多边形拼成一张无缝无叠的覆盖图，再整体简化。

    各单位的等值线在两两相邻处本来就重合，只在三方交汇点附近留下小缝。
    这里把全部等值线打断成面，每个面按所在多边形归属；落在缝里的面按栅格原归属分配，
    然后用覆盖简化（coverage simplify）同时简化共享边，相邻两块的界线始终是同一条线。
    """
    labels = [k for k, g in label_geoms.items() if g is not None]
    if not labels: return {}
    geoms = [label_geoms[k] for k in labels]
    lines = []
    for g in geoms:
        for p in _parts(g):
            lines.append(LineString(p.exterior.coords))
            lines += [LineString(h.coords) for h in p.interiors]
    faces = list(polygonize(unary_union(lines)))
    tree = STRtree(geoms)
    bucket = {}
    for f in faces:
        if f.area < 1e-9: continue
        pt = f.representative_point()
        hit = tree.query(pt, predicate="intersects")
        if len(hit):
            k = labels[int(hit[0])]
        else:
            r, c = G.rc(pt.x, pt.y)
            r = int(min(max(round(r), 0), G.H - 1)); c = int(min(max(round(c), 0), G.W - 1))
            k = seed2label.get(int(seedlab[r, c]))
            if k is None: continue
        bucket.setdefault(k, []).append(f)
    keys = sorted(bucket, key=str)
    merged = [unary_union(bucket[k]) for k in keys]
    simp = shapely.coverage_simplify(merged, tol)
    return {k: g for k, g in zip(keys, simp) if not g.is_empty}


def merge_outline(polys):
    """多个覆盖多边形合并成政权外轮廓（共享边完全重合，合并后无缝）。"""
    g = unary_union(polys)
    ps = []
    for p in _parts(g):
        if p.area < C.MIN_PART_AREA: continue
        holes = [h for h in p.interiors if Polygon(h).area >= C.MIN_HOLE_AREA]
        ps.append(Polygon(p.exterior, holes))
    if not ps: return None
    return ps[0] if len(ps) == 1 else MultiPolygon(ps)


def rings_of(g):
    if g is None: return []
    parts = [g] if g.geom_type == "Polygon" else list(g.geoms)
    out = []
    for p in parts:
        out.append(enc(list(p.exterior.coords)[:-1]))
        for h in p.interiors: out.append(enc(list(h.coords)[:-1]))
    return out


def anchor(G, mask):
    """注记点：最大一块陆地的不可达极点。返回 [经, 纬, 面积(平方度), 内切半径(°)]。"""
    lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
    if n == 0: return None
    sizes = ndimage.sum(mask, lab, range(1, n + 1))
    k = int(np.argmax(sizes)) + 1
    comp = lab == k
    rr, cc = np.nonzero(comp)
    r0, r1, c0, c1 = rr.min(), rr.max() + 1, cc.min(), cc.max() + 1
    sub = np.pad(comp[r0:r1, c0:c1], 1)
    latc = G.lats[int((r0 + r1) / 2)]
    kx = math.cos(math.radians(latc))
    dt = ndimage.distance_transform_edt(sub, sampling=(1.0, kx))
    i, j = np.unravel_index(int(np.argmax(dt)), dt.shape)
    lon, lat = G.ll(i - 1 + r0, j - 1 + c0)
    area = float(sizes[k - 1]) * G.res * G.res * kx
    return [round(lon, 2), round(lat, 2), round(area, 2), round(float(dt.max()) * G.res, 2)]


def boundary_lines(polys):
    """覆盖图里相邻多边形之间的共享边（即内部分界线，不含外缘）。"""
    if len(polys) < 2: return []
    allb = unary_union([p.boundary for p in polys])
    outer = unary_union(polys).boundary
    inner = allb.difference(outer.buffer(1e-6))
    if inner.is_empty: return []
    if inner.geom_type == "MultiLineString": inner = linemerge(inner)
    ls = [inner] if inner.geom_type == "LineString" else [x for x in getattr(inner, "geoms", []) if x.geom_type == "LineString"]
    return [enc(list(l.coords)) for l in ls if l.length > 0.08]
