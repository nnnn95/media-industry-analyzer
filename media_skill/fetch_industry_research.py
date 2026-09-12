"""② 行业研报批量收集 — 遍历传媒成分股，聚合研报数据.

复用 akshare.stock_research_report_em（单股研报接口），扩展为批量聚合。
辅以 DuckDuckGo 搜索行业级策略报告核心观点。

输出: data/industry_research.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent
_DATA_DIR = _SKILL_ROOT / "data"
sys.path.insert(0, str(_HERE))

from citic_media import get_all_media_stocks, get_citic_media_tier2  # noqa: E402

try:
    import akshare as ak  # type: ignore
    _AK_OK = True
except ImportError:
    _AK_OK = False


def _fetch_stock_reports(code: str) -> list[dict]:
    """调用 akshare.stock_research_report_em 获取单股研报"""
    if not _AK_OK:
        return []
    try:
        df = ak.stock_research_report_em(symbol=code)
        if df is None or df.empty:
            return []
        sub = df[df['股票代码'].astype(str) == code]
        if sub.empty:
            sub = df  # 有时返回不带代码列，全量用
        return sub.head(60).to_dict("records")
    except Exception as e:
        print(f"  ⚠ {code} 研报抓取失败: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
        return []


def _parse_stock_research(code: str, name: str, tier2: str, reports: list[dict]) -> dict:
    """解析单股研报数据，提取评级/EPS/目标价等"""
    ratings = Counter()
    eps_2026_vals = []
    pe_2026_vals = []
    eps_2027_vals = []
    brokers = set()
    recent = []

    for r in reports:
        rating = str(r.get("东财评级", r.get("评级", ""))).strip()
        if rating and rating not in ("nan", "-", "None", ""):
            ratings[rating] += 1
        try:
            eps_26 = float(r.get("2026-盈利预测-收益", 0) or 0)
            pe_26 = float(r.get("2026-盈利预测-市盈率", 0) or 0)
            eps_27 = float(r.get("2027-盈利预测-收益", 0) or 0)
            if eps_26 > 0:
                eps_2026_vals.append(eps_26)
            if pe_26 > 0:
                pe_2026_vals.append(pe_26)
            if eps_27 > 0:
                eps_2027_vals.append(eps_27)
        except (ValueError, TypeError):
            pass
        org = str(r.get("机构", "")).strip()
        if org and org not in ("nan", "None"):
            brokers.add(org)
        recent.append({
            "date": str(r.get("日期", ""))[:10],
            "title": str(r.get("报告名称", ""))[:80],
            "broker": org,
            "rating": rating,
        })

    rating_dist = dict(ratings)
    total = sum(rating_dist.values())
    buy_pct = 0
    if total > 0:
        buy_count = sum(v for k, v in rating_dist.items() if "买入" in k or "增持" in k)
        buy_pct = round(buy_count / total * 100, 0)

    avg_eps_2026 = round(sum(eps_2026_vals) / len(eps_2026_vals), 3) if eps_2026_vals else None
    avg_pe_2026 = round(sum(pe_2026_vals) / len(pe_2026_vals), 1) if pe_2026_vals else None
    avg_eps_2027 = round(sum(eps_2027_vals) / len(eps_2027_vals), 3) if eps_2027_vals else None

    return {
        "code": code,
        "name": name,
        "tier2": tier2,
        "report_count": len(reports),
        "broker_count": len(brokers),
        "rating_distribution": rating_dist,
        "buy_rating_pct": buy_pct,
        "consensus_eps_2026": avg_eps_2026,
        "consensus_pe_2026": avg_pe_2026,
        "consensus_eps_2027": avg_eps_2027,
        "brokers": sorted(brokers),
        "recent_reports": recent[:10],
    }


def _aggregate_by_tier2(stock_data: list[dict]) -> dict:
    """按二级行业聚合研报数据"""
    tier2_agg = defaultdict(lambda: {
        "stock_count": 0,
        "total_reports": 0,
        "total_brokers": set(),
        "buy_pct_list": [],
        "avg_pe_2026_list": [],
    })

    for s in stock_data:
        t2 = s["tier2"]
        agg = tier2_agg[t2]
        agg["stock_count"] += 1
        agg["total_reports"] += s["report_count"]
        if s["broker_count"]:
            agg["total_brokers"].update(s["brokers"])
        if s["buy_rating_pct"]:
            agg["buy_pct_list"].append(s["buy_rating_pct"])
        if s["consensus_pe_2026"]:
            agg["avg_pe_2026_list"].append(s["consensus_pe_2026"])

    result = {}
    for t2, agg in tier2_agg.items():
        buy_avg = round(sum(agg["buy_pct_list"]) / len(agg["buy_pct_list"]), 0) if agg["buy_pct_list"] else 0
        pe_avg = round(sum(agg["avg_pe_2026_list"]) / len(agg["avg_pe_2026_list"]), 1) if agg["avg_pe_2026_list"] else None
        result[t2] = {
            "stock_count": agg["stock_count"],
            "total_reports": agg["total_reports"],
            "total_brokers": len(agg["total_brokers"]),
            "avg_buy_pct": buy_avg,
            "avg_pe_2026": pe_avg,
            "report_density": round(agg["total_reports"] / max(agg["stock_count"], 1), 1),
        }
    return result


def _search_industry_strategy() -> list[dict]:
    """用 DuckDuckGo 搜行业级策略报告观点"""
    try:
        from ddgs import DDGS  # type: ignore
    except ImportError:
        return []
    queries = [
        "传媒行业 2026 投资策略 研报",
        "AI 传媒 行业研究报告 2025",
        "传媒板块 投资逻辑 2026",
    ]
    results = []
    for q in queries:
        try:
            with DDGS() as d:
                raw = list(d.text(q, region="cn-zh", safesearch="off", max_results=5))
            for r in raw:
                results.append({
                    "query": q,
                    "title": r.get("title", "")[:100],
                    "body": r.get("body", "") or r.get("snippet", ""),
                    "url": r.get("href", "") or r.get("url", ""),
                })
            time.sleep(0.5)
        except Exception:
            continue
    return results


def main() -> dict:
    """主入口：批量抓取所有传媒成分股研报，按 Tier-2 聚合"""
    print("=" * 60)
    print("  传媒行业研报批量收集")
    print("=" * 60)

    all_stocks = get_all_media_stocks()
    print(f"  成分股数: {len(all_stocks)}")
    print(f"  二级行业: {get_citic_media_tier2()}")
    print()

    stock_research = []
    for i, s in enumerate(all_stocks):
        code = s["code"]
        name = s["name"]
        tier2 = s["tier2"]
        print(f"  [{i+1}/{len(all_stocks)}] {code} {name} ({tier2})...", end=" ", flush=True)
        reports = _fetch_stock_reports(code)
        parsed = _parse_stock_research(code, name, tier2, reports)
        stock_research.append(parsed)
        print(f"研报{parsed['report_count']}份 / 机构{parsed['broker_count']}家")
        if i < len(all_stocks) - 1:
            time.sleep(0.3)  # 避免限频

    print("\n  按二级行业聚合...")
    tier2_agg = _aggregate_by_tier2(stock_research)
    for t2, agg in tier2_agg.items():
        print(f"    {t2}: {agg['stock_count']}股 / {agg['total_reports']}研报 / {agg['total_brokers']}机构 / 买入占比{agg['avg_buy_pct']}%")

    print("\n  搜索行业级策略报告...")
    strategy = _search_industry_strategy()
    print(f"    搜索结果: {len(strategy)} 条")

    result = {
        "collect_date": time.strftime("%Y-%m-%d %H:%M"),
        "classification": "中信一级行业·传媒",
        "tier2_list": get_citic_media_tier2(),
        "stock_count": len(all_stocks),
        "stock_research": stock_research,
        "tier2_aggregate": tier2_agg,
        "industry_strategy_search": strategy,
    }

    out_file = _DATA_DIR / "industry_research.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n  ✓ 输出: {out_file}")
    return result


if __name__ == "__main__":
    main()
