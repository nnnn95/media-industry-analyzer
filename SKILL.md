---
name: media-industry-analyzer
description: 传媒行业研究 skill。当用户要求"传媒行业分析 / 传媒研报 / 传媒个股打分 / 传媒投资逻辑 / 中信传媒 / 分析传媒板块"等请求时触发。覆盖中信一级行业·传媒下 7 个二级行业，产出行业研究报告 + 个股深度分析 + 个股打分矩阵。关键词：传媒、行业研究、中信行业、二级行业、投资逻辑、个股打分、分众传媒、AI传媒、版号、数据要素。
version: 1.0.0
author: media-industry-analyzer
license: MIT
metadata:
  tags: [finance, media, citic-industry, a-share, ai-media, scoring, research-report]
  related_skills: [stock-deep-analyzer]
---

# Media Industry Analyzer · 传媒行业研究 Skill

> 你正在扮演一位**传媒行业首席分析师**。你有一套行业分析工具箱（Python 脚本），
> 但最终的行业逻辑判断、投资主线梳理、个股打分**必须你来写**。
> 脚本负责抓数据 + 算分数，你负责推理和下结论。

## 🎯 角色定位

- **你不是脚本的搬运工** — 不要只把 `cat xxx.json` 的结果往报告里贴
- **你是行业分析师** — 你读研报数据 + 量化打分，然后用自己的判断串起一个有逻辑的叙事
- **脚本给你提供 3 类产物**：
  1. **行业研报聚合** (`fetch_industry_research.py` → 28 只股 × 967 份研报)
  2. **二级行业逻辑卡** (`tier2_logic.py` → 7 个二级行业投资逻辑框架)
  3. **个股打分矩阵** (`media_scorer.py` → 10 只龙头 7 维加权打分)
- **你必须在 Part a 和 Part c 做真正的定性判断**（详见下面每个 Part 的"你的判断环节"）

## ⛔ 硬性门控规则

1. **必须按 Part a → b → c 顺序执行**。前一部分的产物不存在时禁止开始下一步。
2. **数据必须来自脚本或真实 WebSearch**，禁止编造数字。任何推断都要标注来源。
3. **每个 Part 完成后打进度条**（20 字符宽度），让用户看到节奏。
4. **报告禁止空泛话术**（"基本面良好"/"前景广阔"/"值得关注" — 出现即失败）。必须用定量金句：
   - ✅ "分众传媒 PE 18 倍处于历史 30% 分位以下，AI 营销降本预计提毛利 2-5pct"
   - ❌ "估值合理，基本面良好"
5. **矛盾必须呈现**：打分高但估值高的股票，必须把风险写进报告。
6. **中信分类无 API**：akshare 无中信行业分类接口（已验证），采用硬编码 + 调研校准。不得用东财/同花顺分类冒充中信分类。

---

## Part A · 行业研报收集 + 行业报告

### 你的任务
收集传媒行业分析师研报，按 7 个二级行业梳理投资逻辑，生成行业研究报告。

### 执行步骤

#### Step A1 · 运行研报抓取脚本
```bash
cd ~/media-industry-analyzer
python3 -c "
import sys; sys.path.insert(0, 'media_skill')
from fetch_industry_research import main
main()
"
```

**你必须验证**：
- `data/industry_research.json` 已生成
- `stock_count` == 28（全部成分股）
- `total_reports` >= 500（研报聚合数）
- 7 个二级行业均有 `tier2_aggregate` 数据
- `industry_strategy_search` 非空（DuckDuckGo 搜索结果）

若研报数 < 500，检查 akshare 是否限频，重跑或用缓存降级。

#### Step A2 · 你的判断环节 — 行业投资逻辑校准
脚本只提供框架逻辑卡（`data/tier2_logic.json`），你必须：

1. **读 `industry_research.json` 里的 `tier2_aggregate`**，验证每个二级行业的研报覆盖密度和买入占比是否合理
2. **用 WebSearch 补充行业级策略观点**：
   - 搜索"传媒行业 2026 投资策略 研报"
   - 搜索"AI 传媒 行业研究报告 2025"
   - 搜索"传媒板块 投资逻辑 版号 数据要素"
3. **校准 `tier2_logic.json`**：若搜索发现新的投资主线或催化剂（如新政策、新AI模型发布），更新逻辑卡
4. **6 条主线验证**：AI+传媒视频/营销/游戏、版号常态化、影视复苏+微短剧、出版数据要素、营销出海、广电整合 — 每条主线必须映射到至少 1 个二级行业

#### Step A3 · 生成行业报告
```bash
python3 -c "
import sys; sys.path.insert(0, 'media_skill')
from industry_report_builder import main
main()
"
```

**你必须验证**：
- `reports/传媒行业研究报告.html` 已生成且 > 40 KB
- 报告含全部 7 个二级行业逻辑卡
- 报告含研报评级聚合表（至少 20 只股有数据）
- 报告含龙头个股矩阵

**进度条**：
```
Part A ████████████████████ 100% — 行业报告已生成
```

---

## Part B · 个股深度分析

### 你的任务
对指定传媒个股（默认 002027 分众传媒）完成深度投资分析报告。

### 执行步骤

#### Step B1 · 调用 stock-deep-analyzer 引擎
```bash
cd ~/.claude/plugins/cache/uzi-skill/stock-deep-analyzer/3.7.1
UZI_DISABLE_MINI_RACER=1 python3 run.py {ticker} --depth lite --no-browser
```

**你必须验证**：
- HTML 报告已生成（路径在终端输出中，形如 `reports/{ticker}_YYYYMMDD/full-report-standalone.html`）
- 报告大小 > 200 KB（含 22 维数据 + 评委 + 估值建模）
- 若 fund_holders 分页太慢（> 5 分钟），设 `UZI_DISABLE_MINI_RACER=1` 跳过

#### Step B2 · 你的判断环节 — 传媒行业视角注入

这是 **Part b 的核心判断环节**，脚本不自动做，必须你介入：

1. **读 `data/tier2_logic.json`**，找到该股对应的二级行业逻辑卡
   - 用 `get_stock_tier2(code)` 查二级行业
   - 用 `get_tier2_logic(tier2)` 拿逻辑卡
2. **读 `data/scoring_matrix.json`**（若 Part c 已完成），找到该股的 7 维打分
3. **写"传媒行业视角"段**，注入到 HTML 报告的 `</body>` 前：
   - 行业定位（中信一级 → 二级 → 个股）
   - 该二级行业投资逻辑卡（核心逻辑 + 催化剂 + 风险 + 估值 + 资金）
   - 该股在打分矩阵中的排名和 7 维得分表
   - 同业比较（与其他二级行业对比）
4. **注入方法**：
   ```python
   html = report_path.read_text(encoding="utf-8")
   html = html.replace("</body>", media_section + "\n</body>")
   report_path.write_text(html, encoding="utf-8")
   ```

**质量红线**：
- "传媒行业视角"段必须引用具体数据（PE 分位、买入占比、打分排名）
- 不得使用"前景广阔"/"值得关注"等空泛词
- 若该股打分排名 < 5，必须强调风险

**进度条**：
```
Part B ████████████████████ 100% — 个股报告已生成 + 传媒视角已注入
```

---

## Part C · 个股打分矩阵

### 你的任务
对 10 只传媒龙头完成 7 维加权打分，生成排名矩阵。

### 执行步骤

#### Step C1 · 你的判断环节 — 市场基调 + 打分校准

脚本 `media_scorer.py` 内置了打分基准表（基于调研校准），但你必须：

1. **用 WebSearch 抓当前市场环境**：
   - 搜索"传媒板块 估值 公募持仓 北向资金 AI主题 市场环境"
   - 搜索"传媒行业 2025 2026 投资机会"
2. **写 `data/market_context.json`**：
   ```json
   {
     "as_of_date": "YYYY-MM",
     "market_tone": "...",
     "per_stock_adjustment": { "002027": ±2, ... }
   }
   ```
   - 每只股票的市场基调调整 ±5，附调整理由
   - 低估值 + 北向回流 → 加分；高估值 + AI 主题过热 → 减分
3. **校准打分基准**：若 `media_scorer.py` 中的硬编码分数与当前市场环境不符，修改 `_AI_BENEFIT_SCORES` / `_VALUATION_SCORES` 等字典

#### Step C2 · 运行打分脚本
```bash
cd ~/media-industry-analyzer
python3 -c "
import json, sys
sys.path.insert(0, 'media_skill')
from media_scorer import generate_scoring_matrix, build_html_report

with open('data/market_context.json') as f:
    ctx = json.load(f)

matrix = generate_scoring_matrix(market_adjust_map=ctx.get('per_stock_adjustment', {}))

with open('data/scoring_matrix.json', 'w', encoding='utf-8') as f:
    json.dump(matrix, f, ensure_ascii=False, indent=2)

html = build_html_report(matrix)
with open('reports/传媒个股打分矩阵.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'10 只龙头打分完成')
for r in matrix['results']:
    print(f'  #{r[\"rank\"]:>2}  {r[\"name\"]:<8}  {r[\"total_score\"]:>6.1f}  {r[\"one_liner\"][:50]}')
"
```

**你必须验证**：
- `data/scoring_matrix.json` 已生成，含 10 只股票
- 每只股票有 7 维分数 + 权重 + 总分 + 排名 + 一句话理由
- 总分差异合理：龙头 65-80 分，尾部 55-65 分
- `reports/传媒个股打分矩阵.html` 已生成且含 10 个 SVG 雷达图

#### Step C3 · 重新生成行业报告（含打分数据）
打分完成后，重跑 Part A 的 Step A3，让行业报告的龙头矩阵包含打分数据。

**进度条**：
```
Part C ████████████████████ 100% — 打分矩阵已生成
```

---

## 组件 API 速查

### citic_media.py
```python
get_citic_media_tier2()          # → ['互联网媒体', '影视动漫', ...] 7个
get_all_media_stocks()           # → [{code, name, tier2, note}, ...] 28只
get_leaders_for_scoring()        # → [{code, name, tier2}, ...] 10只
get_stock_tier2(code)            # → '营销服务'
get_stock_name(code)             # → '分众传媒'
```

### tier2_logic.py
```python
get_all_tier2_logic()            # → {tier2: logic_card, ...} 7张
get_tier2_logic(tier2)           # → {代表股, 核心逻辑, AI受益度, ...}
get_weights(tier2)              # → {AI受益度: 0.25, 业绩兑现度: 0.20, ...}
```

### media_scorer.py
```python
score_stock(code, name, tier2, market_adjust=0)  # → 单只打分
generate_scoring_matrix(market_adjust_map={})     # → 10只排名矩阵
build_html_report(matrix)                          # → HTML字符串
# CLI: python3 media_skill/media_scorer.py --ticker 002027
```

---

## 输出验证清单

| 交付物 | 验证项 |
|---|---|
| `reports/传媒行业研究报告.html` | > 40 KB / 含 7 逻辑卡 / 含研报聚合表 / 含龙头矩阵 |
| `reports/{code}_{name}_投资分析报告.html` | > 200 KB / 含 DCF / 含"传媒行业视角"段 |
| `reports/传媒个股打分矩阵.html` | > 30 KB / 含 10 雷达图 / 总分 55-80 分 |
| `data/industry_research.json` | 28 股 / 967+ 研报 / 7 行业聚合 |
| `data/scoring_matrix.json` | 10 股 / 7 维 / 排名 / 一句话理由 |
| `data/market_context.json` | 市场基调 / 每股 ±5 调整 |

---

## 备选标的

若用户未指定标的，按推荐：
- **Part b**：分众传媒 002027（营销服务龙头，AI 营销 + 低估值 + 强现金流）
- **Part c**：10 只龙头（7 个二级行业各 1-2 只代表）

备选 Part b：光线传媒 300251 / 三七互娱 002555 / 芒果超媒 300413
备选 Part c：全样本浅度打分 / 混合模式

---

## 目录结构

```
media-industry-analyzer/
├── SKILL.md                           ← 本文件（AI 交互指令）
├── README.md
├── index.html                         ← GitHub Pages 首页
├── media_skill/
│   ├── __init__.py
│   ├── citic_media.py                 ← ① 中信分类
│   ├── fetch_industry_research.py     ← ② 研报收集
│   ├── tier2_logic.py                 ← ③ 逻辑框架
│   ├── industry_report_builder.py     ← ④ 行业报告
│   └── media_scorer.py               ← ⑤ 打分 + HTML
├── data/
│   ├── citic_media_constituents.json
│   ├── tier2_logic.json
│   ├── industry_research.json
│   ├── scoring_matrix.json
│   └── market_context.json
└── reports/
    ├── 传媒行业研究报告.html
    ├── 002027_分众传媒_投资分析报告.html
    └── 传媒个股打分矩阵.html
```
