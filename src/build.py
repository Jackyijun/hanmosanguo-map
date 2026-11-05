# -*- coding: utf-8 -*-
"""汉末三国形势图 · 数据构建。

读 content/ 的史料与 geodata/ 的底图，算出 36 个时间节点的疆域多边形，
写出 build/geo.json（几何）、build/data.json（条目与说明）、build/colors.json（疆域色）。
"""
import json, sys, time
from collections import Counter
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import config as C
sys.path.insert(0, str(C.CONTENT))
from seeds import SEEDS
from units import UNITS
from nodes import NODES
import items as I
import terrain as T

UK = {u["k"]: i for i, u in enumerate(UNITS)}
SI = {s["id"]: i for i, s in enumerate(SEEDS)}
assert len(SI) == len(SEEDS), "种子 id 重复"
JUN = {s["id"]: s for s in SEEDS if s["t"] == "z"}
HATCH = {"公孙氏", "士燮", "张鲁", "黑山"}       # 名义臣属、实则自立（斜线）
STATES = ("汉", "曹", "刘备", "孙", "晋")        # 州界只在这几个政权内部画


# ================================================================ 归属
def jun_of(s):
    return s["id"] if s["t"] == "z" else (s["j"] if s["j"] in JUN else None)

def zhou_han(s):
    j = jun_of(s)
    return JUN[j]["j"] if j else None

WEI = {"河南尹": "司州", "河内郡": "司州", "河东郡": "司州", "弘农郡": "司州",
       "京兆尹": "雍州", "左冯翊": "雍州", "右扶风": "雍州", "汉阳郡": "雍州", "陇西郡": "雍州", "安定郡": "雍州", "北地郡": "雍州", "武都郡": "雍州", "阴平": "雍州"}
JIN = {"河南尹": "司州", "河内郡": "司州", "河东郡": "司州", "弘农郡": "司州", "魏郡": "司州",
       "京兆尹": "雍州", "左冯翊": "雍州", "右扶风": "雍州", "安定郡": "雍州", "北地郡": "雍州",
       "汉阳郡": "秦州", "陇西郡": "秦州", "武都郡": "秦州", "阴平": "秦州",
       "汉中郡": "梁州", "巴郡": "梁州", "广汉郡": "梁州",
       "益州郡": "宁州", "永昌郡": "宁州",
       "辽东郡": "平州", "玄菟郡": "平州", "乐浪郡": "平州", "辽东属国": "平州",
       "平原郡": "冀州", "南海郡": "广州", "苍梧郡": "广州", "郁林郡": "广州"}
SEED_JIN = {"始安": "广州", "曲江": "广州", "临贺": "广州", "上庸": "荆州", "房陵": "荆州", "西城": "荆州"}
SEED_WEI = {"上庸": "荆州", "房陵": "荆州", "西城": "荆州"}

def zhou_of(s, y, owner_k):
    """某年某地属哪个州：220 年前用东汉十三州，三国用魏蜀吴各自的州，晋用太康十九州。"""
    j = jun_of(s)
    if not j: return None
    han = JUN[j]["j"]
    if y < 220: return han
    if y < 265:
        if owner_k == "刘备": return "益州"
        if owner_k == "孙":
            if han == "交州" and y >= 264 and j in ("南海郡", "苍梧郡", "郁林郡"): return "广州"
            return han
        return SEED_WEI.get(s["id"]) or WEI.get(j) or han
    if owner_k == "孙":
        if han == "交州" and (j in ("南海郡", "苍梧郡", "郁林郡") or s["id"] in ("临贺",)): return "广州"
        if s["id"] in ("始安", "曲江"): return "广州"
        return han
    return SEED_JIN.get(s["id"]) or JIN.get(j) or han

def seeds_in(kind, key):
    out = []
    for i, s in enumerate(SEEDS):
        if kind == "Z" and zhou_han(s) == key: out.append(i)
        elif kind == "J" and jun_of(s) == key: out.append(i)
        elif kind == "G" and s["j"] == key: out.append(i)
        elif kind == "ID" and s["id"].startswith(key): out.append(i)
        elif kind == "C" and s["id"] == key: out.append(i)
    if not out: raise KeyError(f"nodes.py：{kind} {key} 没有匹配的种子")
    return out

def ownership():
    """逐节点执行 nodes.py 的操作，得到每个种子归哪个单位、单位属哪个政权。"""
    state = [None] * len(SEEDS)
    pol, lab, seat = {}, {}, {}
    out = []
    for nd in NODES:
        y = nd["y"]
        for op in nd["ops"]:
            if op[0] == "ALL":
                for i, s in enumerate(SEEDS):
                    if jun_of(s): state[i] = op[1]
            elif op[0] == "REPL":
                state = [op[2] if x == op[1] else x for x in state]
                if op[1] in seat: seat[op[2]] = seat.get(op[2], seat[op[1]])
            else:
                kind, key, u = op
                for i in seeds_in(kind, key): state[i] = u
        if y >= 192:        # 林邑自 192 年立国
            state[SI["象林"]] = "林邑"; state[SI["林邑南"]] = "林邑"
        pol.update(nd["pol"]); lab.update(nd["lab"]); seat.update(nd["seat"])
        present = sorted(set(x for x in state if x), key=lambda k: UK[k])
        P = {k: pol.get(k) or UNITS[UK[k]].get("pol") or k for k in present}
        keys = sorted(set(present) | set(P.values()), key=lambda k: UK[k])
        out.append(dict(nd=nd, own=list(state), pol=P, lab={k: lab[k] for k in keys if k in lab},
                        seat={k: seat[k] for k in present if k in seat}))
    return out


# ================================================================ 疆域几何
def compute_snaps(base):
    t0 = time.time()
    G = T.Grid()
    land, lake = T.load_land(G, base)
    elev, relief = T.load_dem(G)
    ranges = [it for it in base["items"].values() if it["c"] == "range"]
    ranges += [dict(geo=g, major=mj) for (_, _, g, _, mj, _) in I.NEW_RANGES]
    name_of = {int(k): it["old"] for k, it in base["items"].items()}
    ren = {k: v[0] for k, v in I.RIVER_RENAME.items()}
    by_river = {}
    for r in base["rivers"]:
        nm = ren.get(name_of.get(r.get("it"), ""), None)
        if nm in C.RIVER_PEAK and r["k"] != "modern":
            by_river.setdefault(nm, []).append(T.dec(r["p"]))
    rivers = [(C.RIVER_PEAK[nm], lines) for nm, lines in sorted(by_river.items())]
    cost, passable = T.cost_raster(G, land, lake, elev, relief, ranges, rivers)
    print(f"   代价栅格 {G.W}×{G.H}，{time.time() - t0:.1f}s")
    seedlab_land, dist = T.partition(G, cost, passable, SEEDS)
    river_d = G.dist_deg(G.burn_lines([l for _, lines in rivers for l in lines]))
    hold = np.clip((river_d - C.WARP_RIVER_HOLD[0]) / C.WARP_RIVER_HOLD[1], 0, 1)
    seedlab = T.warp(G, T.extend_into_water(G, seedlab_land, land, passable), hold)
    print(f"   多源最短路完成，{time.time() - t0:.1f}s")

    cache, cov_cache = {}, {}
    def region(seed_ids):
        """一组种子合起来的平滑多边形（未简化）与注记点。"""
        key = tuple(sorted(seed_ids))
        if key not in cache:
            ids = np.array(key)
            g = T.mask_geom(G, np.isin(seedlab, ids))
            a = T.anchor(G, np.isin(seedlab_land, ids) & land)
            cache[key] = (g, a)
        return cache[key]

    def tiled(groups, tol):
        """groups: {标签: [种子]} → {标签: 覆盖多边形}，相同分组只算一次。"""
        key = (tol, tuple(sorted((str(k), tuple(sorted(v))) for k, v in groups.items())))
        if key not in cov_cache:
            geoms = {k: region(v)[0] for k, v in groups.items()}
            s2l = {i: k for k, v in groups.items() for i in v}
            cov_cache[key] = T.coverage(G, geoms, seedlab, s2l, tol)
        return cov_cache[key]

    snaps = []
    for r in ownership():
        nd = r["nd"]; y = nd["y"]; own = r["own"]
        seeds_of = {}
        for i, k in enumerate(own):
            if k: seeds_of.setdefault(k, []).append(i)
        # 每个种子的州（220 年前汉十三州，三国按魏蜀吴，晋按太康十九州）
        zkey = {}
        for i, s in enumerate(SEEDS):
            k = own[i]
            if not k or UNITS[UK[k]]["kind"] in ("tribe", "waste"): continue
            zh = zhou_of(s, y, k)
            if not zh: continue
            polk = r["pol"][k]
            if polk not in STATES: polk = "汉" if y < 220 else polk
            zkey[i] = (zh, polk)
        # 以“单位 × 州”为最小块拼一张覆盖图：单位界、政权界、州界都由同一批共享边合成，重合处严丝合缝
        pieces = {}
        for i, k in enumerate(own):
            if k: pieces.setdefault((k, zkey.get(i)), []).append(i)
        cov = tiled(pieces, C.SIMPLIFY)
        by_unit, by_zhou = {}, {}
        for (k, zk), g in cov.items():
            by_unit.setdefault(k, []).append(g)
            if zk: by_zhou.setdefault(zk, []).append(g)
        z, lz = {}, {}
        for k in seeds_of:
            g = T.merge_outline(by_unit.get(k, []))
            a = region(seeds_of[k])[1]
            if g is None or a is None: continue
            z[UK[k]] = T.rings_of(g); lz[UK[k]] = a
        members = {}
        for k, p in r["pol"].items(): members.setdefault(p, []).append(k)
        p_out, lp = {}, {}
        for p, ks in members.items():
            if len(ks) > 1 or ks[0] != p:
                g = T.merge_outline([x for k in ks for x in by_unit.get(k, [])])
                a = region([i for k in ks for i in seeds_of.get(k, [])])[1]
                if g is None or a is None: continue
                p_out[UK[p]] = T.rings_of(g); lp[UK[p]] = a
        zl, zpolys = [], []
        for zk in sorted(by_zhou):
            g = T.merge_outline(by_zhou[zk])
            if g is None: continue
            zpolys.append(g)
            a = region([i for i, v in zkey.items() if v == zk])[1]
            if a is not None and a[2] >= C.ZHOU_LABEL_MIN_AREA: zl.append([zk[0]] + a)
        zb = T.boundary_lines(zpolys)
        snaps.append(dict(y=y, era=nd["era"], era2=nd["era2"], t=nd["t"], d=nd["d"],
                          z=z, lz=lz, p=p_out, lp=lp,
                          own=[UK[x] if x else -1 for x in own],
                          pol={UK[k]: UK[p] for k, p in r["pol"].items()},
                          lab={UK[k]: v for k, v in r["lab"].items() if v != UNITS[UK[k]]["n"]},
                          seat={UK[k]: SI[v] for k, v in r["seat"].items()},
                          h=[UK[k] for k in r["pol"] if k in HATCH],
                          zb=zb, zl=zl))
        print(f"   {y:>4}  {len(z):>2} 单位  {len(p_out)} 政权", flush=True)
    unowned = [SEEDS[i]["id"] for i in range(len(SEEDS)) if not np.any(seedlab_land == i)]
    if unowned: print("   注意：这些种子没有分到任何格子：", "、".join(unowned))
    print(f"   疆域计算完成，{time.time() - t0:.1f}s")
    return snaps


# ================================================================ 条目
def build_items(base):
    TIT = {int(k): v for k, v in base["items"].items()}
    items = []
    def add(d):
        d["i"] = len(items); items.append(d); return d["i"]

    river_map = {}
    for i0 in sorted(TIT):
        it = TIT[i0]
        if it["c"] != "river": continue
        if it["old"] in I.DROP_LAKES: river_map[i0] = None; continue
        d = dict(c="river", sub=it["sub"], old=it["old"], mod=it["mod"], note="", major=it.get("major") or False)
        if it["old"] in I.RIVER_RENAME:
            o, m, n, mj = I.RIVER_RENAME[it["old"]]
            d.update(old=o, mod=m, note=n)
            if mj is not None: d["major"] = mj
        for k in ("anc", "lon", "lat", "rx", "ry"):
            if k in it: d[k] = it[k]
        river_map[i0] = add(d)
    for (o, m, lon, lat, rx, ry, n) in I.NEW_MARSHES:
        add(dict(c="river", sub="marsh", old=o, mod=m, note=n, major=False, lon=lon, lat=lat, rx=rx, ry=ry))
    new_river_lines = []
    JI = next(i for i in items if i.get("old") == "济水")["i"]
    for (o, m, line, k, anc, n) in I.NEW_RIVERS:
        if o == "济水（上游）":
            new_river_lines.append(dict(k=k, p=T.enc(line), it=JI)); continue
        idx = add(dict(c="river", sub="river", old=o, mod=m, note=n, major=False, anc=anc))
        new_river_lines.append(dict(k=k, p=T.enc(line), it=idx))

    canals_geo = []
    for (o, m, line, y0, anc, n) in I.CANALS:
        idx = add(dict(c="canal", old=o, mod=m, note=n, anc=anc, y0=y0))
        canals_geo.append(dict(p=T.enc(line), it=idx, y0=y0))
    for c in base["canals"]:
        old = TIT[c["it"]]["old"]
        if old in I.CANAL_KEEP:
            o, m, y0, n = I.CANAL_KEEP[old]
            idx = add(dict(c="canal", old=o, mod=m, note=n, anc=TIT[c["it"]]["anc"], y0=y0))
            canals_geo.append(dict(p=c["p"], it=idx, y0=y0))

    for i0 in sorted(TIT):
        it = TIT[i0]
        if it["c"] != "range": continue
        d = dict(c="range", old=it["old"], mod=it["mod"], note="", geo=it["geo"], anc=it["anc"], major=it.get("major") or False)
        if it["old"] in I.RANGE_RENAME:
            o, m, n, mj = I.RANGE_RENAME[it["old"]]
            d.update(old=o, mod=m, note=n, major=mj)
        add(d)
    for (o, m, geo, anc, mj, n) in I.NEW_RANGES:
        add(dict(c="range", old=o, mod=m, note=n, geo=geo, anc=anc, major=mj))

    DES = {"大流沙": ("流沙", "塔克拉玛干沙漠"), "大碛": ("大漠（瀚海）", "戈壁"), "普纳沙": ("毛乌素沙地", "毛乌素沙地")}
    desert_map = {}
    for i0 in sorted(TIT):
        it = TIT[i0]
        if it["c"] != "desert": continue
        o, m = DES.get(it["old"], (it["old"], it["mod"]))
        desert_map[i0] = add(dict(c="desert", old=o, mod=m, note="", anc=it["anc"]))

    for (o, m, geo, anc, n) in I.ROADS:
        add(dict(c="road", old=o, mod=m, note=n, geo=geo, anc=anc, major=True))
    for (o, m, lon, lat, st, yrs, at, n) in I.CAPITALS:
        add(dict(c="capital", old=o, mod=m, note=n, lon=lon, lat=lat, st=UK[st], yrs=yrs, at=SI[at]))
    for (o, m, lon, lat, y, yt, sides, cmd, n) in I.BATTLES:
        add(dict(c="battle", old=o, mod=m, note=n, lon=lon, lat=lat, y=y, yt=yt, sides=sides, cmd=cmd))
    for (o, m, lon, lat, n) in I.PASSES:
        add(dict(c="pass", old=o, mod=m, note=n, lon=lon, lat=lat))
    for (o, m, lon, lat, y, yt, n) in I.EVENTS:
        add(dict(c="event", old=o, mod=m, note=n, lon=lon, lat=lat, y=y, yt=yt))
    for (o, lon, lat, y0, y1, n) in I.PEOPLE:
        add(dict(c="people", old=o, mod="", note=n, lon=lon, lat=lat, y0=y0, y1=y1))

    rivers = []
    for r in base["rivers"]:
        it = r.get("it")
        if it is not None:
            if river_map.get(it) is None: continue
            r = dict(r, it=river_map[it])
        rivers.append(r)
    rivers += new_river_lines
    lakes = []
    for l in base["lakes"]:
        it = l.get("it")
        if it is not None and river_map.get(it) is None: continue
        c = Polygon(T.dec(l["r"])).centroid
        if any(abs(c.x - a) < 0.15 and abs(c.y - b) < 0.15 for a, b in I.DROP_LAKE_RINGS): continue
        if it is None and 108.6 < c.x < 109.1 and 40.8 < c.y < 41.1: continue   # 乌梁素海（近代形成）
        lakes.append(dict(l, it=river_map[it]) if it is not None else l)
    deserts = [dict(d, it=desert_map[d["it"]]) for d in base["deserts"]]
    return items, dict(rivers=rivers, lakes=lakes, canals=canals_geo, deserts=deserts)


# 郡国治所在地图上标城名，郡名放进提示框
CITY = {"河南尹": "洛阳", "京兆尹": "长安", "魏郡": "邺", "南阳郡": "宛", "南郡": "江陵", "蜀郡": "成都", "广汉郡": "雒", "巴郡": "江州",
        "东郡": "濮阳", "东海郡": "郯", "汉阳郡": "冀", "陇西郡": "狄道", "武都郡": "下辨", "武威郡": "姑臧", "太原郡": "晋阳", "涿郡": "涿",
        "广阳郡": "蓟", "辽东郡": "襄平", "齐国": "临淄", "山阳郡": "昌邑", "济阴郡": "定陶", "梁国": "睢阳", "陈国": "陈", "鲁国": "鲁",
        "安平国": "信都", "赵国": "邯郸", "勃海郡": "南皮", "南海郡": "番禺", "吴郡": "吴", "彭城国": "彭城", "下邳国": "下邳", "广陵郡": "广陵",
        "平原郡": "平原", "陈留郡": "陈留", "弘农郡": "弘农", "河内郡": "怀", "长沙郡": "临湘", "交趾郡": "龙编", "苍梧郡": "广信", "汉中郡": "南郑",
        "丹阳郡": "宛陵", "会稽郡": "山阴", "豫章郡": "南昌", "九江郡": "阴陵", "庐江郡": "舒", "颍川郡": "阳翟", "汝南郡": "平舆", "河东郡": "安邑"}

def build_seeds():
    out = []
    for s in SEEDS:
        d = dict(id=s["id"], n=s["n"], mod=s["mod"], lon=s["lon"], lat=s["lat"], t=s["t"])
        if s["id"] in CITY:
            d["n"] = CITY[s["id"]]; d["jn"] = s["n"]
            if s.get("nm"): d["jnm"] = s["nm"]
        elif s.get("nm"): d["nm"] = s["nm"]
        if s.get("note"): d["note"] = s["note"]
        out.append(d)
    return out


def dark(hx):
    r, g, b = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
    f = lambda v, k: max(0, min(255, int(round(v * k))))
    return "#%02X%02X%02X" % (f(r, 1.13), f(g, 1.11), f(b, 1.07))


def main():
    base = json.load(open(C.GEODATA / "base.json", encoding="utf8"))
    items, layers = build_items(base)
    snaps = compute_snaps(base)
    # 相邻节点里没变的疆域只存一份：z / p 的值和州界 zb 换成 pool 里的序号
    pool, where = [], {}
    def put(v):
        k = json.dumps(v, separators=(",", ":"))
        if k not in where: where[k] = len(pool); pool.append(v)
        return where[k]
    for sn in snaps:
        for key in ("z", "p"): sn[key] = {u: put(r) for u, r in sn[key].items()}
        sn["zb"] = put(sn["zb"])
    GEO = dict(land=base["land"], prov=base["prov"], border=base["border"], **layers,
               snaps=snaps, pool=pool, regions=[], ext=[72.0, 136.0, 15.5, 55.0], first=C.FIRST_YEAR)
    DATA = dict(units=[dict(k=u["k"], n=u["n"], kind=u["kind"], note=u["note"], **({"x": 1} if u.get("x") else {})) for u in UNITS],
                seeds=build_seeds(), items=items)
    colors = dict(light=[u["col"] for u in UNITS], dark=[dark(u["col"]) for u in UNITS])
    C.BUILD.mkdir(exist_ok=True)
    dump = lambda o, p: open(p, "w", encoding="utf8").write(json.dumps(o, ensure_ascii=False, separators=(",", ":")))
    dump(GEO, C.BUILD / "geo.json"); dump(DATA, C.BUILD / "data.json"); dump(colors, C.BUILD / "colors.json")
    print(f"   {len(snaps)} 个节点 · {len(items)} 条目 · {len(SEEDS)} 个郡国城邑点 · {len(UNITS)} 个政权诸侯部族")
    print("   " + " ".join(f"{k} {v}" for k, v in Counter(i['c'] for i in items).most_common()))


if __name__ == "__main__":
    main()
