"""① 中信传媒分类映射 — 硬编码 7 个二级行业 + 代表股.

akshare 无中信行业分类接口（已验证仅有东财/同花顺），故采用硬编码+调研校准。
"""
from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DATA_FILE = _HERE.parent / "data" / "citic_media_constituents.json"

_CACHE: dict | None = None


def _load() -> dict:
    global _CACHE
    if _CACHE is None:
        with open(_DATA_FILE, encoding="utf-8") as f:
            _CACHE = json.load(f)
    return _CACHE


def get_citic_media_tier2() -> list[str]:
    """返回传媒行业 7 个二级行业名"""
    return _load()["tier2_list"]


def get_constituents(tier2: str | None = None) -> list[dict]:
    """返回成分股列表，可按二级行业过滤.

    每项: {code, name, tier2, note}
    """
    data = _load()
    stocks = data["constituents"]
    if tier2:
        return [s for s in stocks if s["tier2"] == tier2]
    return stocks


def get_all_media_stocks() -> list[dict]:
    """返回全部代表股（约 30 只）"""
    return _load()["constituents"]


def get_leaders_for_scoring() -> list[dict]:
    """返回打分用龙头股清单（约 10 只，每二级行业 1-2 只）"""
    return _load()["leaders_for_scoring"]


def get_stock_tier2(code: str) -> str | None:
    """根据股票代码返回二级行业名"""
    for s in _load()["constituents"]:
        if s["code"] == code:
            return s["tier2"]
    return None


def get_stock_name(code: str) -> str | None:
    """根据股票代码返回名称"""
    for s in _load()["constituents"]:
        if s["code"] == code:
            return s["name"]
    return None


if __name__ == "__main__":
    import sys
    print(f"中信传媒二级行业: {get_citic_media_tier2()}")
    print(f"总成分股数: {len(get_all_media_stocks())}")
    print(f"打分龙头数: {len(get_leaders_for_scoring())}")
    if len(sys.argv) > 1:
        code = sys.argv[1]
        t2 = get_stock_tier2(code)
        nm = get_stock_name(code)
        print(f"{code} -> {nm} / {t2}")
