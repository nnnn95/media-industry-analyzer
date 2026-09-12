"""③ 7 个二级行业投资逻辑框架.

每个 Tier-2 产出结构化逻辑卡：行业规模/核心逻辑/AI受益度/催化剂/风险/估值/资金/权重建议.
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DATA_FILE = _HERE.parent / "data" / "tier2_logic.json"

_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        with open(_DATA_FILE, encoding="utf-8") as f:
            _CACHE = json.load(f)
    return _CACHE


def get_all_tier2_logic() -> dict:
    """返回全部 7 个二级行业的投资逻辑卡"""
    return _load()


def get_tier2_logic(tier2: str) -> dict | None:
    """返回指定二级行业的投资逻辑卡"""
    return _load().get(tier2)


def get_weights(tier2: str) -> dict[str, float]:
    """返回指定二级行业的 7 维打分权重建议"""
    card = _load().get(tier2, {})
    return card.get("逻辑权重建议", _default_weights())


def _default_weights() -> dict[str, float]:
    """默认权重（当二级行业未配置时使用）"""
    return {
        "AI受益度": 0.15,
        "业绩兑现度": 0.20,
        "估值水位": 0.15,
        "资金关注度": 0.10,
        "催化剂密度": 0.15,
        "护城河": 0.15,
        "政策友好度": 0.10,
    }


def get_ai_benefit(tier2: str) -> str:
    """返回 AI 受益度等级"""
    card = _load().get(tier2, {})
    return card.get("AI受益度", "中")


def get_valuation_water(tier2: str) -> str:
    """返回估值水位描述"""
    card = _load().get(tier2, {})
    return card.get("估值水位", "—")


if __name__ == "__main__":
    for t2 in ["营销服务", "游戏", "出版"]:
        card = get_tier2_logic(t2)
        print(f"\n{'='*60}")
        print(f"  {t2}")
        print(f"{'='*60}")
        print(json.dumps(card, ensure_ascii=False, indent=2))
