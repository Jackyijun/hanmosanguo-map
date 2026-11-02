# -*- coding: utf-8 -*-
"""用 matplotlib 快速画出若干时间节点的疆域，检查归属有没有填错。

  python tools/preview.py 196,229                       汉地范围
  python tools/preview.py 190 108,123,29,42             指定经纬范围：西,东,南,北
  python tools/preview.py 190 108,123,29,42 out.png     指定输出文件（默认 build/preview.png）
粗黑线是多单位政权的外轮廓，点线是州界。
"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
for f in ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc", "C:/Windows/Fonts/msyh.ttc",
          "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]:
    if Path(f).exists():
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name(); break

def dec(f):
    out = []; x = y = 0
    for i in range(0, len(f), 2):
        x += f[i]; y += f[i + 1]; out.append((x / 100, y / 100))
    return out

def main():
    years = [int(y) for y in sys.argv[1].split(",")]
    ext = [float(v) for v in sys.argv[2].split(",")] if len(sys.argv) > 2 else [96, 128, 17, 44]
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "build" / "preview.png"
    geo = json.loads((ROOT / "build" / "geo.json").read_text(encoding="utf8"))
    data = json.loads((ROOT / "build" / "data.json").read_text(encoding="utf8"))
    cols = json.loads((ROOT / "build" / "colors.json").read_text(encoding="utf8"))["light"]
    units = data["units"]
    n = len(years); nc = min(n, 2); nr = (n + nc - 1) // nc
    fig, axs = plt.subplots(nr, nc, figsize=(10 * nc, 8 * nr), squeeze=False)
    for ax, y in zip(axs.ravel(), years):
        sn = next(s for s in geo["snaps"] if s["y"] == y)
        res = lambda v: geo["pool"][v] if isinstance(v, int) else v
        sn = dict(sn, z={u: res(v) for u, v in sn["z"].items()}, p={u: res(v) for u, v in sn["p"].items()}, zb=res(sn["zb"]))
        for poly in geo["land"]:
            for r in poly[:1]: ax.add_patch(MP(dec(r), closed=True, fc="#ECEBE3", ec="#999", lw=.3))
        for u, rings in sn["z"].items():
            u = int(u); tribe = units[u]["kind"] == "tribe"
            for r in rings:
                ax.add_patch(MP(dec(r), closed=True, fc=cols[u], alpha=.35 if tribe else .62, ec="#333", lw=.4, ls="--" if tribe else "-"))
        for p, rings in sn["p"].items():
            for r in rings: ax.add_patch(MP(dec(r), closed=True, fill=False, ec="k", lw=1.3))
        for l in sn.get("zb", []):
            pts = dec(l); ax.plot([a for a, b in pts], [b for a, b in pts], ":", color="#444", lw=.8)
        for u, L in sn["lz"].items():
            u = int(u)
            if ext[0] < L[0] < ext[1] and ext[2] < L[1] < ext[3]:
                ax.text(L[0], L[1], sn["lab"].get(str(u)) or units[u]["n"], fontsize=9, ha="center", va="center", weight="bold")
        for z in sn.get("zl", []):
            if ext[0] < z[1] < ext[1] and ext[2] < z[2] < ext[3]:
                ax.text(z[1], z[2] - .45, z[0], fontsize=7, ha="center", color="#555")
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect(1 / .83)
        ax.set_title(f"{y} {sn['t']}")
    for ax in axs.ravel()[n:]: ax.axis("off")
    plt.tight_layout(); out.parent.mkdir(exist_ok=True); plt.savefig(out, dpi=72)
    print(f"   {out}")

if __name__ == "__main__":
    main()
