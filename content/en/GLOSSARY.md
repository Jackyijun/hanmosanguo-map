# 英文版译名与体例（GLOSSARY）

中文是源文本，英文按同一套键写在本目录的 `*.json` 里（结构见 `src/i18n.py` 开头）。本文件记录译名体例，新增或修改英文时照此执行；同一个名称在全图各处必须写法一致（地图注记、悬停说明、索引、对照表、年表、节点说明）。体例与本系列其他几幅图（宋辽夏金元等）一致，下面只列本图用到的部分和三国特有的写法。

## 一、总原则

1. **说真话**：英文只翻译中文已有的内容，不增不减；中文本身有误时先改中文，再改英文（并运行 `python tools/i18n.py lock`）。
2. **通俗写法，全图统一**：采用英文读者最常见的写法（Red Cliffs、Yellow Turbans、Kucha、Khotan），不用学术转写。
3. **地名用当时当地的名称**：中国及汉字文化圈的地名用汉语拼音转写中文古名；汉字圈以外的地名用当地当时名称的通行英文写法（龟兹 → Kucha，疏勒 → Kashgar，于阗 → Khotan，热海 → Issyk-Kul，阿耨达池 → Anavatapta）。
4. **今地/今名**用今天的通行英文名和行政区（Xuchang, Henan；Sariwon, North Hwanghae, North Korea）。行政区划变了中英文一起改（越南 2025 年 7 月并省：广南并入岘港，所以象林今地写“越南岘港会安一带 / Hội An area, Đà Nẵng, Vietnam”）。
5. **地图注记不加中文里没有的消歧义**：同音的不同地名照写，靠位置和悬停里的汉字区分（郁水、淯水都作 Yu River；伊水、易水、沂水都作 Yi River；凉州、梁州都作 Liang Province；夷洲、益州都作 Yizhou / Yi Province）。中文自带的区别字样照译（洛水（北）→ Northern Luo River）。“今地 / 今名”一栏是给英文读者定位用的，英文同名时可括注地区（Min River (Sichuan)），英文读者更熟悉另一通行名时可括注（Nu River (Salween)）。
6. **中文名自带括注的照译**：江（长江）→ Jiang (Yangtze)，河（黄河）→ He (Yellow River)，沔水（汉水）→ Mian River (Han River)，士燮（交州）→ Shi Xie (Jiao Province)。
7. **政权全称可括注英文通行的别称**（Sun Wu (Eastern Wu)、Linyi (Champa)），地图短名（s）不括注。
8. 英文界面里，地图注记只显示英文；悬停说明、索引、对照表、年表在英文名后附注汉字原名。
9. **按语末的“（今名）”**表示条目名称是今名、当时没有这个名称；英文一律放在按语最末，写作 “The name is modern.”。

## 二、拼音与通名

| 类别 | 写法 | 例 |
|---|---|---|
| 拼音 | 不标声调；音节界限有歧义时加撇号；ü 保留 | Chang'an、Jian'an、Lü Bu、Lüliang |
| 多音字 | 按古地名、人名的传统读音 | 冯翊 Pingyi、会稽 Kuaiji、犍为 Qianwei、越巂 Yuexi、朱提 Zhushi、阳翟 Yangzhai、枹罕 Fuhan、令支 Lingzhi、六安 Lu'an、曲阿 Qu'e、褒斜道 Baoye Road、琅邪 Langya、沙羡 Shayi、不其 Fuji、允吾 Yanya、叶县 She County、千乘 Qiansheng、濡水 Nuan River、㶟水 Lei River；姓氏“区”读 Ōu（区连 Ou Lian、区景 Ou Jing）；英文著作已有通行写法的从通行写法（曳咥河 Yexi River） |
| 州 | X Province | 冀州 Ji Province、荆州 Jing Province；司隶 Sili |
| 郡 | X Commandery | 南阳郡 Nanyang Commandery |
| 尹（京畿郡） | 照拼 Yin | 河南尹 Henan Yin、京兆尹 Jingzhao Yin |
| 三辅 | 照拼 | 左冯翊 Zuo Pingyi、右扶风 You Fufeng |
| 王国 / 国 | X Kingdom（与“王”译 King 一致） | 梁国 Liang Kingdom、琅邪国 Langya Kingdom |
| 属国 | X Dependent State | 辽东属国 Liaodong Dependent State |
| 县 | 两字县名直接拼；单字县名加 County | 陈仓 Chencang、郿县 Mei County、陕县 Shan County |
| 城（城名的一部分） | City | 它乾城 Tuoqian City、白帝城 Baidi City |
| 关 / 塞 / 坞 / 陉 / 津 | Pass / Fort / Fort / Defile / Ford；已成专名者照拼 | 潼关 Tong Pass、卢龙塞 Lulong Fort、濡须坞 Ruxu Fort、郿坞 Mei Fort、太行八陉 Eight Defiles of the Taihang、蒲阪津 Puban Ford、剑阁 Jiange、井陉 Jingxing |
| 道（栈道、驿道） | X Road | 子午道 Ziwu Road、金牛道 Jinniu Road |
| 渠 / 沟 / 渎 | X Canal；以“河”为名的运河作 X River | 白沟 Baigou Canal、破冈渎 Pogang Canal、蒗荡渠（鸿沟）Langdang Canal (Honggou Canal)、新河 Xin River |
| 水 / 河 / 江（单音节专名） | X River；英文惯用 -shui 的连写 | 汾水 Fen River、淮水 Huai River；湟水 Huangshui、弱水 Ruoshui、黑水 Heishui |
| 泽 / 陂 / 海（中国湖泽） | X Marsh / 照拼；英文已有定名的从定名 | 云梦泽 Yunmeng Marsh、芍陂 Quebei、白水陂 Baishuibei、西海（仙海）Xihai (Xianhai)、北海 Lake Baikal |
| 山 | 山脉 X Mountains；单峰 Mount X；英文惯称照用 | 太行山 Taihang Mountains、泰山 Mount Tai、祁山 Mount Qi、天山 Tian Shan |
| 蛮 / 夷 | tribes / peoples（不用 barbarian） | 武陵蛮 Wuling tribes、南中夷 Nanzhong peoples |
| 行在 | court in flight | 献帝行在 Emperor Xian's court in flight |

## 三、官爵与称号

| 中文 | 英文 | 说明 |
|---|---|---|
| 王（封王） | King of X | 魏王曹操 Cao Cao, King of Wei；汉中王 King of Hanzhong；吴王 King of Wu |
| 公 | Duke of X | 魏公 Duke of Wei |
| 称帝 | proclaims himself emperor | 孙权称帝 Sun Quan proclaims himself emperor |
| 受禅 / 代 | accepts the abdication / replaces | 曹丕受禅；晋代魏 Jin replaces Wei |
| 刺史 / 州牧 | Inspector / Governor | 交州刺史 Inspector of Jiao Province |
| 太守 | Administrator | 交趾太守 Administrator of Jiaozhi |
| 都护 | Protector-General；作为辖区时 Protectorate | 西域都护 Protectorate of the Western Regions |
| 屯田 | military farms | 许下屯田 Military farms at Xu；屯田兵 military-farm troops |
| 夷三族 | the three branches of the family wiped out | 不用 kin to the third degree |
| 受禅 | accepts the abdication；禅位于 X → abdicates in favour of X | |
| 牙门将 / 护军 / 阁尉 | Gate General / Army Protector / Gallery Commandant | |

## 四、人名、政权

- 汉人名：姓在前、拼音（Cao Cao、Liu Bei、Sun Quan、Zhuge Liang、Lü Bu）；复姓连写（Gongsun Zan、Sima Yi、Zhuge Ke、Guanqiu Jian、Xianyu Fu、Chunyu Qiong）。
- 两三人并称的“·”译作 “&”（李傕·郭汜 Li Jue & Guo Si），句中列举用 “and”。
- 政权：东汉 Eastern Han、曹魏 Cao Wei、蜀汉 Shu Han、孙吴 Sun Wu (Eastern Wu)（地图短名 Sun Wu）、西晋 Western Jin；节点里的当年称呼照中文（汉 Han、魏 Wei、吴 Wu、晋 Jin），年号前缀用 Wei: / Shu: / Wu:。地图上用短名（s），说明里用全称（n）。
- 北方、西方诸族照拼汉文史籍名：Xiongnu、Xianbei、Wuhuan、Qiang、Di、Shanyue；首领名照拼（Tanshihuai、Kebineng、Tadun、Tufa Shujineng）。
- 西域城邦用通行英文名：Kucha、Kashgar、Khotan、Yarkand、Karasahr、Shanshan、Loulan、Further Jushi。
- 朝鲜半岛用新罗马字（Goguryeo、Buyeo、Mahan、Jinhan、Byeonhan、Okjeo、Hwando、黄山江 Hwangsan River；高句丽王位宫 Wigung）；日本古称 Wa；越南今地保留声调符号（Bắc Ninh、Thanh Hóa、Quảng Trị、Hội An、Đà Nẵng）；林邑 Linyi (Champa)。
- 书名：《三国志·东夷传》Account of the Eastern Peoples in the Records of the Three Kingdoms；《三国演义》the Romance。
- 淮南三叛 the Three Rebellions in Huainan（专名，大写）；关东联军 the coalition east of the passes；黑山 Black Mountain (army)。
- 战役中的部众、联军照中文：青州黄巾 the Qing Province Yellow Turbans、关中诸将 the Guanzhong generals。
- 胜负句里，部族名前加 the（the Xianbei、the Northern Xiongnu、the Wuhuan），政权名不加（Han、Jin、Cao Wei）。

## 五、年代

- 中文写农历月份，英文照写农历月序，不换算公历：
  - 200 年八月 → 8th month, 200；闰六月 → intercalary 6th month；正月 → 1st month
  - 春、夏、秋、冬 → spring / summer / autumn / winter 208
  - 跨年区间：12th month, 208 – 12th month, 209；同年内：8th–10th month, 200
- 年号：Jian'an 13（年号拼音 + 序数，不写 “13th year of”）；三国并立时另两方的年号写作 “Shu: Zhangwu 2 · Wu: Huangwu 1”。
- 约 → c.；年份区间用 en dash：175–183；“一说”→ (or …)：239 (or 238)；今地里的“一说”同样作 (or …)。
- 今地的“一带”作 “X area”；两地之间的路线用前后带空格的 en dash：Mei County – Baocheng, Hanzhong, Shaanxi。

## 六、战役

- 名称：Battle of X / Siege of X / X Campaign，英文已有通行名称的用通行名称（Battle of Red Cliffs、Battle of Guandu、Battle of Wuzhang Plains、Crossing the River in White）。
- 同地多次战役，中文以年份括注区别的，英文同样以年份括注（Battle of Jiangling (208) / (222) / (250) / (280)）；中文未括注而英文与另一战同名的，也补年份（宛城之战 Battle of Wancheng (197)、皖城之战 Battle of Wancheng (199)、皖城之战（214）Battle of Wancheng (214)）。这是第一节第 5 条的唯一例外。
- 交战结果：“A defeated B”；相持不下作 “Stalemate; X withdrew”；中文另有说明时照译（Minor Shu Han success; withdrew when supplies ran out）。
- 主将：“A and B vs. C”。
- 地望有争议的今地括注 “(location disputed)”。

## 七、维护

- `python tools/i18n.py status`：缺译、过期、未登记指纹的条数。
- `python tools/i18n.py todo [文件]`：逐条列出缺译与过期的中文。
- 改完英文：`python tools/i18n.py lock` 记下中文指纹；以后中文一改，对应英文就会报“过期”。
- `python run.py --html` 默认严格：有缺译或过期就停下；`--draft` 允许先出草稿（缺译处显示中文）。
- `python tools/i18n.py table` 导出中英对照表 `build/i18n-review.tsv` 供审校。
