# -*- coding: utf-8 -*-
"""汉末三国形势图 · 全部路径与可调参数。"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
GEODATA = ROOT / "geodata"
BUILD = ROOT / "build"
DOCS = ROOT / "docs"
TEMPLATE = ROOT / "src" / "template.html"
OUT_HTML = DOCS / "index.html"

ETOPO_URL = "https://raw.githubusercontent.com/matplotlib/basemap/v1.4.0/examples/{name}.gz"
ETOPO_FALLBACK_URL = "https://raw.githubusercontent.com/matplotlib/basemap/develop/doc/examples/{name}.gz"
ETOPO_FILES = ("etopo20data", "etopo20lons", "etopo20lats")

# ---------------------------------------------------------------- 栅格
GRID_LON = (72.0, 136.0)      # 经度范围
GRID_LAT = (14.0, 55.0)       # 纬度范围
RES = 0.05                    # 格边长（°），约 5 km

# ---------------------------------------------------------------- 通行代价
# 每格基础代价 1（平地）。以下各项相加后再乘以噪声。
RELIEF_SCALE = 1300.0         # 地形起伏（米/度）每这么多加 1
RELIEF_MAX = 3.5              # 起伏代价上限
PLATEAU = (2700.0, 3700.0, 1.0)   # 海拔从 a 到 b 线性加到 c（高原腹地难以控制）
RANGE_WIDTH = 0.11            # 山脊阻隔带的高斯半宽（°）
RANGE_PEAK = {True: 7.0, False: 3.5}   # 主干 / 次要山脉的峰值代价
RIDGE_WAVES = (0.35, 0.9, 2.2)          # 山脊横向摆动的波长（°）
RIDGE_AMPS = (0.035, 0.06, 0.09)        # 对应振幅（°）
RIVER_WIDTH = 0.05            # 界河阻隔带半宽（°）
RIVER_PEAK = {"江（长江）": 3.5, "河（黄河）": 2.5, "淮水": 2.0, "沔水（汉水）": 1.2}
NOISE_SEED = 184              # 噪声随机种子（固定，保证每次构建一致）
NOISE_SIGMAS = (2.0, 6.0, 16.0)   # 三层平滑噪声的尺度（格）：细处让界线有小弯，粗处让走向不呆板
NOISE_AMP = 0.42              # 噪声幅度：代价 ×(1 ± AMP)
BIG_LAKE_AREA = 0.15          # 面积大于此值（平方度）的湖泊不可通行

# ---------------------------------------------------------------- 归属范围
# 每个种子最远能“够到”的代价距离 = 半径 × REACH_MULT。半径取 seeds.py 里的 R，缺省按类型。
REACH_DEFAULT = {"z": 2.6, "c": 1.6, "r": 2.2}
REACH_MULT = 1.45
FRONTIER_CLOSE = 0.7          # 外缘闭运算半径（°）：填平各点可达圆之间的凹口
FRONTIER_SMOOTH = 5.0         # 外缘高斯平滑（格）
MIN_WILD_CELLS = 600          # 无主地至少要连成这么多格（约 1.5 平方度），更小的空隙并入相邻疆域

# ---------------------------------------------------------------- 多边形
WARP = ((4.0, 0.9), (11.0, 1.6))   # 界线曲折：位移场的（尺度，幅度），单位：格
SEA_FILL_CELLS = 4            # 疆域向海面外延的格数（海岸线由前端按陆地剪裁）
SMOOTH_SIGMA = 1.25           # 边界平滑（高斯 σ，单位：格）
SIMPLIFY = 0.017              # 疆域覆盖简化容差（约为被删三角形面积的平方根，°）
MIN_PART_AREA = 0.012         # 小于此面积（平方度）的碎块丢弃
MIN_HOLE_AREA = 0.02          # 小于此面积的洞填平
ZHOU_LABEL_MIN_AREA = 1.2     # 州名只标在面积大于此值的州

FIRST_YEAR = 229              # 首屏节点
