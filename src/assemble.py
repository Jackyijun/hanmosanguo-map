# -*- coding: utf-8 -*-
"""把 build/ 里的数据注入 src/template.html，输出 docs/index.html。"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

def main():
    tpl = C.TEMPLATE.read_text(encoding="utf8")
    geo = (C.BUILD / "geo.json").read_text(encoding="utf8")
    data = (C.BUILD / "data.json").read_text(encoding="utf8")
    colors = json.loads((C.BUILD / "colors.json").read_text(encoding="utf8"))
    light = " ".join(f"--u-{i}:{c};" for i, c in enumerate(colors["light"]))
    dark = " ".join(f"--u-{i}:{c};" for i, c in enumerate(colors["dark"]))
    for k in ("__GEO__", "__DATA__", "__UCSS_LIGHT__", "__UCSS_DARK__"):
        assert k in tpl, f"模板缺少占位符 {k}"
    html = (tpl.replace("__UCSS_LIGHT__", light).replace("__UCSS_DARK__", dark)
               .replace("__DATA__", data).replace("__GEO__", geo))
    C.DOCS.mkdir(exist_ok=True)
    C.OUT_HTML.write_text(html, encoding="utf8")
    (C.DOCS / ".nojekyll").write_text("", encoding="utf8")
    print(f"   {C.OUT_HTML.relative_to(C.ROOT)}  {len(html.encode('utf8')) // 1024} KB")

if __name__ == "__main__":
    main()
