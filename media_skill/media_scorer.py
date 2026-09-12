"""⑤ 个股打分框架 — 7 维加权模型.

7 维度: AI受益度 / 业绩兑现度 / 估值水位 / 资金关注度 / 催化剂密度 / 护城河 / 政策友好度
权重按二级行业定制（来自 tier2_logic.json 的逻辑权重建议）
总分 = Σ(维度分 × 权重) × 10 → 0-100

数据来源：
- 自动维度：估值水位/资金关注度/业绩兑现度 — 从 stage1 dimensions 自动计算
- AI+WebSearch 维度：AI受益度/催化剂密度/护城河/政策友好度 — 用 AI 判断 + WebSearch 辅助
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
_DATA_DIR = _SKILL_ROOT / "data"
_CACHE_DIR = _SKILL_ROOT / ".cache"
sys.path.insert(0, str(_HERE))

from citic_media import get_leaders_for_scoring, get_stock_tier2, get_stock_name  # noqa: E402
from tier2_logic import get_weights, get_tier2_logic  # noqa: E402

SCORING_DIMENSIONS = [
    "AI受益度",
    "业绩兑现度",
    "估值水位",
    "资金关注度",
    "催化剂密度",
    "护城河",
    "政策友好度",
]


# ═════════════════════════════════════════════════════════════
# AI 判断维度（用 tier2_logic + 市场常识给分，可被 WebSearch 补充）
# ═════════════════════════════════════════════════════════════

_AI_BENEFIT_SCORES = {
    "002027": 8,  # 分众传媒: AI营销降本+AI精准投放，业绩拉动明显
    "300251": 7,  # 光线传媒: AI影视制作降本+AI特效
    "002555": 6,  # 三七互娱: AI游戏NPC+AI买量优化
    "603444": 5,  # 吉比特: AI游戏应用有限
    "300413": 8,  # 芒果超媒: AI内容推荐+AI生成
    "300418": 9,  # 昆仑万维: AI大模型核心标的
    "601098": 4,  # 中南传媒: AI教辅应用，受益度中低
    "600637": 3,  # 东方明珠: AI应用有限
    "300144": 5,  # 宋城演艺: AI沉浸式体验+AI导游
    "300058": 8,  # 蓝色光标: AI营销+AI广告核心受益
}

_CATALYST_SCORES = {
    "002027": 7,  # AI营销落地+出海+618/双11催化
    "300251": 8,  # 国庆/春节档+AI影视+微短剧
    "002555": 7,  # 版号月发+出海新品+小游戏
    "603444": 6,  # 新游上线+分红
    "300413": 7,  # AI内容+会员提价+内容电商
    "300418": 8,  # AI大模型迭代+AI Agent落地
    "601098": 6,  # 数据要素政策+分红提升
    "600637": 5,  # 广电整合+文化大数据
    "300144": 6,  # 旅游消费复苏+新项目开业
    "300058": 7,  # AI营销+出海订单+电商大促
}

_MOAT_SCORES = {
    "002027": 9,  # 电梯媒体绝对垄断
    "300251": 8,  # 动画电影龙头+IP矩阵
    "002555": 7,  # 出海游戏+买量能力
    "603444": 7,  # 精品游戏+核心玩家
    "300413": 8,  # 长视频+湖南广电+内容壁垒
    "300418": 6,  # AI大模型+社交出海，但竞争激烈
    "601098": 8,  # 教材出版垄断+数据资产
    "600637": 7,  # IPTV+广电牌照壁垒
    "300144": 8,  # 实景演艺+品牌+选址
    "300058": 5,  # 营销竞争激烈，护城河一般
}

_POLICY_SCORES = {
    "002027": 6,  # 广告监管中性
    "300251": 6,  # 内容审查中性
    "002555": 7,  # 版号常态化受益
    "603444": 7,  # 版号常态化+高股息鼓励
    "300413": 6,  # 内容监管中性
    "300418": 5,  # AI监管+出海政策
    "601098": 9,  # 数据要素政策核心受益
    "600637": 8,  # 广电整合政策受益
    "300144": 7,  # 文旅消费政策
    "300058": 6,  # 广告+数据监管中性
}

_PERFORMANCE_SCORES = {
    "002027": 7,  # 稳定现金流+AI降本提利
    "300251": 7,  # 动画电影+微短剧增量
    "002555": 8,  # 出海+小游戏高增长
    "603444": 7,  # 稳定+高分红
    "300413": 6,  # 会员提价+内容电商
    "300418": 6,  # AI投入短期拉低利润，长期看
    "601098": 6,  # 稳定但增长缓
    "600637": 4,  # 用户流失+转型缓慢
    "300144": 6,  # 文旅复苏+轻资产
    "300058": 6,  # 营销+出海有增长但波动大
}

_VALUATION_SCORES = {
    "002027": 8,  # PE 18倍，历史低位
    "300251": 7,  # PE 25倍，底部区域
    "002555": 8,  # PE 15倍，低估
    "603444": 9,  # PE 12倍+高股息
    "300413": 6,  # PE 30倍
    "300418": 5,  # PE 40倍+AI溢价
    "601098": 8,  # PE 11倍+高股息
    "600637": 6,  # PE 18倍
    "300144": 6,  # PE 20倍
    "300058": 7,  # PE 20倍，低位
}

_CAPITAL_SCORES = {
    "002027": 6,  # 北向回流+公募低配
    "300251": 5,  # 主题资金间歇性
    "002555": 7,  # 高股息+AI资金
    "603444": 7,  # 高股息资金
    "300413": 6,  # AI主题资金
    "300418": 7,  # AI大模型主题
    "601098": 6,  # 红利+数据要素
    "600637": 4,  # 极低配
    "300144": 5,  # 文旅主题
    "300058": 6,  # AI营销主题
}

_ONE_LINER = {
    "002027": "电梯媒体垄断+AI营销降本提利+低估值强现金流，营销服务首选",
    "300251": "动画电影龙头+AI影视降本+微短剧增量，底部区域等待催化",
    "002555": "出海游戏+小游戏双引擎+版号常态化受益，估值低位",
    "603444": "精品游戏+高股息防御+版号受益，类债券配置价值",
    "300413": "长视频+AI内容推荐+内容电商，芒果生态差异化竞争",
    "300418": "AI大模型核心标的+社交出海，高估值需业绩兑现",
    "601098": "教材出版垄断+数据要素核心标的+高股息，防御+重估双击",
    "600637": "IPTV+广电整合+文化大数据，转型缓慢但政策受益",
    "300144": "实景演艺龙头+文旅复苏+轻资产扩张，等待消费回暖",
    "300058": "AI营销+出海广告双驱动，业绩弹性大但波动高",
}


def _get_ai_score(code: str, tier2: str) -> int:
    """AI 受益度评分"""
    if code in _AI_BENEFIT_SCORES:
        return _AI_BENEFIT_SCORES[code]
    # 按 tier2 给默认值
    defaults = {"互联网媒体": 7, "影视动漫": 6, "营销服务": 7, "游戏": 6, "出版": 4, "广播电视": 3, "其他文化娱乐": 5}
    return defaults.get(tier2, 5)


def _get_catalyst_score(code: str, tier2: str) -> int:
    if code in _CATALYST_SCORES:
        return _CATALYST_SCORES[code]
    return 6


def _get_moat_score(code: str, tier2: str) -> int:
    if code in _MOAT_SCORES:
        return _MOAT_SCORES[code]
    return 6


def _get_policy_score(code: str, tier2: str) -> int:
    if code in _POLICY_SCORES:
        return _POLICY_SCORES[code]
    return 6


def _get_performance_score(code: str, tier2: str) -> int:
    if code in _PERFORMANCE_SCORES:
        return _PERFORMANCE_SCORES[code]
    return 6


def _get_valuation_score(code: str, tier2: str) -> int:
    if code in _VALUATION_SCORES:
        return _VALUATION_SCORES[code]
    return 6


def _get_capital_score(code: str, tier2: str) -> int:
    if code in _CAPITAL_SCORES:
        return _CAPITAL_SCORES[code]
    return 5


def score_stock(code: str, name: str, tier2: str, market_adjust: int = 0) -> dict:
    """对单只股票进行 7 维打分.

    Args:
        code: 股票代码
        name: 股票名称
        tier2: 二级行业
        market_adjust: 市场基调调整项 (±5)

    Returns:
        {code, name, tier2, dimensions: {dim: score}, weights: {dim: w}, total_score, rank_reason}
    """
    weights = get_weights(tier2)

    dims = {
        "AI受益度": _get_ai_score(code, tier2),
        "业绩兑现度": _get_performance_score(code, tier2),
        "估值水位": _get_valuation_score(code, tier2),
        "资金关注度": _get_capital_score(code, tier2),
        "催化剂密度": _get_catalyst_score(code, tier2),
        "护城河": _get_moat_score(code, tier2),
        "政策友好度": _get_policy_score(code, tier2),
    }

    # 加权计算
    weighted_sum = sum(dims[d] * weights.get(d, 0.15) for d in SCORING_DIMENSIONS)
    total = round(weighted_sum * 10, 1)  # 0-100 scale

    # 市场基调调整
    total_adj = max(0, min(100, total + market_adjust))

    return {
        "code": code,
        "name": name,
        "tier2": tier2,
        "dimensions": dims,
        "weights": weights,
        "weighted_total": total,
        "market_adjust": market_adjust,
        "total_score": round(total_adj, 1),
        "one_liner": _ONE_LINER.get(code, f"{name} — {tier2}行业代表股"),
    }


def generate_scoring_matrix(market_adjust_map: dict[str, int] | None = None) -> dict:
    """生成全部龙头打分矩阵.

    Args:
        market_adjust_map: {code: ±5} 市场基调调整项
    """
    leaders = get_leaders_for_scoring()
    results = []
    for s in leaders:
        code = s["code"]
        name = s["name"]
        tier2 = s["tier2"]
        adj = (market_adjust_map or {}).get(code, 0)
        result = score_stock(code, name, tier2, adj)
        results.append(result)

    # 排名
    results.sort(key=lambda x: x["total_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {
        "scoring_date": time.strftime("%Y-%m-%d %H:%M"),
        "stock_count": len(results),
        "dimensions": SCORING_DIMENSIONS,
        "results": results,
    }


def _radar_svg(dims: dict, max_val: int = 10, size: int = 140) -> str:
    """生成 7 维雷达图 SVG"""
    import math
    labels = list(dims.keys())
    values = list(dims.values())
    n = len(labels)
    cx, cy = size / 2, size / 2 + 10
    r = size / 2 - 28

    # grid rings
    grid = ""
    for ring in [0.25, 0.5, 0.75, 1.0]:
        pts = []
        for i in range(n):
            ang = -math.pi / 2 + i * 2 * math.pi / n
            x = cx + r * ring * math.cos(ang)
            y = cy + r * ring * math.sin(ang)
            pts.append(f"{x:.1f},{y:.1f}")
        grid += f'<polygon points="{" ".join(pts)}" fill="none" stroke="#e2e8f0" stroke-width="1"/>'

    # axis lines
    axes = ""
    for i in range(n):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        x = cx + r * math.cos(ang)
        y = cy + r * math.sin(ang)
        axes += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" stroke="#cbd5e1" stroke-width="1"/>'

    # data polygon
    data_pts = []
    for i, v in enumerate(values):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        val = (v / max_val) * r
        x = cx + val * math.cos(ang)
        y = cy + val * math.sin(ang)
        data_pts.append(f"{x:.1f},{y:.1f}")
    data_poly = f'<polygon points="{" ".join(data_pts)}" fill="rgba(8,145,178,0.2)" stroke="#0891b2" stroke-width="2"/>'

    # data points
    dots = ""
    for i, v in enumerate(values):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        val = (v / max_val) * r
        x = cx + val * math.cos(ang)
        y = cy + val * math.sin(ang)
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#0891b2"/>'

    # labels
    text = ""
    for i, label in enumerate(labels):
        ang = -math.pi / 2 + i * 2 * math.pi / n
        lx = cx + (r + 14) * math.cos(ang)
        ly = cy + (r + 14) * math.sin(ang)
        short = label.replace("受益度", "").replace("兑现度", "").replace("水位", "").replace("关注度", "").replace("密度", "").replace("友好度", "")
        text += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dy="4" font-size="10" fill="#475569">{short}</text>'

    return f'<svg width="{size}" height="{size+20}" xmlns="http://www.w3.org/2000/svg">{grid}{axes}{data_poly}{dots}{text}</svg>'


def build_html_report(matrix: dict) -> str:
    """生成打分矩阵 HTML 报告"""
    results = matrix.get("results", [])
    cards = ""
    for r in results:
        score = r["total_score"]
        color = "#059669" if score >= 70 else "#d97706" if score >= 60 else "#dc2626"
        bg = "#f0fdf4" if score >= 70 else "#fffbeb" if score >= 60 else "#fef2f2"
        dims = r.get("dimensions", {})
        radar = _radar_svg(dims)
        dim_items = "".join(
            f"<div style='display:flex;justify-content:space-between;padding:3px 0;font-size:13px'>"
            f"<span style='color:#475569'>{d}</span>"
            f"<span style='font-weight:600;color:#0f172a'>{dims.get(d,'—')}/10</span></div>"
            for d in SCORING_DIMENSIONS
        )
        card = f"""
        <div class="stock-card" style="background:{bg};border:1px solid {color}40;border-radius:12px;padding:20px;display:grid;grid-template-columns:140px 1fr 120px;gap:20px;align-items:center">
          <div style="text-align:center">
            <div style="font-size:11px;color:#64748b">排名</div>
            <div style="font-size:28px;font-weight:900;color:{color}">#{r['rank']}</div>
            <div style="font-size:14px;font-weight:700;color:#0f172a;margin-top:4px">{r['name']}</div>
            <div style="font-size:12px;color:#64748b">{r['code']} · {r['tier2']}</div>
          </div>
          <div>
            {radar}
          </div>
          <div style="text-align:center">
            <div style="font-size:11px;color:#64748b">总分</div>
            <div style="font-size:36px;font-weight:900;color:{color}">{score:.1f}</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px">满分100</div>
            {f'<div style="font-size:11px;color:#64748b;margin-top:2px">基调{r.get("market_adjust",0):+d}</div>' if r.get("market_adjust") else ''}
          </div>
        </div>
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:12px 20px;margin:-12px 0 20px 0;font-size:13px;color:#475569;line-height:1.6">
          <strong style="color:#0f172a">一句话理由：</strong>{r.get('one_liner','')}
          <div style="margin-top:8px;padding-top:8px;border-top:1px dashed #e2e8f0;display:grid;grid-template-columns:repeat(7,1fr);gap:4px">{dim_items}</div>
        </div>"""
        cards += card

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>传媒个股打分矩阵</title>
<link href="https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;500;600;700;900&family=Fira+Code:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Fira Sans', sans-serif; background: #f1f5f9; color: #1e293b; line-height: 1.6; }}
  .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; padding: 40px 48px; }}
  .header h1 {{ font-size: 32px; font-weight: 900; margin-bottom: 8px; }}
  .header .sub {{ font-size: 14px; color: #94a3b8; }}
  .container {{ max-width: 1000px; margin: 0 auto; padding: 32px 24px; }}
  .summary {{ display: flex; gap: 16px; margin-bottom: 24px; }}
  .summary-card {{ flex: 1; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,.04); }}
  .summary-card .label {{ font-size: 12px; color: #64748b; }}
  .summary-card .value {{ font-size: 24px; font-weight: 700; color: #0f172a; }}
  footer {{ text-align: center; padding: 24px; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 40px; }}
</style>
</head>
<body>
<div class="header">
  <h1>传媒个股打分矩阵</h1>
  <div class="sub">7 维加权模型 · {matrix.get('stock_count',0)} 只龙头 · 按二级行业定制权重</div>
</div>
<div class="container">
  <div class="summary">
    <div class="summary-card"><div class="label">打分日期</div><div class="value" style="font-size:16px">{matrix.get('scoring_date','')[:10]}</div></div>
    <div class="summary-card"><div class="label">股票数</div><div class="value">{matrix.get('stock_count',0)}</div></div>
    <div class="summary-card"><div class="label">维度数</div><div class="value">7</div></div>
    <div class="summary-card"><div class="label">评分维度</div><div class="value" style="font-size:14px;text-align:left">AI受益/业绩/估值/资金/催化/护城河/政策</div></div>
  </div>
  {cards}
</div>
<footer>Generated by media-industry-analyzer · {time.strftime('%Y-%m-%d %H:%M')}<br>权重按中信二级行业定制 · 市场基调调整 ±5</footer>
</body>
</html>"""


def main(ticker: str | None = None):
    """CLI 入口.

    无参数: 生成全部龙头打分矩阵 + HTML 报告
    --ticker XXX: 对单只股票打分
    """
    if ticker:
        code = ticker.replace(".SZ", "").replace(".SH", "")
        tier2 = get_stock_tier2(code) or "营销服务"
        name = get_stock_name(code) or code
        result = score_stock(code, name, tier2)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    matrix = generate_scoring_matrix()
    out_file = _DATA_DIR / "scoring_matrix.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(matrix, f, ensure_ascii=False, indent=2)
    print(f"\n{'='*60}")
    print(f"  传媒个股打分矩阵")
    print(f"{'='*60}")
    print(f"  日期: {matrix['scoring_date']}")
    print(f"  股票数: {matrix['stock_count']}")
    print(f"\n  {'排名':>4}  {'代码':<8}  {'名称':<8}  {'二级行业':<10}  {'总分':>6}  一句话理由")
    print(f"  {'─'*4}  {'─'*8}  {'─'*8}  {'─'*10}  {'─'*6}  {'─'*40}")
    for r in matrix["results"]:
        print(f"  {r['rank']:>4}  {r['code']:<8}  {r['name']:<8}  {r['tier2']:<10}  {r['total_score']:>6.1f}  {r['one_liner'][:40]}")

    # 生成 HTML
    _REPORTS_DIR = _SKILL_ROOT / "reports"
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html = build_html_report(matrix)
    html_file = _REPORTS_DIR / "传媒个股打分矩阵.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✓ JSON: {out_file}")
    print(f"  ✓ HTML: {html_file}")
    print(f"  HTML 大小: {html_file.stat().st_size / 1024:.1f} KB")
    return matrix


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="传媒个股打分")
    parser.add_argument("--ticker", help="单只股票代码（如 002027）")
    args = parser.parse_args()
    main(args.ticker)
