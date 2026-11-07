# -*- coding: utf-8 -*-
"""汉末三国形势图 · 一键构建。

  python run.py               底图缺失则下载 → 计算疆域 → 生成 docs/index.html
  python run.py --html        只重新拼装 HTML（只改了 src/template.html 时用，不到 1 秒）
  python run.py --draft       英文有缺译或过期时也照常生成（缺译处临时显示中文），只给警告
  python run.py --open        构建完成后用浏览器打开
  python run.py --preview 190,229
                              构建后画出这几个节点的疆域草图（build/preview.png）
"""
import argparse, subprocess, sys, time, webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

def step(title, script, args=()):
    print(f"\n== {title} ==")
    t0 = time.time()
    r = subprocess.run([sys.executable, str(script), *args], cwd=ROOT)
    if r.returncode != 0:
        sys.exit(f"失败：{title}")
    print(f"   用时 {time.time() - t0:.1f}s")

def main():
    ap = argparse.ArgumentParser(description="构建汉末三国形势图")
    ap.add_argument("--html", action="store_true", help="跳过疆域计算，只重新拼装 HTML")
    ap.add_argument("--draft", action="store_true", help="英文缺译或过期时不停下，缺译处显示中文")
    ap.add_argument("--open", action="store_true", help="完成后在浏览器中打开")
    ap.add_argument("--preview", metavar="YEARS", help="逗号分隔的年份，画疆域草图")
    a = ap.parse_args()
    if not a.html:
        step("检查底图", SRC / "fetch_data.py")
        step("计算疆域（约 30 秒）", SRC / "build.py")
    step("拼装 HTML（并入英文）", SRC / "assemble.py", ["--draft"] if a.draft else [])
    if a.preview:
        step("画草图", ROOT / "tools" / "preview.py", [a.preview])
    out = ROOT / "docs" / "index.html"
    print(f"\n完成：{out}")
    if a.open:
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
