---
name: media-industry-analyzer
description: 传媒行业研究 skill。当用户要求"传媒行业分析 / 传媒研报 / 传媒个股打分 / 传媒投资逻辑 / 中信传媒 / 分析传媒板块"等请求时触发。覆盖中信一级行业·传媒下 7 个二级行业（互联网媒体/影视动漫/营销服务/游戏/出版/广播电视/其他文化娱乐），产出行业研究报告 + 个股深度分析 + 个股打分矩阵。关键词：传媒、行业研究、中信行业、二级行业、投资逻辑、个股打分、分众传媒、AI传媒、版号、数据要素。
version: 1.0.0
author: media-industry-analyzer
license: MIT
metadata:
  tags: [finance, media, citic-industry, a-share, ai-media, scoring, research-report]
  related_skills: [stock-deep-analyzer]
---

# Media Industry Analyzer · 传媒行业研究 Skill v1.0

> 你正在扮演一位**传媒行业首席分析师**。你有一套行业分析工具箱（Python 脚本），
> 但最终的行业逻辑判断、投资主线梳理、个股打分**必须你来写**。
> 脚本负责抓数据 + 算分数，你负责推理和下结论。

## 🎯 角色定位（非常重要）

- **你不是脚本的搬运工** — 不要只把 `cat xxx.json` 的结果往报告里贴
- **你是行业分析师** — 你读研报数据 + 量化打分，然后用自己的判断串起一个有逻辑的叙事
- **脚本给你提供 3 类产物**：
  1. **行业研报聚合** (`fetch_industry_research.py` → 28 只股 × ~967 份研报)
  2. **二级行业逻辑卡** (`tier2_logic.py` → 7 个二级行业投资逻辑框架)
  3. **个股打分矩阵** (`media_scorer.py` → 10 只龙头 7 维加权打分)
- **你必须在每个 Part 的"你的判断环节"做真正的定性判断**

## ⛔ 硬性门控规则（违反即停止）

### GATE-1 · 执行顺序
必须按 **Part A → B → C** 顺序执行。前一部分的产物 JSON 不存在时禁止开始下一步。
唯一例外：Part B 的个股分析可在 Part C 之前或之后跑，但"传媒行业视角"段的打分数据需要 Part C 完成。

### GATE-2 · 数据真实性
- **数据必须来自脚本或真实 WebSearch**，禁止编造数字
- 任何推断都要标注来源（akshare / WebSearch / 调研校准）
- 打分基准表中的分数必须能追溯到研报数据或市场公开信息

### GATE-3 · 禁止空泛话术
报告禁止出现以下三个词组，出现即失败：
- ❌ "基本面良好"
- ❌ "前景广阔"
- ❌ "值得关注"

必须用有冲突感的定量金句：
- ✅ "分众传媒 PE 18 倍处于历史 30% 分位以下，AI 营销降本预计提毛利 2-5pct"
- ✅ "昆仑万维 PE 40 倍含 AI 溢价，但 2026 EPS 共识 0.47 元，需业绩兑现"
- ❌ "估值合理，基本面良好"

### GATE-4 · 矛盾必须呈现
打分高但估值高的股票（如昆仑万维），**必须把风险写进报告**。
研报买入占比 100% 但股价下跌的，**必须强调分歧本身是信息**。

### GATE-5 · 中信分类不可冒充
akshare 无中信行业分类接口（已验证仅有东财/同花顺），采用**硬编码 + 调研校准**。
- 不得用东财/同花顺分类冒充中信分类
- 若用户质疑分类准确性，回答"基于调研校准的硬编码映射，akshare 无中信接口"
- 新增股票需人工确认其二级行业归属后再加入 `citic_media_constituents.json`

### GATE-6 · 进度条
每个 Part 完成后必须打进度条（20 字符宽度）：
```
Part A ████████████████████ 100% — 行业报告已生成
```

---

## Part A · 行业研报收集 + 行业报告

### 你的任务
收集传媒行业分析师研报，按 7 个二级行业梳理投资逻辑，生成行业研究报告。

### Step A1 · 运行研报抓取脚本

```bash
cd ~/media-industry-analyzer
python3 -c "
import sys; sys.path.insert(0, 'media_skill')
from fetch_industry_research import main
main()
"
```

**脚本内部流程**：
1. 调 `get_all_media_stocks()` 获取 28 只成分股
2. 逐只调 `akshare.stock_research_report_em(symbol=code)` 抓研报
3. 每只间隔 0.3s 防限频
4. DuckDuckGo 搜"传媒行业 2026 投资策略 研报"等 3 个 query
5. 按 Tier-2 聚合：评级均值 / 目标价空间 / 研报覆盖密度
6. 输出 `data/industry_research.json`

#### ⚠️ 错误处理与降级

| 错误 | 症状 | 降级策略 |
|---|---|---|
| akshare 限频 | 某些股返回 0 研报 | 重跑单只：`python3 -c "import akshare as ak; print(ak.stock_research_report_em(symbol='002027'))"` |
| akshare 登录失败 | stderr 有 `login success!` 但返回空 | 等 10s 重试，最多 3 次 |
| DDGS 超时 | stderr 有 `ddgs: timeout` | 脚本已内置 10s 硬超时 + ThreadPoolExecutor，超时返空不 crash |
| DDGS 被墙 | `industry_strategy_search` 为空 | 用 WebSearch 工具手动搜 3 个 query 补数据 |
| mini_racer crash | stderr 有 `address_pool_manager` | 不影响研报抓取（仅影响 valuation/industry_pe） |

#### 验证清单（必须逐项检查）

```python
import json
with open('data/industry_research.json') as f:
    d = json.load(f)

# ✅ 必须全部通过
assert d['stock_count'] == 28, f"成分股数 {d['stock_count']} != 28"
total_reports = sum(s['report_count'] for s in d['stock_research'])
assert total_reports >= 500, f"研报总数 {total_reports} < 500"
assert len(d['tier2_aggregate']) == 7, "7 个二级行业聚合缺失"
assert len(d['industry_strategy_search']) > 0, "DDGS 搜索结果为空"

# 逐行业检查
for t2, agg in d['tier2_aggregate'].items():
    assert agg['stock_count'] > 0, f"{t2} 无成分股"
    assert agg['total_reports'] > 0, f"{t2} 无研报"
    print(f"  {t2}: {agg['stock_count']}股 / {agg['total_reports']}研报 / 买入{agg['avg_buy_pct']}%")
```

若 `total_reports < 500`：检查哪些股返回 0 研报，重跑单只或用缓存降级。

### Step A2 · 你的判断环节 — 行业投资逻辑校准

**这是 Part A 的核心判断环节**，脚本只提供框架逻辑卡，你必须：

#### A2.1 · 读研报聚合数据，验证逻辑卡合理性

```python
import json
with open('data/tier2_logic.json') as f:
    logic = json.load(f)
with open('data/industry_research.json') as f:
    research = json.load(f)

# 逐行业对比逻辑卡 vs 研报数据
for t2, card in logic.items():
    agg = research['tier2_aggregate'].get(t2, {})
    ai_benefit = card['AI受益度']
    buy_pct = agg.get('avg_buy_pct', 0)
    pe = agg.get('avg_pe_2026')
    print(f"\n{t2}:")
    print(f"  逻辑卡 AI受益度: {ai_benefit}")
    print(f"  研报买入占比: {buy_pct}%")
    print(f"  2026 PE: {pe}")
    # 若买入占比 < 70% 但逻辑卡说"高 AI 受益"，需判断是否逻辑有变
```

#### A2.2 · 用 WebSearch 补充行业级策略观点

必须搜索以下 3 个 query（用 WebSearch 工具，不是脚本里的 DDGS）：
1. `"传媒行业 2026 投资策略 研报"`
2. `"AI 传媒 行业研究报告 2025"`
3. `"传媒板块 投资逻辑 版号 数据要素"`

对每条搜索结果：
- 提取核心观点（AI 落地进度 / 版号节奏 / 数据要素政策 / 微短剧监管）
- 若发现新主线或催化剂，更新 `tier2_logic.json` 对应逻辑卡

#### A2.3 · 6 条主线验证

必须验证以下 6 条投资主线，每条映射到至少 1 个二级行业：

| 主线 | 对应二级行业 | 验证方式 |
|---|---|---|
| AI+传媒视频/营销/游戏 | 互联网媒体/营销服务/游戏 | WebSearch "AI视频 Sora Kling 传媒" |
| 版号常态化 | 游戏 | WebSearch "2025 2026 游戏版号 月度发放" |
| 影视复苏+微短剧 | 影视动漫 | WebSearch "微短剧 市场 规模 2025" |
| 出版数据要素 | 出版 | WebSearch "数据要素 政策 出版 数据资产入表" |
| 营销出海 | 营销服务 | WebSearch "中国品牌 出海营销 增长" |
| 广电整合 | 广播电视 | WebSearch "全国一网 广电整合 2025" |

若某条主线有重大变化（如新政策发布），更新 `tier2_logic.json` 的 `核心投资逻辑` / `关键催化剂` 字段。

### Step A3 · 生成行业报告

```bash
python3 -c "
import sys; sys.path.insert(0, 'media_skill')
from industry_report_builder import main
main()
"
```

#### 验证清单

```python
from pathlib import Path
import json

html = Path('reports/传媒行业研究报告.html').read_text(encoding='utf-8')
assert len(html) > 40000, f"报告太小: {len(html)} bytes"
for t2 in ['互联网媒体','影视动漫','营销服务','游戏','出版','广播电视','其他文化娱乐']:
    assert t2 in html, f"缺少 {t2} 逻辑卡"
assert '研报观点' in html, "缺少研报汇总章节"
assert '龙头' in html, "缺少龙头矩阵"
print("✅ 行业报告验证通过")
```

**进度条**：
```
Part A ████████████████████ 100% — 行业报告已生成
```

---

## Part B · 个股深度分析

### 你的任务
对指定传媒个股（默认 002027 分众传媒）完成深度投资分析报告，并增补"传媒行业视角"段。

### Step B1 · 调用 stock-deep-analyzer 引擎

```bash
cd ~/.claude/plugins/cache/uzi-skill/stock-deep-analyzer/3.7.1
UZI_DISABLE_MINI_RACER=1 UZI_DDG_BUDGET=10 python3 run.py {ticker} --depth lite --no-browser
```

**参数说明**：
- `--depth lite`：7 维 + 10 评委，30-60s 完成（medium 需 5-8 分钟）
- `--no-browser`：不自动打开浏览器（适合 CI / agent 环境）
- `UZI_DISABLE_MINI_RACER=1`：跳过 fetch_industry / fetch_capital_flow / fetch_valuation 三个用 mini_racer 的 fetcher（macOS 上 mini_racer 可能 SIGTRAP）
- `UZI_DDG_BUDGET=10`：限制 DDGS 搜索 10 次（防 token 爆炸）

#### ⚠️ 已知问题与降级

| 问题 | 症状 | 降级 |
|---|---|---|
| fund_holders 分页太慢 | 进度条 `0/879` 卡住超过 3 分钟 | kill 进程，加 `UZI_DISABLE_MINI_RACER=1` 重跑 |
| mini_racer SIGTRAP | `address_pool_manager.cc Check failed` | 设 `UZI_DISABLE_MINI_RACER=1` |
| Playwright 缺失 | `BrowserType.launch: Executable doesn't exist` | 不影响 HTML 报告生成，仅跳过分享卡截图 |
| akshare 登录失败 | `login success!` 但返回空 | 等 10s 重跑 |
| 报告生成但缺评委 | `_review_issues.json` 有 warning | lite 模式正常，HTML 仍可生成 |

#### 获取报告路径

```bash
# 报告路径在终端输出最后一行
# 形如：reports/{ticker}_YYYYMMDD/full-report-standalone.html
REPORT=$(find ~/.claude/plugins/cache/uzi-skill/stock-deep-analyzer/3.7.1/skills/deep-analysis/scripts/reports -name "full-report-standalone.html" -newer /tmp/marker 2>/dev/null | head -1)
echo "报告路径: $REPORT"
```

#### 验证

```python
from pathlib import Path
report_path = Path(REPORT)  # 替换为实际路径
assert report_path.exists(), "报告文件不存在"
assert report_path.stat().st_size > 200000, f"报告太小: {report_path.stat().st_size}"
html = report_path.read_text(encoding='utf-8')
assert 'DCF' in html or '估值' in html, "缺少估值章节"
print(f"✅ 个股报告验证通过 ({report_path.stat().st_size/1024:.0f} KB)")
```

### Step B2 · 你的判断环节 — 传媒行业视角注入

**这是 Part B 的核心判断环节**，脚本不自动做，必须你介入。

#### B2.1 · 查该股的二级行业 + 逻辑卡

```python
import sys, json
sys.path.insert(0, 'media_skill')
from citic_media import get_stock_tier2, get_stock_name

code = "002027"  # 替换为实际代码
tier2 = get_stock_tier2(code)
name = get_stock_name(code)
print(f"{code} {name} → 二级行业: {tier2}")

with open('data/tier2_logic.json') as f:
    logic = json.load(f)
card = logic[tier2]
print(f"逻辑卡: {card['核心投资逻辑']}")
```

#### B2.2 · 读打分数据（若 Part C 已完成）

```python
with open('data/scoring_matrix.json') as f:
    scoring = json.load(f)
stock_score = next(r for r in scoring['results'] if r['code'] == code)
print(f"排名: #{stock_score['rank']}, 总分: {stock_score['total_score']}")
```

若 Part C 未完成，跳过打分表注入，只注入逻辑卡。

#### B2.3 · 写"传媒行业视角"段并注入 HTML

注入的 HTML 段必须包含 4 个子段：

1. **行业定位** — 中信一级 → 二级 → 个股，说明该股在 6 条主线中的位置
2. **该二级行业投资逻辑卡** — 核心逻辑 / 催化剂 / 风险 / 估值 / 资金（从 `tier2_logic.json` 提取）
3. **个股打分表** — 7 维得分 + 权重 + 加权得分 + 总分 + 排名 + 一句话理由（从 `scoring_matrix.json` 提取）
4. **同业比较** — 与其他二级行业对比，附跳转链接到行业报告和打分矩阵

注入方法（Python str.replace）：

```python
from pathlib import Path

report_path = Path('reports/002027_分众传媒_投资分析报告.html')
# 先把原始报告复制过来
import shutil
shutil.copy(REPORT_ORIGINAL, report_path)

html = report_path.read_text(encoding='utf-8')
html = html.replace("</body>", media_section + "\n</body>")
report_path.write_text(html, encoding='utf-8')
```

#### 质量红线

- "传媒行业视角"段必须引用具体数据（PE 分位、买入占比、打分排名）
- 不得使用 GATE-3 禁止的空泛词
- 若该股打分排名 < 5，必须强调风险和分歧
- 逻辑卡的催化剂和风险必须原样来自 `tier2_logic.json`，不得编造

**进度条**：
```
Part B ████████████████████ 100% — 个股报告已生成 + 传媒视角已注入
```

---

## Part C · 个股打分矩阵

### 你的任务
对 10 只传媒龙头完成 7 维加权打分，生成排名矩阵 HTML。

### 7 维打分模型

| 维度 | 0-10 分判据 | 数据来源 | 权重默认 |
|---|---|---|---|
| AI 受益度 | AI 视频/营销/游戏对该股业绩拉动程度 | 研报 + AI 判断 | 0.15 |
| 业绩兑现度 | 营收/利润增速 + 可见度 | 研报 EPS 共识 | 0.20 |
| 估值水位 | PE/PB 历史分位（越低越高分） | 研报 PE + 行业 PE | 0.15 |
| 资金关注度 | 公募持仓 + 北向 + ETF 流入 | WebSearch + 研报 | 0.10 |
| 催化剂密度 | 近 60 天催化事件数 + 量级 | tier2_logic + WebSearch | 0.15 |
| 护城河 | 市占率 + IP + 竞争格局 | 研报 + AI 判断 | 0.15 |
| 政策友好度 | 监管环境 + 数据要素/版号受益度 | tier2_logic + WebSearch | 0.10 |

**权重按二级行业定制**（来自 `tier2_logic.json` 的 `逻辑权重建议`）：
- 营销服务：AI 受益度 0.25 / 业绩 0.20 / 估值 0.15 / 资金 0.10 / 催化 0.15 / 护城河 0.10 / 政策 0.05
- 出版：政策友好度 0.25 / 业绩 0.20 / 估值 0.15 / 护城河 0.15 / 资金 0.10 / 催化 0.10 / AI 0.05
- 广播电视：政策友好度 0.30 / 业绩 0.15 / 估值 0.15 / 资金 0.10 / 催化 0.15 / 护城河 0.10 / AI 0.05

**总分** = Σ(维度分 × 权重) × 10 → 0-100
**市场基调调整**：±5，来自 `data/market_context.json`

### Step C1 · 你的判断环节 — 市场基调 + 打分校准

#### C1.1 · 用 WebSearch 抓当前市场环境

必须搜索以下 query（用 WebSearch 工具）：
1. `"传媒板块 估值 公募持仓 北向资金 AI主题 市场环境"`
2. `"传媒行业 2025 2026 投资机会"`
3. `"分众传媒 机构持仓 北向"` (替换为目标股名)

从搜索结果中提取：
- 板块整体 PE 分位（低/中/高）
- 公募基金对传媒板块的配置比例（低配/标配/超配）
- 北向资金流向（流入/流出/中性）
- AI 主题热度（高/中/低）
- 政策环境（利好/中性/利空）

#### C1.2 · 写 `data/market_context.json`

```json
{
  "as_of_date": "YYYY-MM",
  "market_tone": "一句话总结",
  "overall_adjustment": 0,
  "key_factors": {
    "估值水位": "...",
    "公募仓位": "...",
    "北向资金": "...",
    "AI主题热度": "...",
    "政策环境": "...",
    "消费环境": "..."
  },
  "per_stock_adjustment": {
    "002027": 2,
    "300251": 1,
    "...": 0
  },
  "adjustment_logic": {
    "002027": "分众传媒：低估值+强现金流+AI营销落地，北向回流+2",
    "300251": "光线传媒：底部区域+AI影视催化+微短剧，+1"
  }
}
```

**调整规则**：
- 低估值 + 北向回流 + 业绩确定性高 → +2~+5
- 高估值 + AI 主题过热 + 业绩未兑现 → -1~-3
- 中性 → 0

#### C1.3 · 校准打分基准表

`media_scorer.py` 内置了 7 个打分字典（硬编码，基于调研校准）：

```python
_AI_BENEFIT_SCORES = {"002027": 8, "300251": 7, ...}      # AI 受益度
_CATALYST_SCORES = {"002027": 7, "300251": 8, ...}         # 催化剂密度
_MOAT_SCORES = {"002027": 9, "300251": 8, ...}             # 护城河
_POLICY_SCORES = {"002027": 6, "300251": 6, ...}            # 政策友好度
_PERFORMANCE_SCORES = {"002027": 7, "300251": 7, ...}      # 业绩兑现度
_VALUATION_SCORES = {"002027": 8, "300251": 7, ...}        # 估值水位
_CAPITAL_SCORES = {"002027": 6, "300251": 5, ...}          # 资金关注度
```

**校准流程**：
1. 读 `data/industry_research.json` 获取每只股的 `consensus_pe_2026` / `buy_rating_pct`
2. 对照打分字典，若 PE < 15 但 `_VALUATION_SCORES` 给 5 → 调到 8-9
3. 若 `buy_rating_pct` < 70% 但 `_PERFORMANCE_SCORES` 给 7 → 降到 5-6
4. 若 WebSearch 发现新催化剂 → 调高 `_CATALYST_SCORES`
5. 修改后重跑 `media_scorer.py`

### Step C2 · 运行打分脚本

```bash
cd ~/media-industry-analyzer
python3 -c "
import json, sys, os
sys.path.insert(0, 'media_skill')
from media_scorer import generate_scoring_matrix, build_html_report

# 加载市场基调
with open('data/market_context.json') as f:
    ctx = json.load(f)

# 生成打分矩阵
matrix = generate_scoring_matrix(market_adjust_map=ctx.get('per_stock_adjustment', {}))

# 保存 JSON
with open('data/scoring_matrix.json', 'w', encoding='utf-8') as f:
    json.dump(matrix, f, ensure_ascii=False, indent=2)

# 生成 HTML
os.makedirs('reports', exist_ok=True)
html = build_html_report(matrix)
with open('reports/传媒个股打分矩阵.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'10 只龙头打分完成')
for r in matrix['results']:
    print(f'  #{r[\"rank\"]:>2}  {r[\"name\"]:<8}  {r[\"tier2\"]:<10}  {r[\"total_score\"]:>6.1f}  {r[\"one_liner\"][:50]}')
"
```

#### 验证清单

```python
import json
from pathlib import Path

with open('data/scoring_matrix.json') as f:
    m = json.load(f)

# ✅ 基础验证
assert m['stock_count'] == 10, f"股票数 {m['stock_count']} != 10"
assert len(m['results']) == 10, "结果数不足 10"
assert m['dimensions'] == ['AI受益度','业绩兑现度','估值水位','资金关注度','催化剂密度','护城河','政策友好度']

# ✅ 排名验证
for i, r in enumerate(m['results']):
    assert r['rank'] == i + 1, f"排名不连续: #{r['rank']} 应为 #{i+1}"

# ✅ 分数范围验证
for r in m['results']:
    assert 50 <= r['total_score'] <= 90, f"{r['name']} 总分 {r['total_score']} 超范围"
    for d in r['dimensions'].values():
        assert 1 <= d <= 10, f"{r['name']} 维度分 {d} 超范围"
    assert abs(sum(r['weights'].values()) - 1.0) < 0.01, f"{r['name']} 权重和不为 1"

# ✅ 分数差异合理性
scores = [r['total_score'] for r in m['results']]
score_range = max(scores) - min(scores)
assert score_range >= 10, f"分数差异太小 ({score_range})，龙头和尾部应有 10+ 分差"

# ✅ HTML 验证
html = Path('reports/传媒个股打分矩阵.html').read_text(encoding='utf-8')
assert html.count('<svg') == 10, f"雷达图数量 {html.count('<svg')} != 10"
assert '分众传媒' in html, "缺少分众传媒"
print("✅ 打分矩阵验证通过")
```

### Step C3 · 重新生成行业报告（含打分数据）

打分完成后，重跑 Part A 的 Step A3，让行业报告的龙头矩阵包含打分数据：

```bash
python3 -c "
import sys; sys.path.insert(0, 'media_skill')
from industry_report_builder import main
main()
"
```

**进度条**：
```
Part C ████████████████████ 100% — 打分矩阵已生成
```

---

## ⛔ HARD-GATE-SELF-REVIEW · 出报告前的自查清单

在交付三份 HTML 之前，必须逐项检查：

| # | 检查项 | severity | 方法 |
|---|---|---|---|
| 1 | `传媒行业研究报告.html` > 40 KB | 🔴 | `Path('reports/传媒行业研究报告.html').stat().st_size > 40000` |
| 2 | 行业报告含 7 个二级行业名 | 🔴 | 逐个 `assert t2 in html` |
| 3 | 行业报告含研报聚合表 | 🔴 | `assert '研报' in html` |
| 4 | `industry_research.json` 含 28 股 | 🔴 | `assert d['stock_count'] == 28` |
| 5 | 研报总数 >= 500 | 🔴 | `assert total_reports >= 500` |
| 6 | DDGS 搜索结果非空 | 🟡 | `assert len(d['industry_strategy_search']) > 0` |
| 7 | 个股报告 > 200 KB | 🔴 | `Path(report).stat().st_size > 200000` |
| 8 | 个股报告含"传媒行业视角" | 🔴 | `assert '传媒行业视角' in html` |
| 9 | 个股报告含 DCF/估值 | 🔴 | `assert 'DCF' in html or '估值' in html` |
| 10 | 打分矩阵含 10 只股 | 🔴 | `assert m['stock_count'] == 10` |
| 11 | 打分矩阵含 10 个 SVG 雷达图 | 🔴 | `assert html.count('<svg') == 10` |
| 12 | 打分总分 50-90 范围 | 🔴 | `assert 50 <= r['total_score'] <= 90` |
| 13 | 权重和 = 1.0 | 🔴 | `assert abs(sum(w.values()) - 1.0) < 0.01` |
| 14 | 排名连续 1-10 | 🔴 | `assert r['rank'] == i+1` |
| 15 | 分数差异 >= 10 分 | 🟡 | `assert max - min >= 10` |
| 16 | 无 GATE-3 禁词 | 🔴 | 搜 "基本面良好"/"前景广阔"/"值得关注" |
| 17 | `market_context.json` 存在 | 🟡 | `Path('data/market_context.json').exists()` |

**迭代流程**：
```
loop:
  1. 运行自查清单
  2. if 有 🔴: 修问题，重跑对应步骤
  3. if 有 🟡: 要么修，要么在报告里标注原因
  4. 全部通过 → 交付
```

---

## 组件 API 速查

### citic_media.py
```python
get_citic_media_tier2()          # → ['互联网媒体', '影视动漫', '营销服务', '游戏', '出版', '广播电视', '其他文化娱乐']
get_constituents(tier2=None)     # → [{code, name, tier2, note}, ...] 可按二级行业过滤
get_all_media_stocks()           # → [{code, name, tier2, note}, ...] 全部 28 只
get_leaders_for_scoring()        # → [{code, name, tier2}, ...] 打分用 10 只龙头
get_stock_tier2(code)            # → '营销服务'（根据代码查二级行业）
get_stock_name(code)              # → '分众传媒'
```

### tier2_logic.py
```python
get_all_tier2_logic()            # → {tier2: logic_card, ...} 7 张逻辑卡
get_tier2_logic(tier2)           # → {代表股, 行业规模, 核心投资逻辑, AI受益度, ...}
get_weights(tier2)              # → {AI受益度: 0.25, 业绩兑现度: 0.20, ...} 7 维权重
get_ai_benefit(tier2)           # → '高' / '中高' / '中' / '低'
get_valuation_water(tier2)       # → 'PE-TTM 15-25倍，历史30%分位以下'
```

### media_scorer.py
```python
score_stock(code, name, tier2, market_adjust=0)   # → {code, name, tier2, dimensions, weights, total_score, one_liner}
generate_scoring_matrix(market_adjust_map={})       # → {scoring_date, stock_count, dimensions, results}
build_html_report(matrix)                           # → HTML 字符串（含 SVG 雷达图）
_radar_svg(dims, max_val=10, size=140)              # → SVG 字符串

# CLI
# python3 media_skill/media_scorer.py --ticker 002027   # 单只打分
# python3 media_skill/media_scorer.py                    # 全部 10 只打分矩阵
```

### fetch_industry_research.py
```python
_fetch_stock_reports(code)          # → [dict, ...] 单股研报（akshare）
_parse_stock_research(code, name, tier2, reports)  # → {report_count, rating_distribution, ...}
_aggregate_by_tier2(stock_data)    # → {tier2: {stock_count, total_reports, avg_buy_pct, ...}}
_search_industry_strategy()        # → [{query, title, body, url}, ...] DDGS 搜索
main()                              # → 完整 pipeline，输出 data/industry_research.json
```

---

## 数据 Schema

### data/citic_media_constituents.json
```json
{
  "industry_level1": "传媒",
  "classification": "中信一级行业",
  "tier2_list": ["互联网媒体", "影视动漫", "营销服务", "游戏", "出版", "广播电视", "其他文化娱乐"],
  "constituents": [
    {"code": "002027", "name": "分众传媒", "tier2": "营销服务", "note": "电梯媒体龙头+AI营销"}
  ],
  "leaders_for_scoring": [
    {"code": "002027", "name": "分众传媒", "tier2": "营销服务"}
  ]
}
```

### data/tier2_logic.json
```json
{
  "营销服务": {
    "代表股": ["分众传媒002027"],
    "行业规模与增速": "广告市场约1.2万亿...",
    "核心投资逻辑": ["AI营销降本提毛利2-5pct", "出海营销高增长"],
    "AI受益度": "高",
    "关键催化剂": ["AI视频模型迭代", "出海订单放量"],
    "关键风险": ["宏观经济影响广告主预算"],
    "估值水位": "PE-TTM 15-25倍，历史30%分位以下",
    "资金关注度": "公募低配，北向回流",
    "逻辑权重建议": {"AI受益度": 0.25, "业绩兑现度": 0.20, "估值水位": 0.15, "资金关注度": 0.10, "催化剂密度": 0.15, "护城河": 0.10, "政策友好度": 0.05}
  }
}
```

### data/industry_research.json
```json
{
  "collect_date": "2026-09-12 15:58",
  "classification": "中信一级行业·传媒",
  "tier2_list": ["互联网媒体", ...],
  "stock_count": 28,
  "stock_research": [
    {
      "code": "300413", "name": "芒果超媒", "tier2": "互联网媒体",
      "report_count": 60, "broker_count": 13,
      "rating_distribution": {"买入": 44, "增持": 15},
      "buy_rating_pct": 100.0,
      "consensus_eps_2026": 1.217, "consensus_pe_2026": 19.8,
      "consensus_eps_2027": 1.21,
      "brokers": ["万联证券", ...],
      "recent_reports": [{"date": "...", "title": "...", "broker": "...", "rating": "..."}]
    }
  ],
  "tier2_aggregate": {
    "互联网媒体": {"stock_count": 3, "total_reports": 165, "total_brokers": 21, "avg_buy_pct": 100.0, "avg_pe_2026": null, "report_density": 55.0}
  },
  "industry_strategy_search": [{"query": "...", "title": "...", "body": "...", "url": "..."}]
}
```

### data/scoring_matrix.json
```json
{
  "scoring_date": "2026-09-12 16:02",
  "stock_count": 10,
  "dimensions": ["AI受益度", "业绩兑现度", "估值水位", "资金关注度", "催化剂密度", "护城河", "政策友好度"],
  "results": [
    {
      "code": "002027", "name": "分众传媒", "tier2": "营销服务",
      "dimensions": {"AI受益度": 8, "业绩兑现度": 7, "估值水位": 8, "资金关注度": 6, "催化剂密度": 7, "护城河": 9, "政策友好度": 6},
      "weights": {"AI受益度": 0.25, "业绩兑现度": 0.20, "估值水位": 0.15, "资金关注度": 0.10, "催化剂密度": 0.15, "护城河": 0.10, "政策友好度": 0.05},
      "weighted_total": 74.5, "market_adjust": 2, "total_score": 76.5,
      "one_liner": "电梯媒体垄断+AI营销降本提利+低估值强现金流，营销服务首选",
      "rank": 1
    }
  ]
}
```

### data/market_context.json
```json
{
  "as_of_date": "2025-09",
  "market_tone": "低估值+多催化+AI主题驱动",
  "overall_adjustment": 0,
  "key_factors": {"估值水位": "...", "公募仓位": "...", "北向资金": "..."},
  "per_stock_adjustment": {"002027": 2, "300251": 1},
  "adjustment_logic": {"002027": "分众传媒：低估值+强现金流+AI营销落地，北向回流+2"}
}
```

---

## 扩展指南

### 新增股票
1. 编辑 `data/citic_media_constituents.json`，在 `constituents` 数组追加 `{code, name, tier2, note}`
2. 若需打分，在 `leaders_for_scoring` 追加，并在 `media_scorer.py` 的 7 个打分字典中添加该股分数
3. 重跑 `fetch_industry_research.py` 和 `media_scorer.py`

### 新增二级行业
1. 编辑 `data/citic_media_constituents.json` 的 `tier2_list` 追加行业名
2. 在 `data/tier2_logic.json` 追加该行业的逻辑卡（含 7 维权重）
3. 添加该行业的成分股到 `constituents`
4. 重跑全流程

### 更新打分基准
1. 编辑 `media_scorer.py` 的 7 个字典（`_AI_BENEFIT_SCORES` 等）
2. 用 `--ticker` 参数验证单只：`python3 media_skill/media_scorer.py --ticker 300251`
3. 重跑全量打分

### 部署到 GitHub Pages
```bash
git add -A && git commit -m "update" && git push
# GitHub Pages 自动构建，30s 内生效
# 访问 https://{username}.github.io/media-industry-analyzer/
```

---

## 备选标的

若用户未指定标的，按推荐：
- **Part b**：分众传媒 002027（营销服务龙头，AI 营销 + 低估值 + 强现金流）
- **Part c**：10 只龙头（7 个二级行业各 1-2 只代表）

备选 Part b：光线传媒 300251 / 三七互娱 002555 / 芒果超媒 300413
备选 Part c：全 28 只浅度打分 / 混合模式（3 只深度 + 7 只浅度）

---

## 目录结构

```
media-industry-analyzer/
├── SKILL.md                           ← 本文件（AI 交互指令）
├── README.md
├── index.html                         ← GitHub Pages 首页
├── media_skill/
│   ├── __init__.py
│   ├── citic_media.py                 ← ① 中信分类 + 7 二级行业 + 28 只代表股
│   ├── fetch_industry_research.py     ← ② 行业研报批量收集（akshare + DDGS）
│   ├── tier2_logic.py                ← ③ 7 二级行业投资逻辑框架
│   ├── industry_report_builder.py     ← ④ 行业研究报告 HTML 生成器
│   ├── media_scorer.py               ← ⑤ 个股打分 + SVG 雷达图 + HTML
│   └── templates/                     ← 模板目录（预留）
├── data/
│   ├── citic_media_constituents.json  ← 传媒成分股清单（硬编码+校准）
│   ├── tier2_logic.json              ← 7 二级行业投资逻辑卡
│   ├── industry_research.json         ← 研报聚合数据（967 份）
│   ├── scoring_matrix.json            ← 10 只龙头打分结果
│   └── market_context.json            ← 市场环境基调
└── reports/
    ├── 传媒行业研究报告.html           ← Part a 交付
    ├── 002027_分众传媒_投资分析报告.html ← Part b 交付
    └── 传媒个股打分矩阵.html           ← Part c 交付
```
