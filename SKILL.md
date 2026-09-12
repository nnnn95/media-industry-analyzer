---
name: media-industry-analyzer
description: 传媒行业研究 skill。当用户要求"传媒行业分析 / 传媒研报 / 传媒个股打分 / 传媒投资逻辑 / 中信传媒"等请求时触发。覆盖中信一级行业·传媒下 7 个二级行业（互联网媒体/影视动漫/营销服务/游戏/出版/广播电视/其他文化娱乐），产出行业研究报告 + 个股深度分析 + 个股打分矩阵三份 HTML 报告。关键词：传媒、行业研究、中信行业、二级行业、投资逻辑、个股打分、分众传媒、AI传媒。
version: 1.0.0
author: media-industry-analyzer
license: MIT
metadata:
  tags: [finance, media, citic-industry, a-share, ai-media, scoring, research-report]
  related_skills: [stock-deep-analyzer]
---

# Media Industry Analyzer · 传媒行业研究 Skill

> 中信一级行业·传媒，7 个二级行业投资逻辑 + 个股深度分析 + 个股打分矩阵。

## 三部分交付

| Part | 产出 | 命令 |
|---|---|---|
| **a. 行业研究** | `reports/传媒行业研究报告.html` | `python3 media_skill/fetch_industry_research.py && python3 media_skill/industry_report_builder.py` |
| **b. 个股分析** | `reports/{code}_{name}_投资分析报告.html` | 复用 `stock-deep-analyzer` 的 `run.py {code} --depth lite --no-browser` |
| **c. 个股打分** | `reports/传媒个股打分矩阵.html` | `python3 media_skill/media_scorer.py` |

## 组件说明

### ① citic_media.py — 中信传媒分类映射
- akshare 无中信行业分类接口（已验证），采用硬编码 + 调研校准
- 7 个二级行业：互联网媒体 / 影视动漫 / 营销服务 / 游戏 / 出版 / 广播电视 / 其他文化娱乐
- 28 只代表股，每只标注二级行业归属
- `get_citic_media_tier2()` → 7 个二纓名
- `get_all_media_stocks()` → 全部成分股
- `get_leaders_for_scoring()` → 10 只打分龙头
- `get_stock_tier2(code)` → 根据代码查二级行业

### ② fetch_industry_research.py — 行业研报批量收集
- 遍历 `get_all_media_stocks()`，逐只调 `akshare.stock_research_report_em`
- 解析：评级分布 / 2026-2027 EPS 预测 / 目标价 / 机构列表 / 近 10 份研报
- 按二级行业聚合：评级均值 / 目标价空间 / 研报覆盖密度
- DuckDuckGo 搜"传媒行业 2026 投资策略 研报"补充行业级观点
- 输出 `data/industry_research.json`

### ③ tier2_logic.py — 7 二级行业投资逻辑框架
- 每个二级行业一张逻辑卡：行业规模 / 核心逻辑 / AI 受益度 / 催化剂 / 风险 / 估值水位 / 资金关注度 / 权重建议
- `get_tier2_logic(tier2)` → 指定行业逻辑卡
- `get_weights(tier2)` → 7 维打分权重（按行业定制）

### ④ industry_report_builder.py — 行业研究报告生成器
- 组装 citic_media + industry_research + tier2_logic → Bloomberg 风格 HTML
- 章节：①行业概览 ②二级行业对比矩阵 ③各二级行业投资逻辑 ④研报观点汇总 ⑤龙头个股矩阵

### ⑤ media_scorer.py — 个股打分框架
- 7 维模型：AI 受益度 / 业绩兑现度 / 估值水位 / 资金关注度 / 催化剂密度 / 护城河 / 政策友好度
- 总分 = Σ(维度分 × 权重) × 10 → 0-100
- 权重按二级行业定制（来自 tier2_logic.json）
- 市场基调调整项 ±5（来自 market_context.json）
- 输出 SVG 雷达图 + 排名矩阵 HTML
- `media_scorer.py --ticker 002027` → 单只打分
- `media_scorer.py` → 全部 10 只龙头打分矩阵

## 工作流

```
Step 1: 行业研报收集
  fetch_industry_research.py → data/industry_research.json

Step 2: 行业报告生成
  industry_report_builder.py → reports/传媒行业研究报告.html

Step 3: 个股深度分析（复用 stock-deep-analyzer）
  run.py {code} --depth lite --no-browser → full-report-standalone.html
  注入"传媒行业视角"段（tier2_logic + scoring 数据）

Step 4: 个股打分
  media_scorer.py → data/scoring_matrix.json + reports/传媒个股打分矩阵.html
```

## 数据来源

- **研报**：akshare `stock_research_report_em`（东财研报）
- **行业策略**：DuckDuckGo 搜索
- **个股深度**：复用 `stock-deep-analyzer` skill（22 维 + 52 评委 + DCF/Comps/LBO）
- **行业分类**：中信一级行业（硬编码 + 调研校准）

## 目录结构

```
media-industry-analyzer/
├── SKILL.md                           ← 本文件
├── README.md
├── index.html                         ← GitHub Pages 首页
├── media_skill/
│   ├── citic_media.py
│   ├── fetch_industry_research.py
│   ├── tier2_logic.py
│   ├── industry_report_builder.py
│   └── media_scorer.py
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
