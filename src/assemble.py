# -*- coding: utf-8 -*-
"""把 build/geo.json、build/data.json、content/en/ 的英文和每个单位的颜色注入 src/template.html，
生成一个不依赖任何外部文件的 docs/index.html。

  python src/assemble.py           严格：有缺译或过期的英文就报错退出
  python src/assemble.py --draft   草稿：缺译、过期处临时显示中文，只给警告
"""
import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C
import i18n


def check_english(geo, data, draft):
    missing, stale, unlocked = i18n.check(geo, data)
    bad = missing + stale
    if unlocked:
        print(f"   提醒：{len(unlocked)} 条英文未登记指纹（改完英文后运行 python tools/i18n.py lock）")
    if not bad:
        print("   英文：齐全")
        return
    msg = (f"英文缺译 {len(missing)} 条、过期 {len(stale)} 条："
           + "、".join(f"{f} {n}" for f, n in Counter(f for f, _, _ in bad).items())
           + "。运行 python tools/i18n.py todo 查看清单。")
    if not draft:
        sys.exit("   " + msg + "\n   如只想先看效果，用 python run.py --html --draft（缺译处显示中文）。")
    print("   草稿模式，" + msg)


def main():
    draft = "--draft" in sys.argv[1:]
    tpl = C.TEMPLATE.read_text(encoding="utf8")
    geo = json.loads((C.BUILD / "geo.json").read_text(encoding="utf8"))
    data = json.loads((C.BUILD / "data.json").read_text(encoding="utf8"))
    check_english(geo, data, draft)
    geo, data = i18n.attach(geo, data)
    colors = json.loads((C.BUILD / "colors.json").read_text(encoding="utf8"))
    light = " ".join(f"--u-{i}:{c};" for i, c in enumerate(colors["light"]))
    dark = " ".join(f"--u-{i}:{c};" for i, c in enumerate(colors["dark"]))
    for k in ("__GEO__", "__DATA__", "__UCSS_LIGHT__", "__UCSS_DARK__"):
        assert k in tpl, f"模板缺少占位符 {k}"
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = (tpl.replace("__UCSS_LIGHT__", light).replace("__UCSS_DARK__", dark)
               .replace("__DATA__", dump(data)).replace("__GEO__", dump(geo)))
    C.DOCS.mkdir(exist_ok=True)
    C.OUT_HTML.write_text(html, encoding="utf8")
    (C.DOCS / ".nojekyll").write_text("", encoding="utf8")
    print(f"   {C.OUT_HTML.relative_to(C.ROOT)}  {len(html.encode('utf8')) // 1024} KB")

if __name__ == "__main__":
    main()
