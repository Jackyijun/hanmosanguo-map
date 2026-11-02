# -*- coding: utf-8 -*-
"""下载 ETOPO20 地形数据（已有则跳过）。仓库里已附带，正常情况下不会触发下载。"""
import sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

def main():
    d = C.GEODATA / "etopo20"
    d.mkdir(parents=True, exist_ok=True)
    for name in C.ETOPO_FILES:
        p = d / f"{name}.gz"
        if p.exists() and p.stat().st_size > 0:
            continue
        for url in (C.ETOPO_URL, C.ETOPO_FALLBACK_URL):
            try:
                print(f"   下载 {url.format(name=name)}")
                urllib.request.urlretrieve(url.format(name=name), p)
                break
            except Exception as e:
                print(f"   失败：{e}")
        else:
            sys.exit(f"无法下载 {name}，请手动放到 {p}")
    if not (C.GEODATA / "base.json").exists():
        sys.exit("缺少 geodata/base.json（底图），请从仓库重新获取")
    print("   底图齐全")

if __name__ == "__main__":
    main()
