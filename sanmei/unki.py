"""大運・年運。docs/60 §7。"""
from __future__ import annotations

import datetime as dt
import math

from .constants import STEM_YANG, kanshi
from .iso import pair_relations, relation_labels
from .setsu import next_setsu, prev_setsu
from .stars import main_star, sub_star
from .tenchusatsu import in_group


def _round_half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def start_age(birth: dt.date, forward: bool) -> tuple[int, int]:
    """起運年齢と、その元になった日数。順行＝次の節入日まで、逆行＝前の節入日まで。÷3 四捨五入。

    0日（節入日当日生まれの逆行など）で 0 になる場合は 1 歳とする（起運年齢は 1〜10）。
    """
    days = (next_setsu(birth) - birth).days if forward else (birth - prev_setsu(birth)).days
    age = _round_half_up(days / 3)
    return max(1, age), days


def _column_relations(day_stem: str, pillars: dict, stem: str, branch: str) -> dict:
    """ある干支（大運・年運）と各柱（日・月・年）の位相。"""
    out = {}
    for key, label in (("day", "日"), ("month", "月"), ("year", "年")):
        p = pillars[key]
        rels = pair_relations(stem, branch, p.stem, p.branch)
        out[label] = relation_labels(rels)
    return out


def taiun(birth: dt.date, sex: str, pillars: dict, tcs_group: str, periods: int = 12) -> dict:
    """大運。sex は 'male'/'female'（'男'/'女' も可）。"""
    male = sex in ("male", "男", "m", "M")
    year_yang = STEM_YANG[pillars["year"].stem]
    forward = (year_yang and male) or (not year_yang and not male)
    age, days = start_age(birth, forward)
    day_stem = pillars["day"].stem
    n = pillars["month"].number
    rows = []
    for i in range(periods):
        n = (n - 1 + (1 if forward else -1)) % 60 + 1
        ks = kanshi(n)
        rows.append({
            "index": i + 1,
            "age": age + 10 * i,
            "year": birth.year + age + 10 * i,
            "number": n, "kanshi": ks,
            "main_star": main_star(day_stem, ks[0]),
            "sub_star": sub_star(day_stem, ks[1]),
            "tenchusatsu": in_group(tcs_group, ks[1]),
            "relations": _column_relations(day_stem, pillars, ks[0], ks[1]),
        })
    return {"forward": forward, "start_age": age, "start_days": days, "periods": rows}


def nenun(birth: dt.date, pillars: dict, tcs_group: str, years: int = 120) -> list[dict]:
    """年運（生年から years 年分）。"""
    day_stem = pillars["day"].stem
    rows = []
    for y in range(birth.year, birth.year + years + 1):
        n = (y - 4) % 60 + 1
        ks = kanshi(n)
        rows.append({
            "year": y, "age": y - birth.year,
            "number": n, "kanshi": ks,
            "main_star": main_star(day_stem, ks[0]),
            "sub_star": sub_star(day_stem, ks[1]),
            "tenchusatsu": in_group(tcs_group, ks[1]),
            "relations": _column_relations(day_stem, pillars, ks[0], ks[1]),
        })
    return rows
