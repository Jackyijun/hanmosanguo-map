# Late Han and the Three Kingdoms

[![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-red.svg)](README.md) [![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)

An interactive, bilingual (Chinese / English) historical map from the Yellow Turban Uprising to the reunification under Jin (184–280), with the Eastern Han at its height in Yongyuan 6 (94) as a prologue. It covers the territories of warlords and states at 36 snapshots, historical and modern names for 207 commanderies, kingdoms and towns, 117 battles, 50 events, 27 passes and 12 capitals and temporary courts, plus three layers specific to the period: provincial boundaries, the Shu roads and plank roads, and the canals of Cao Wei and Sun Wu.

---

## 1. Just open it

Double-click **`docs/index.html`** and open it in any modern browser (Chrome, Edge, Safari, Firefox).

The file is about 1.7 MB with all data, styles and scripts inlined: no network, no server, no external libraries.

- Language: switch with "中 | EN" at the top right of the map (at the top right of the content area in the Timeline and Gazetteer views); the choice is remembered in the browser. Add `#en` to the end of the URL to open the English version directly. In English the map shows English labels only; tooltips, the index, the timeline and the gazetteer give the Chinese original after each English name. Search works in both languages, and English searches ignore diacritics.

---

## 2. Online

https://jackyijun.github.io/hanmosanguo-map/

---

## 3. Building locally

You only need to rebuild after changing the historical content (`content/`) or the parameters (`src/config.py`). Requires **Python 3.9 or later**.

**macOS / Linux**

```bash
cd hanmosanguo-map
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py --open
```

**Windows (PowerShell)**

```powershell
cd hanmosanguo-map
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py --open
```

A full build takes about 30 seconds and then opens the new `docs/index.html` in your browser.

| Command | What it does |
|---|---|
| `python run.py` | Check base map → compute territories → assemble HTML |
| `python run.py --html` | Reassemble the HTML only (when only `src/template.html` changed; under a second) |
| `python run.py --open` | Open in the browser when the build finishes |
| `python run.py --html --draft` | Build even if English translations are missing or stale (missing ones temporarily show the Chinese); without `--draft` the build stops with an error |
| `python tools/i18n.py status` | English status: how many entries are missing, stale or not yet fingerprinted (see section 7) |
| `python run.py --preview 190,229` | Also draw territory sketches for these snapshots to `build/preview.png`, to check that no assignment is wrong |
| `python tools/preview.py 190 108,123,29,42` | Draw a sketch only, optionally for a given extent (west,east,south,north) |

The base map (`geodata/`, about 2 MB) ships with the project, so it builds offline. If the ETOPO20 terrain file has been deleted, `run.py` downloads a pinned version from GitHub.

The same input always produces a byte-identical build, so changes can be tracked in git.

After building, commit `docs/index.html` with your changes and push to `main`; the online page updates automatically.

---

## 4. Layout

```
hanmosanguo-map/
├── run.py                 one-step build
├── requirements.txt
├── README.md              documentation (Chinese)
├── README.en.md           documentation (English)
├── docs/
│   ├── index.html         ★ the finished map, a single file (published by GitHub Pages)
│   └── .nojekyll          makes GitHub Pages publish files as they are
├── content/               ★ historical content (hand-written; most edits go here)
│   ├── seeds.py           320 assignment points: Eastern Han commandery and kingdom seats, towns, helper points used only for partitioning, tribal points
│   ├── units.py           53 states, warlords, tribes and abandoned lands: names, colours, descriptions
│   ├── nodes.py           36 snapshots: reign era, title, summary, and which commanderies changed hands that year
│   ├── items.py           capitals, battles, passes, events, peoples, historical names of mountains and rivers, canals, ancient and plank roads
│   └── en/                ★ English version: translations matching the files above (JSON), zh.lock.json Chinese fingerprints, GLOSSARY.md naming conventions
├── src/
│   ├── config.py          ★ all paths and tunable parameters (grid, costs, smoothing…)
│   ├── fetch_data.py      checks the base map; downloads ETOPO20 if missing
│   ├── terrain.py         territory algorithm: cost raster, multi-source shortest paths, smoothing, coverage assembly
│   ├── build.py           computes assignments and territories per snapshot; writes build/geo.json, data.json, colors.json
│   ├── assemble.py        merges the English, checks for missing translations, injects the data into the template, writes docs/index.html
│   ├── i18n.py            English version: lists what needs translating, checks for missing and stale translations, merges them into the data
│   └── template.html      front end: page structure, styles, interaction scripts
├── geodata/
│   ├── base.json          base map: land, lakes, rivers, modern provincial and national borders, deserts, mountain ridgelines (encoded)
│   └── etopo20/           ETOPO20 terrain (1/3° resolution), used for relief
├── tools/
│   ├── preview.py         matplotlib territory sketches
│   └── i18n.py            English maintenance: status / todo / lock / table
└── build/                 intermediate files (safe to delete)
```

---

## 5. How it works

```
content/*.py ─────┐
geodata/ (base) ──┼─► build.py + terrain.py ─► build/*.json ─► assemble.py ─► docs/index.html
                  │                                               ▲
                  └───────────────────────────── src/template.html┘
```

### 1. Why the territories are computed

There is no ready-made boundary data for the late Han warlords. What the histories can establish is mostly "commandery X belonged to Y in year Z", and Han commandery boundaries largely followed mountains and rivers. So the approach is:

1. Hand-write only the assignments **commandery (town) → warlord → state** and the years they changed (`nodes.py`);
2. Let the computer infer the boundaries between commanderies from a "travel cost" map, so that they fall on ridges and major rivers wherever possible.

### 2. The territory algorithm (`terrain.py`)

1. **Land–sea grid**: longitude 72°–136°, latitude 14°–55°, 0.05° per cell (about 5 km), 1280 × 820 cells. Large lakes are impassable.
2. **Cost raster**: flat land costs 1, plus, in turn:
   - **relief** from ETOPO20 (+1 per 1300 m per degree, at most +3.5), and up to +1 more between 2700 and 3700 m elevation (the plateau interior is hard to hold);
   - **mountain ridgelines** from `base.json`, each burned in as a Gaussian band of high cost, peaking at +7 for major ranges and +3.5 for minor ones. The hand-drawn ridgelines are a few straight segments, so they first get a little sideways wobble from a fixed seed;
   - **border rivers**: Yangtze +3.5, Yellow River +2.5, Huai +2, Han +1.2;
   - finally multiplied by three-scale smooth noise (±42%) so that boundaries bend naturally.
3. **Multi-source shortest paths**: with all 320 points as sources, one run of `scipy.sparse.csgraph.dijkstra(min_only=True)` on a 16-neighbour grid graph assigns each cell to the point with the smallest cost distance. This is a **weighted Voronoi** diagram: boundaries are drawn onto ridges and rivers. The 16-neighbour stencil (including "knight's moves") is closer to isotropic than 8 neighbours, so boundaries on plains do not follow the grid axes.
4. **Unclaimed land and outer edges**: cells beyond a point's reach (`R` in `seeds.py` × 1.45) are unclaimed (the far side of the Gobi, the heart of the Tibetan Plateau). Each point's reach is an iso-cost line, so the outer edge would be a string of arcs; a morphological closing (radius 0.7°) fills the notches and Gaussian smoothing shaves off small bumps. Small gaps enclosed by territories are merged into a neighbour.
5. **Wiggly boundaries**: on a plain the boundary between two points is a straight perpendicular bisector, so the whole assignment grid is shifted by a smooth displacement field that gives every boundary small river-like bends. Within about 0.3° of the Yangtze, Yellow River, Huai and Han the displacement tapers to zero, so boundaries along border rivers stay on the river and riverside towns (such as Jingkou) are not pushed to the other bank.
6. **Polygons per snapshot**: for each snapshot, cells are merged by "point → warlord × province", Gaussian-smoothed (σ = 1.25 cells) and traced with marching squares at the 0.5 level. The contours of adjacent blocks already coincide except for small gaps at three-way junctions; all contours are split into faces, each face is assigned to its block (faces in the gaps go by the raster assignment), and the whole set is simplified together with GEOS **coverage simplify**. Warlord, state and provincial boundaries are all built from this one set of shared edges, so two neighbours always share exactly the same line, with no gaps or overlaps.
7. **Label points**: each warlord, state and province is labelled at the "pole of inaccessibility" (the maximum of the distance transform) of its largest land piece.
8. **Deduplication**: territory that does not change between adjacent snapshots is stored once (`GEO.pool`), roughly halving the file size.

### 3. Front end (`src/template.html`)

The skeleton, palette, symbols and interactions all follow the unified specification for the historical maps, shared with the Tang–Song, Warring States and Sui–Tang maps:

- No dependencies: plain JavaScript + SVG, Albers equal-area conic projection (standard parallels 25°N and 47°N, centred on 108°E, 34°N).
- Colouring switches between "Warlords" (actual control) and "States" (nominal allegiance); the Gongsun clan, Shi Xie, Zhang Lu and Black Mountain are hatched to show nominal submission but de facto independence.
- Abandoned lands (the northern frontier commanderies settled by Qiang and Hu, and the land between the Yangtze and Huai after Cao Cao moved its people north in 213) are drawn like tribes, with pale fill and a dashed outline, and do not count as states.
- Period-specific layers: provincial boundaries (the thirteen Eastern Han provinces before 220, each state's own provinces in the Three Kingdoms, the nineteen provinces of Jin's Taikang era), ancient and plank roads (the eight Shu roads and the Lulong Road), and canals (appearing from the year they were dug).
- Language: every piece of text is taken in the current language (through a few accessors such as `LZ(zh, en)` and `iF(item, field)`); switching redraws the map, index, timeline and gazetteer. English labels are measured on a canvas for collision avoidance, and long names that do not fit inside a territory wrap onto two lines.
- The template has 4 placeholders: `__GEO__`, `__DATA__`, `__UCSS_LIGHT__`, `__UCSS_DARK__`, replaced by `assemble.py`. `assemble.py` first uses `src/i18n.py` to check that the English is complete and up to date (stopping with an error if not, unless `--draft`), then merges the English into the data (units `ne`/`se`/`notee`, commanderies and towns `ne`/`nme`/`jne`/`mode`/`notee`, items `e`, snapshots `erae`/`era2e`/`te`/`de`/`labe`, province names `GEO.zhoue`), and finally replaces the placeholders.

---

## 6. Common changes

**Change who held a commandery in a given year**: add an entry to the `ops` of that snapshot in `content/nodes.py`. Each snapshot inherits every assignment from the previous one; write only what changes:

```python
("J", "南郡", "孙")        # a whole commandery (with its towns)
("C", "柳城", "曹")        # a single town or helper point
("Z", "冀州", "曹")        # a whole province
("G", "乌桓", "鲜卑")      # a tribal group
("ID", "黑山", "黑山")     # every point whose ID starts with this prefix
("REPL", "孙", "晋")       # replace one unit with another everywhere
```

**Add a town**: add a line `C("name", "commandery", lon, lat, "modern location", "note")` to `content/seeds.py`. It follows its commandery automatically; write it into `nodes.py` only if it changes hands separately.

**Add a battle**: add a line to `BATTLES` in `content/items.py` (name, modern location, longitude and latitude, year, displayed date, outcome, commanders, note).

After a change, run `python run.py --preview <year>` to look at the sketch, then check the page.

**Whenever you add or change any Chinese** (points, items, units, snapshot summaries…): add or update the English in `content/en/` too, or the strict build reports it as missing or stale; see section 7.

---

## 7. English version

Chinese is the source text. The English is written in `content/en/` under the same keys:

| File | Contents | Key |
|---|---|---|
| `units.json` | states, warlords, tribes: full name `n`, short map name `s` (optional), description `note` | unit key (e.g. `曹`) |
| `labels.json` | what a unit is called at a given snapshot (e.g. "魏王曹操") | the Chinese name |
| `seeds.json` | commanderies and towns: modern location `mod`, note `note`, names by period `n`, name of the commandery it was the seat of `jn` | point ID |
| `items.json` | items: `old` `mod` `note` `yt` `sides` `cmd` | `category:name` (e.g. `battle:官渡之战`); duplicates get `#2`, `#3` |
| `snaps.json` | snapshots: reign era `era`, Shu and Wu eras `era2`, title `t`, summary `d` | year |
| `misc.json` | modern province names `prov`, Han–Jin province names `zhou` | the Chinese name |

`zh.lock.json` records a fingerprint (first 10 characters of the sha1) of the Chinese each English entry was written from. If the Chinese changes and the English does not, the build reports it as "stale". Naming and style conventions are in `content/en/GLOSSARY.md` (pinyin, foreign place names, lunar months, how battle outcomes are written, and so on).

**After changing the Chinese**:

1. `python tools/i18n.py status` shows how many entries are missing or stale;
2. `python tools/i18n.py todo` lists their Chinese; add or update the English in the matching JSON;
3. `python tools/i18n.py lock` records the new Chinese fingerprints;
4. `python run.py --html` reassembles (strict mode: missing translations are an error).

`python tools/i18n.py table` exports every Chinese–English pair to `build/i18n-review.tsv` for review.

---

## 8. Tuning

All tunable parameters are in `src/config.py`:

| Parameter | What it does |
|---|---|
| `RES` | Grid cell size. Smaller is finer but slower |
| `RELIEF_SCALE` · `PLATEAU` | Cost of relief and of plateau elevation |
| `RANGE_PEAK` · `RANGE_WIDTH` · `RIDGE_*` | Strength, width and wobble of ridge barriers |
| `RIVER_PEAK` | Cost of border rivers |
| `NOISE_*` · `WARP` · `WARP_RIVER_HOLD` | Noise and displacement field that bend the boundaries; the band along border rivers left undisplaced |
| `REACH_*` · `FRONTIER_*` · `MIN_WILD_CELLS` | Extent of unclaimed land and smoothing of outer edges |
| `SMOOTH_SIGMA` · `SIMPLIFY` | Outline smoothing and simplification tolerance |
| `FIRST_YEAR` | Snapshot shown on first load |

---

## 9. Sources and reliability

- **Territorial assignments**: inferred from the *Book of the Later Han*, the *Records of the Three Kingdoms*, the *Zizhi Tongjian*, the *Book of Jin* and the general picture in volumes 2 and 3 of Tan Qixiang's *Historical Atlas of China*; written with AI assistance and not checked line by line against the original texts. The overall picture and the key years are fairly reliable; the exact holder of a given commandery in a given year, and the extent of the fringes (the Western Regions, north of the Gobi, Nanzhong, east of Liaodong), are rough.
- **Boundary lines**: entirely computed schematic lines. They only mean "this area belonged to this side", not that the histories record such a line.
- **Romance and history**: fictional episodes from the *Romance of the Three Kingdoms* (Guan Yu slaying Hua Xiong over warm wine, the three heroes fighting Lü Bu, the five passes, the Empty Fort Strategy, Guan Yu releasing Cao Cao at Huarong, etc.) are not listed as battles; where relevant, the notes on the related items point out the difference.
- **Base map**: land, lakes, rivers and modern national borders from Natural Earth 1:10m (public domain); modern provincial borders and mountain ridgelines are hand-drawn simplifications carried over from the Tang–Song map; terrain from NOAA ETOPO20 (as distributed in the matplotlib/basemap repository).
- **English version**: translated from the Chinese; naming conventions in `content/en/GLOSSARY.md`. Months are lunar months in order, not converted to the Western calendar.
