"""数理法・八門法・宇宙盤。docs/60 §8、docs/40。"""
from __future__ import annotations

from collections import Counter

from .constants import CONTROLS, ELEMENTS, GENERATES, STEM_ELEMENT, STEMS
from .stars import sub_star_points


def suri(day, month, year) -> dict:
    """数理法。材料＝天干3つ＋全蔵干。十干ごとに（3地支の従星点数の合計）×出現回数。"""
    branches = [day.branch, month.branch, year.branch]
    counts = Counter([day.stem, month.stem, year.stem] + day.all_zokan + month.all_zokan + year.all_zokan)
    per_stem = {}
    for s in STEMS:
        if counts[s]:
            base = sum(sub_star_points(s, b) for b in branches)
            per_stem[s] = {"count": counts[s], "base": base, "value": base * counts[s]}
    per_element = {e: 0 for e in ELEMENTS}
    for s, v in per_stem.items():
        per_element[STEM_ELEMENT[s]] += v["value"]
    total = sum(per_element.values())
    return {"per_stem": per_stem, "per_element": per_element, "total": total}


def exhaust(day_stem: str, branches: list[str]) -> float:
    """排気口＝従星3つの点数の平均。"""
    return round(sum(sub_star_points(day_stem, b) for b in branches) / 3, 1)


def hachimon(day_stem: str, per_element: dict) -> dict:
    """八門法：日干中心の五方向配置と型。"""
    de = STEM_ELEMENT[day_stem]
    north = next(e for e in ELEMENTS if GENERATES[e] == de)
    south = GENERATES[de]
    east = CONTROLS[de]
    west = next(e for e in ELEMENTS if CONTROLS[e] == de)
    pos = {"北": (north, per_element[north]), "南": (south, per_element[south]),
           "東": (east, per_element[east]), "西": (west, per_element[west]), "中央": (de, per_element[de])}
    values = {k: v[1] for k, v in pos.items()}
    types = {"東": "青龍", "西": "白虎", "南": "朱雀", "北": "玄武", "中央": "騰蛇"}
    max_dir = max(values, key=lambda k: values[k])
    vertical = values["北"] + values["中央"] + values["南"]
    horizontal = values["東"] + values["中央"] + values["西"]
    return {
        "positions": {k: {"element": v[0], "value": v[1]} for k, v in pos.items()},
        "max_direction": max_dir, "type": types[max_dir],
        "vertical": vertical, "horizontal": horizontal,
        "orientation": "順型" if vertical > horizontal else ("逆型" if horizontal > vertical else "同等"),
    }


def uchuban(numbers: list[int]) -> dict:
    """宇宙盤：三干支の番号から行動領域の形。"""
    distinct = len(set(numbers))
    shape = {3: "三角", 2: "直線", 1: "点"}[distinct]
    return {"numbers": numbers, "shape": shape}
