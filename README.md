# media-industry-analyzer · 传媒行业研究 Skill

## 报告

| 交付物                        | 路径                                          | 说明                                                                |
| ----------------------------- | --------------------------------------------- | ------------------------------------------------------------------- |
| **a. 传媒行业研究报告** | `reports/传媒行业研究报告.html`             | 中信一级行业·传媒，7 个二级行业投资逻辑 + 研报观点聚合 + 龙头矩阵  |
| **b. 个股投资分析报告** | `reports/002027_分众传媒_投资分析报告.html` | 分众传媒 002027，22 维数据 + 52 评委 + DCF/Comps/LBO + 传媒行业视角 |
| **c. 传媒个股打分矩阵** | `reports/传媒个股打分矩阵.html`             | 10 只龙头 7 维加权打分 + 雷达图 + 排名                              |

## Skill 架构

```
media-industry-analyzer/
├── README.md                         ← 本文件
├── media_skill/                      ← 核心代码
│   ├── citic_media.py                ← ① 中信传媒分类 + 7 二级行业 + 30 只代表股
│   ├── fetch_industry_research.py    ← ② 行业研报批量收集（akshare + DDGS）
│   ├── tier2_logic.py               ← ③ 7 二级行业投资逻辑框架
│   ├── industry_report_builder.py    ← ④ 行业研究报告生成器
│   └── media_scorer.py              ← ⑤ 个股打分框架（7 维加权 + 雷达图 HTML）
├── data/
│   ├── citic_media_constituents.json ← 传媒成分股清单（硬编码+校准）
│   ├── tier2_logic.json             ← 7 二级行业投资逻辑卡
│   ├── industry_research.json       ← 抓取的研报聚合数据（967份研报）
│   ├── scoring_matrix.json          ← 10 只龙头打分结果
│   └── market_context.json          ← 当前市场环境基调
└── reports/                          ← 最终交付报告（HTML）
```

## 使用

### 重新抓取行业研报

```bash
cd ~/media-industry-analyzer
python3 -c "import sys; sys.path.insert(0,'media_skill'); from fetch_industry_research import main; main()"
```

### 重新生成行业研究报告

```bash
python3 -c "import sys; sys.path.insert(0,'media_skill'); from industry_report_builder import main; main()"
```

### 重新生成打分矩阵

```bash
python3 -c "import sys; sys.path.insert(0,'media_skill'); from media_scorer import main; main()"
```

### 对单只新股打分

```bash
python3 media_skill/media_scorer.py --ticker 300251
```

### 分析新股票（复用 stock-deep-analyzer）

```bash
cd ~/.claude/plugins/cache/uzi-skill/stock-deep-analyzer/3.7.1
python3 run.py 300251 --depth medium --no-browser
```

## 设计

### 中信行业分类（无 API → 硬编码）

akshare 无中信行业分类接口（已验证仅有东财/同花顺），故中信传媒二级行业映射采用**硬编码 + 调研校准**。7 个二级行业：互联网媒体 / 影视动漫 / 营销服务 / 游戏 / 出版 / 广播电视 / 其他文化娱乐。

### 7 维打分模型

| 维度       | 0-10 分判据                           |
| ---------- | ------------------------------------- |
| AI 受益度  | AI 视频/营销/游戏对该股的业绩拉动程度 |
| 业绩兑现度 | 营收/利润增速 + 可见度                |
| 估值水位   | PE/PB 历史分位（越低越高分）          |
| 资金关注度 | 公募持仓 + 北向 + ETF 流入            |
| 催化剂密度 | 近 60 天催化事件数 + 量级             |
| 护城河     | 市占率 + IP + 竞争格局                |
| 政策友好度 | 监管环境 + 数据要素/版号受益度        |

**权重按二级行业定制**：如营销服务 AI 受益度权重 0.25，出版政策友好度权重 0.25。

### 市场基调调整

用 WebSearch 抓当前市场环境（板块 PE 分位/公募仓位/北向/近期催化），作为打分的"市场基调"调整项（±5 分），写入 `data/market_context.json`。

## 数据来源

- **研报数据**：akshare `stock_research_report_em`（东财研报，28 只成分股共 967 份）
- **行业策略**：DuckDuckGo 搜索"传媒行业 2026 投资策略 研报"
- **个股深度分析**：复用 `stock-deep-analyzer` skill v3.7.1（22 维 + 52 评委 + DCF/Comps/LBO）
- **行业分类**：中信一级行业分类（硬编码 + 调研校准）

## 复用的现有 Skill

| 组件                     | 来源路径                            | 复用点                       |
| ------------------------ | ----------------------------------- | ---------------------------- |
| `fetch_research.py`    | `.../scripts/fetch_research.py`   | 单股研报抓取逻辑             |
| `lib/web_search.py`    | `.../scripts/lib/web_search.py`   | DuckDuckGo 搜索              |
| `run_real_test.py`     | `.../scripts/run_real_test.py`    | stage1 数据采集引擎          |
| `report-template.html` | `.../assets/report-template.html` | Bloomberg 风格 HTML 模板参考 |
| `/analyze-stock`       | stock-deep-analyzer skill           | Part b 个股深度分析          |
