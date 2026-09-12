"""④ 行业研究报告生成器 — 组装数据 + 逻辑卡 → HTML 报告.

组装 citic_media + fetch_industry_research + tier2_logic → Bloomberg 风格 HTML 报告。
章节：①行业概览 ②二级行业对比矩阵 ③各二级行业投资逻辑 ④研报观点汇总 ⑤龙头个股矩阵
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
_DATA_DIR = _SKILL_ROOT / "data"
_REPORTS_DIR = _SKILL_ROOT / "reports"
sys.path.insert(0, str(_HERE))

from citic_media import get_all_media_stocks, get_citic_media_tier2, get_leaders_for_scoring  # noqa: E402
from tier2_logic import get_all_tier2_logic  # noqa: E402


def _load_research_data() -> dict:
    """加载 industry_research.json"""
    f = _DATA_DIR / "industry_research.json"
    if f.exists():
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _load_scoring_data() -> dict:
    """加载 scoring_matrix.json（用于龙头矩阵）"""
    f = _DATA_DIR / "scoring_matrix.json"
    if f.exists():
        with open(f, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def _ai_benefit_badge(level: str) -> str:
    """AI 受益度徽章"""
    colors = {"高": "#34d399", "中高": "#22d3ee", "中": "#facc15", "低": "#94a3b8"}
    color = colors.get(level, "#94a3b8")
    return f'<span style="background:{color}20;color:{color};padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600">{level}</span>'


def _tier2_logic_card(tier2: str, logic: dict) -> str:
    """生成单个二级行业投资逻辑卡"""
    reps = "、".join(logic.get("代表股", []))
    core_logic = "".join(f"<li>{l}</li>" for l in logic.get("核心投资逻辑", []))
    catalysts = "、".join(logic.get("关键催化剂", []))
    risks = "、".join(logic.get("关键风险", []))
    weights = logic.get("逻辑权重建议", {})
    weight_items = "".join(f"<span style='display:inline-block;margin:2px 4px;background:#e2e8f0;padding:2px 8px;border-radius:4px;font-size:12px'>{k} {v:.0%}</span>" for k, v in weights.items())

    return f"""
    <div class="tier2-card" style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.04)">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
        <h3 style="margin:0;font-size:20px;color:#0f172a">{tier2}</h3>
        <div>AI受益度 {_ai_benefit_badge(logic.get("AI受益度","中"))}</div>
      </div>
      <div style="font-size:14px;color:#475569;margin-bottom:12px"><strong>代表股：</strong>{reps}</div>
      <div style="font-size:14px;color:#475569;margin-bottom:12px"><strong>行业规模与增速：</strong>{logic.get("行业规模与增速","")}</div>
      <div style="margin-bottom:12px">
        <strong style="font-size:14px;color:#0f172a">核心投资逻辑：</strong>
        <ul style="margin:6px 0 0 20px;padding:0;font-size:14px;color:#1e293b;line-height:1.8">{core_logic}</ul>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
        <div style="background:#f0fdf4;padding:10px 14px;border-radius:8px;border-left:3px solid #34d399">
          <div style="font-size:12px;color:#059669;font-weight:600;margin-bottom:4px">关键催化剂</div>
          <div style="font-size:13px;color:#1e293b">{catalysts}</div>
        </div>
        <div style="background:#fef2f2;padding:10px 14px;border-radius:8px;border-left:3px solid #f87171">
          <div style="font-size:12px;color:#dc2626;font-weight:600;margin-bottom:4px">关键风险</div>
          <div style="font-size:13px;color:#1e293b">{risks}</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px">
        <div style="background:#f8fafc;padding:8px 12px;border-radius:8px">
          <div style="font-size:11px;color:#64748b">估值水位</div>
          <div style="font-size:13px;color:#0f172a;font-weight:500">{logic.get("估值水位","—")}</div>
        </div>
        <div style="background:#f8fafc;padding:8px 12px;border-radius:8px">
          <div style="font-size:11px;color:#64748b">资金关注度</div>
          <div style="font-size:13px;color:#0f172a;font-weight:500">{logic.get("资金关注度","—")}</div>
        </div>
        <div style="background:#f8fafc;padding:8px 12px;border-radius:8px">
          <div style="font-size:11px;color:#64748b">打分权重</div>
          <div style="font-size:12px;color:#1e293b">{weight_items}</div>
        </div>
      </div>
    </div>"""


def _tier2_comparison_table(research: dict, logic: dict) -> str:
    """二级行业对比矩阵表"""
    tier2_agg = research.get("tier2_aggregate", {})
    rows = ""
    for t2 in get_citic_media_tier2():
        agg = tier2_agg.get(t2, {})
        lg = logic.get(t2, {})
        rows += f"""
        <tr>
          <td style="font-weight:600;color:#0f172a">{t2}</td>
          <td style="text-align:center">{agg.get('stock_count',0)}</td>
          <td style="text-align:center">{agg.get('total_reports',0)}</td>
          <td style="text-align:center">{agg.get('total_brokers',0)}</td>
          <td style="text-align:center">{agg.get('avg_buy_pct',0)}%</td>
          <td style="text-align:center">{agg.get('avg_pe_2026','—')}</td>
          <td style="text-align:center">{_ai_benefit_badge(lg.get('AI受益度','中'))}</td>
          <td style="font-size:12px">{lg.get('估值水位','—')[:20]}</td>
        </tr>"""

    return f"""
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)">
      <thead>
        <tr style="background:#1e293b;color:#f8fafc">
          <th style="padding:10px 12px;text-align:left">二级行业</th>
          <th style="padding:10px 12px;text-align:center">成分股</th>
          <th style="padding:10px 12px;text-align:center">研报数</th>
          <th style="padding:10px 12px;text-align:center">覆盖机构</th>
          <th style="padding:10px 12px;text-align:center">买入占比</th>
          <th style="padding:10px 12px;text-align:center">26年PE</th>
          <th style="padding:10px 12px;text-align:center">AI受益度</th>
          <th style="padding:10px 12px;text-align:left">估值水位</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def _research_summary(research: dict) -> str:
    """研报观点汇总"""
    stock_research = research.get("stock_research", [])
    # 取研报数最多的前10只
    top10 = sorted(stock_research, key=lambda x: x.get("report_count", 0), reverse=True)[:10]
    rows = ""
    for s in top10:
        ratings = s.get("rating_distribution", {})
        rating_str = " / ".join(f"{k}{v}" for k, v in list(ratings.items())[:3]) if ratings else "—"
        rows += f"""
        <tr>
          <td style="font-weight:600">{s['name']}</td>
          <td style="font-size:12px;color:#64748b">{s['code']}</td>
          <td style="text-align:center">{s['tier2']}</td>
          <td style="text-align:center;font-weight:600;color:#059669">{s.get('report_count',0)}</td>
          <td style="text-align:center">{s.get('broker_count',0)}</td>
          <td style="text-align:center">{s.get('buy_rating_pct',0)}%</td>
          <td style="text-align:center">{s.get('consensus_eps_2026','—')}</td>
          <td style="text-align:center">{s.get('consensus_pe_2026','—')}</td>
          <td style="font-size:12px">{rating_str}</td>
        </tr>"""

    return f"""
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)">
      <thead>
        <tr style="background:#1e293b;color:#f8fafc">
          <th style="padding:10px 12px;text-align:left">名称</th>
          <th style="padding:10px 12px;text-align:center">代码</th>
          <th style="padding:10px 12px;text-align:center">二级行业</th>
          <th style="padding:10px 12px;text-align:center">研报数</th>
          <th style="padding:10px 12px;text-align:center">机构数</th>
          <th style="padding:10px 12px;text-align:center">买入占比</th>
          <th style="padding:10px 12px;text-align:center">26年EPS</th>
          <th style="padding:10px 12px;text-align:center">26年PE</th>
          <th style="padding:10px 12px;text-align:left">评级分布</th>
        </tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def _leader_matrix(scoring: dict) -> str:
    """龙头个股矩阵"""
    results = scoring.get("results", [])
    if not results:
        # 无打分数据时用 leaders 清单
        leaders = get_leaders_for_scoring()
        rows = ""
        for l in leaders:
            rows += f"""
            <tr>
              <td style="font-weight:600">{l['name']}</td>
              <td style="font-size:12px;color:#64748b">{l['code']}</td>
              <td style="text-align:center">{l['tier2']}</td>
              <td colspan="6" style="text-align:center;color:#94a3b8">打分待运行</td>
            </tr>"""
    else:
        rows = ""
        for r in results:
            dims = r.get("dimensions", {})
            dim_cells = "".join(f"<td style='text-align:center;font-weight:600'>{dims.get(d,'—')}</td>" for d in ["AI受益度","业绩兑现度","估值水位","资金关注度","催化剂密度","护城河","政策友好度"])
            score = r["total_score"]
            color = "#059669" if score >= 70 else "#d97706" if score >= 60 else "#dc2626"
            rows += f"""
            <tr>
              <td style="font-weight:600">{r['name']}</td>
              <td style="font-size:12px;color:#64748b">{r['code']}</td>
              <td style="text-align:center">{r['tier2']}</td>
              {dim_cells}
              <td style="text-align:center;font-size:16px;font-weight:700;color:{color}">{score:.1f}</td>
            </tr>"""

    headers = ["名称", "代码", "二级行业", "AI受益", "业绩", "估值", "资金", "催化", "护城河", "政策", "总分"]
    header_row = "".join(f"<th style='padding:10px 8px;text-align:{'left' if i<3 else 'center'}'>{h}</th>" for i, h in enumerate(headers))

    return f"""
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.04)">
      <thead>
        <tr style="background:#1e293b;color:#f8fafc">{header_row}</tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    </div>"""


def _strategy_search_section(research: dict) -> str:
    """行业级策略报告搜索结果"""
    strategy = research.get("industry_strategy_search", [])
    if not strategy:
        return "<p style='color:#94a3b8;text-align:center;padding:20px'>未获取到行业级策略报告搜索结果</p>"

    items = ""
    for s in strategy[:8]:
        items += f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:10px">
          <div style="font-size:14px;font-weight:600;color:#0f172a;margin-bottom:4px">{s.get('title','')[:80]}</div>
          <div style="font-size:13px;color:#475569;margin-bottom:4px;line-height:1.5">{s.get('body','')[:200]}...</div>
          <div style="font-size:11px;color:#64748b">{s.get('url','')[:80]}</div>
        </div>"""

    return f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">{items}</div>'


def build_report() -> str:
    """生成完整 HTML 报告"""
    research = _load_research_data()
    scoring = _load_scoring_data()
    logic = get_all_tier2_logic()

    collect_date = research.get("collect_date", time.strftime("%Y-%m-%d"))
    total_stocks = len(get_all_media_stocks())
    tier2_count = len(get_citic_media_tier2())
    total_reports = sum(s.get("report_count", 0) for s in research.get("stock_research", []))
    total_brokers = len(set(b for s in research.get("stock_research", []) for b in s.get("brokers", [])))

    # 逻辑卡
    logic_cards = "".join(_tier2_logic_card(t2, logic.get(t2, {})) for t2 in get_citic_media_tier2())

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>传媒行业研究报告 · 中信一级</title>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700;900&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Fira Sans', sans-serif; background: #f1f5f9; color: #1e293b; line-height: 1.6; }}
  .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; padding: 40px 48px; }}
  .header h1 {{ font-size: 32px; font-weight: 900; margin-bottom: 8px; }}
  .header .sub {{ font-size: 14px; color: #94a3b8; }}
  .header .meta {{ display: flex; gap: 24px; margin-top: 16px; }}
  .header .meta-item {{ background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 6px; }}
  .header .meta-item .label {{ font-size: 11px; color: #94a3b8; }}
  .header .meta-item .value {{ font-size: 18px; font-weight: 700; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
  .section {{ margin-bottom: 40px; }}
  .section-title {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #0891b2; display: flex; align-items: center; gap: 8px; }}
  .section-title .num {{ background: #0891b2; color: #fff; width: 28px; height: 28px; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; font-size: 14px; }}
  .card {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
  .highlight-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; }}
  .highlight {{ background: linear-gradient(135deg, #fff 0%, #f8fafc 100%); border: 1px solid #e2e8f0; border-radius: 10px; padding: 20px; border-left: 4px solid #0891b2; }}
  .highlight .label {{ font-size: 12px; color: #64748b; margin-bottom: 4px; }}
  .highlight .value {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
  .highlight .desc {{ font-size: 12px; color: #475569; margin-top: 4px; }}
  footer {{ text-align: center; padding: 24px; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 40px; }}
</style>
</head>
<body>
<div class="header">
  <h1>传媒行业研究报告</h1>
  <div class="sub">中信一级行业 · 7 个二级行业投资逻辑 + 研报观点 + 龙头矩阵</div>
  <div class="meta">
    <div class="meta-item"><div class="label">报告日期</div><div class="value">{collect_date}</div></div>
    <div class="meta-item"><div class="label">二级行业</div><div class="value">{tier2_count}</div></div>
    <div class="meta-item"><div class="label">成分股</div><div class="value">{total_stocks}</div></div>
    <div class="meta-item"><div class="label">研报聚合</div><div class="value">{total_reports}</div></div>
    <div class="meta-item"><div class="label">覆盖机构</div><div class="value">{total_brokers}</div></div>
  </div>
</div>

<div class="container">

  <!-- ① 行业概览 -->
  <div class="section">
    <div class="section-title"><span class="num">1</span>行业概览</div>
    <div class="card">
      <p style="font-size:15px;line-height:1.8;margin-bottom:20px">
        传媒行业是中信一级行业分类下涵盖<strong>互联网媒体、影视动漫、营销服务、游戏、出版、广播电视、其他文化娱乐</strong>共7个二级行业的综合性板块。
        2025-2026年传媒行业的核心主线是<strong>AI+传媒</strong>——AI视频模型(Sora/Kling)、AI营销降本、AI游戏NPC、AI内容生成等正在重塑整个内容生产链。
        叠加版号常态化、影视复苏+微短剧爆发、出版数据要素重估、营销出海、广电整合等多条线，传媒板块处于<strong>低估值+多催化</strong>的战略布局期。
      </p>
      <div class="highlight-grid">
        <div class="highlight">
          <div class="label">AI+传媒主线</div>
          <div class="value">6条</div>
          <div class="desc">AI视频/营销/游戏 + 版号常态化 + 影视复苏 + 出版数据要素 + 营销出海 + 广电整合</div>
        </div>
        <div class="highlight">
          <div class="label">估值水位</div>
          <div class="value">低位</div>
          <div class="desc">多数二级行业PE处于历史30%分位以下</div>
        </div>
        <div class="highlight">
          <div class="label">资金关注度</div>
          <div class="value">低配</div>
          <div class="desc">公募低配，北向+红利资金回流</div>
        </div>
        <div class="highlight">
          <div class="label">催化时间线</div>
          <div class="value">密集</div>
          <div class="desc">月度版号 + AI模型迭代 + 国庆/春节档 + 数据要素政策</div>
        </div>
      </div>
    </div>
  </div>

  <!-- ② 二级行业对比矩阵 -->
  <div class="section">
    <div class="section-title"><span class="num">2</span>二级行业对比矩阵</div>
    {_tier2_comparison_table(research, logic)}
  </div>

  <!-- ③ 各二级行业投资逻辑 -->
  <div class="section">
    <div class="section-title"><span class="num">3</span>各二级行业投资逻辑</div>
    {logic_cards}
  </div>

  <!-- ④ 研报观点汇总 -->
  <div class="section">
    <div class="section-title"><span class="num">4</span>研报观点汇总</div>
    <p style="font-size:13px;color:#64748b;margin-bottom:16px">数据来源：akshare stock_research_report_em · 按研报覆盖数排序</p>
    {_research_summary(research)}
  </div>

  <!-- ⑤ 行业级策略报告 -->
  <div class="section">
    <div class="section-title"><span class="num">5</span>行业级策略报告（搜索）</div>
    <p style="font-size:13px;color:#64748b;margin-bottom:16px">来源：DuckDuckGo 搜索"传媒行业 2026 投资策略 研报"</p>
    {_strategy_search_section(research)}
  </div>

  <!-- ⑥ 龙头个股矩阵 -->
  <div class="section">
    <div class="section-title"><span class="num">6</span>龙头个股矩阵</div>
    <p style="font-size:13px;color:#64748b;margin-bottom:16px">10 只龙头 7 维打分 · 详见 <a href="传媒个股打分矩阵.html" style="color:#0891b2">传媒个股打分矩阵.html</a></p>
    {_leader_matrix(scoring)}
  </div>

</div>

<footer>
  Generated by media-industry-analyzer skill · {time.strftime("%Y-%m-%d %H:%M")}<br>
  数据来源：akshare (stock_research_report_em) + DuckDuckGo + 调研校准
</footer>
</body>
</html>"""
    return html


def main():
    """生成行业研究报告 HTML"""
    print("=" * 60)
    print("  传媒行业研究报告生成")
    print("=" * 60)

    html = build_report()
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = _REPORTS_DIR / "传媒行业研究报告.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✓ 输出: {out_file}")
    print(f"  文件大小: {out_file.stat().st_size / 1024:.1f} KB")
    return out_file


if __name__ == "__main__":
    main()
