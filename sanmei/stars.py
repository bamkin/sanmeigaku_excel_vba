"""陽占：十大主星・十二大従星。docs/60 §5。"""
from __future__ import annotations

from .constants import (BRANCHES, CONTROLS, GENERATES, STEM_ELEMENT, STEM_YANG, SUB_STAR_POINTS,
                        SUB_STARS, TENPO_START)


def main_star(day_stem: str, target_stem: str) -> str:
    de, te = STEM_ELEMENT[day_stem], STEM_ELEMENT[target_stem]
    same = STEM_YANG[day_stem] == STEM_YANG[target_stem]
    if te == de:
        return "貫索" if same else "石門"
    if GENERATES[de] == te:
        return "鳳閣" if same else "調舒"
    if CONTROLS[de] == te:
        return "禄存" if same else "司禄"
    if CONTROLS[te] == de:
        return "車騎" if same else "牽牛"
    if GENERATES[te] == de:
        return "龍高" if same else "玉堂"
    raise AssertionError  # pragma: no cover


def sub_star(day_stem: str, branch: str) -> str:
    start = BRANCHES.index(TENPO_START[day_stem])
    step = 1 if STEM_YANG[day_stem] else -1
    idx = ((BRANCHES.index(branch) - start) * step) % 12
    return SUB_STARS[idx]


def sub_star_points(day_stem: str, branch: str) -> int:
    return SUB_STAR_POINTS[sub_star(day_stem, branch)]


def yosen(day_stem: str, year_stem: str, month_stem: str,
          month_zokan: str, year_zokan: str, day_zokan: str,
          year_branch: str, month_branch: str, day_branch: str) -> dict:
    """人体星図。"""
    return {
        "北": main_star(day_stem, year_stem),
        "南": main_star(day_stem, month_stem),
        "中央": main_star(day_stem, month_zokan),
        "東": main_star(day_stem, year_zokan),
        "西": main_star(day_stem, day_zokan),
        "初年期": sub_star(day_stem, year_branch),
        "中年期": sub_star(day_stem, month_branch),
        "晩年期": sub_star(day_stem, day_branch),
    }
