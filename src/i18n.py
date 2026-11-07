# -*- coding: utf-8 -*-
"""英文版：把 content/en/ 下的译文并入构建结果，并检查缺译与过期。

中文是源文本。每一条要显示的中文都有一个“键/字段”，英文按同样的键写在 content/en/*.json 里：

  units.json    政权、诸侯、部族          {"曹": {"n": 全称, "s": 地图短名（可省）, "note": 说明}}
  labels.json   节点里的当年别名          {"仲（袁术）": "Zhong (Yuan Shu)"}
  seeds.json    郡国城邑（键为点的 ID）    {"南阳郡": {"mod": 今地, "note": 按语, "n": {各时期名称: …}, "jn": {所治郡名: …}}}
  items.json    条目（键为 类别:古名）     {"battle:官渡之战": {"old", "mod", "note", "yt", "sides", "cmd"}}；同名的加 #2、#3
  snaps.json    时间节点（键为年份）       {"200": {"era": 年号, "era2": 另一方年号, "t": 标题, "d": 概述}}
  misc.json     今省名、州名              {"prov": {"河南": …}, "zhou": {"豫州": …}}

zh.lock.json 记着每条英文写成时所据中文的指纹（sha1 前 10 位）。中文改了而英文没改，就是“过期”。
改完英文后运行 `python tools/i18n.py lock` 更新指纹。
"""
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "content" / "en"
FILES = ["units", "labels", "seeds", "items", "snaps", "misc"]
LOCK = EN / "zh.lock.json"
ITEM_FIELDS = ("old", "mod", "note", "yt", "sides", "cmd", "tag")
SNAP_FIELDS = ("era", "era2", "t", "d")


def fp(zh):
    return hashlib.sha1(zh.encode("utf8")).hexdigest()[:10]


def load_en():
    out = {}
    for f in FILES:
        p = EN / f"{f}.json"
        out[f] = json.load(open(p, encoding="utf8")) if p.exists() else {}
    return out


def load_lock():
    return json.load(open(LOCK, encoding="utf8")) if LOCK.exists() else {}


def item_keys(data):
    """条目键：类别:古名；同类同名的条目（如三个政权的都城洛阳）依次加 #2、#3。"""
    seen, out = {}, []
    for it in data["items"]:
        k = f"{it['c']}:{it['old']}"
        seen[k] = seen.get(k, 0) + 1
        out.append(k if seen[k] == 1 else f"{k}#{seen[k]}")
    return out


def seed_names(s):
    return list(dict.fromkeys([s["n"]] + [n for _, n in (s.get("nm") or [])]))


def seed_jnames(s):
    if not s.get("jn"): return []
    return list(dict.fromkeys([s["jn"]] + [n for _, n in (s.get("jnm") or [])]))


def zhou_names(geo):
    return sorted({z[0] for s in geo["snaps"] for z in (s.get("zl") or [])})


def required(geo, data):
    """列出全部需要英文的 (文件, 路径, 中文)。路径是键名组成的元组。"""
    req = []
    for u in data["units"]:
        req.append(("units", (u["k"], "n"), u["n"]))
        if u.get("note"): req.append(("units", (u["k"], "note"), u["note"]))
    labs = sorted({v for s in geo["snaps"] for v in s["lab"].values()})
    for v in labs: req.append(("labels", (v,), v))
    for s in data["seeds"]:
        if s["t"] == "r": continue
        if s.get("mod"): req.append(("seeds", (s["id"], "mod"), s["mod"]))
        if s.get("note"): req.append(("seeds", (s["id"], "note"), s["note"]))
        for n in seed_names(s): req.append(("seeds", (s["id"], "n", n), n))
        for n in seed_jnames(s): req.append(("seeds", (s["id"], "jn", n), n))
    for it, k in zip(data["items"], item_keys(data)):
        for f in ITEM_FIELDS:
            if it.get(f): req.append(("items", (k, f), it[f]))
    for s in geo["snaps"]:
        y = str(s["y"])
        for f in SNAP_FIELDS:
            if s.get(f): req.append(("snaps", (y, f), s[f]))
    for p in geo.get("prov", []): req.append(("misc", ("prov", p["n"]), p["n"]))
    for z in zhou_names(geo): req.append(("misc", ("zhou", z), z))
    return req


def get(en, f, path):
    v = en.get(f, {})
    for k in path:
        if not isinstance(v, dict) or k not in v: return None
        v = v[k]
    return v if isinstance(v, str) and v.strip() else None


def lock_key(f, path):
    return f + "/" + "/".join(path)


def check(geo, data, en=None, lock=None):
    en = en if en is not None else load_en()
    lock = lock if lock is not None else load_lock()
    missing, stale, unlocked = [], [], []
    for f, path, zh in required(geo, data):
        if get(en, f, path) is None: missing.append((f, path, zh)); continue
        lk = lock.get(lock_key(f, path))
        if lk is None: unlocked.append((f, path, zh))
        elif lk != fp(zh): stale.append((f, path, zh))
    return missing, stale, unlocked


def attach(geo, data, en=None):
    """把英文写进 geo/data（缺译时退回中文），返回 (geo, data)。"""
    en = en if en is not None else load_en()
    g = lambda f, *path: get(en, f, path)
    for u in data["units"]:
        u["ne"] = g("units", u["k"], "n") or u["n"]
        s = g("units", u["k"], "s")
        if s: u["se"] = s
        u["notee"] = g("units", u["k"], "note") or u.get("note", "")
    for s in data["seeds"]:
        if s["t"] == "r": continue
        s["ne"] = g("seeds", s["id"], "n", s["n"]) or s["n"]
        if s.get("nm"): s["nme"] = [g("seeds", s["id"], "n", n) or n for _, n in s["nm"]]
        if s.get("jn"):
            s["jne"] = g("seeds", s["id"], "jn", s["jn"]) or s["jn"]
            if s.get("jnm"): s["jnme"] = [g("seeds", s["id"], "jn", n) or n for _, n in s["jnm"]]
        s["mode"] = g("seeds", s["id"], "mod") or s.get("mod", "")
        if s.get("note"): s["notee"] = g("seeds", s["id"], "note") or s["note"]
    for it, k in zip(data["items"], item_keys(data)):
        it["e"] = {f: (g("items", k, f) or it[f]) for f in ITEM_FIELDS if it.get(f)}
    for s in geo["snaps"]:
        y = str(s["y"])
        s["erae"] = g("snaps", y, "era") or s.get("era", "")
        if s.get("era2"): s["era2e"] = g("snaps", y, "era2") or s["era2"]
        s["te"] = g("snaps", y, "t") or s["t"]
        s["de"] = g("snaps", y, "d") or s.get("d", "")
        s["labe"] = {u: (g("labels", v) or v) for u, v in s["lab"].items()}
    for p in geo.get("prov", []): p["ne"] = g("misc", "prov", p["n"]) or p["n"]
    geo["zhoue"] = {z: (g("misc", "zhou", z) or z) for z in zhou_names(geo)}
    return geo, data
