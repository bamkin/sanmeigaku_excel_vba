"""節入日（sanmei/data/setsu.json）の読み込みと検索。"""
from __future__ import annotations

import datetime as dt
import json
import os
from functools import lru_cache

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "setsu.json")


@lru_cache(maxsize=1)
def _load() -> dict:
    with open(_DATA, encoding="utf-8") as fp:
        return json.load(fp)["years"]


def year_range() -> tuple[int, int]:
    ys = sorted(int(y) for y in _load())
    return ys[0], ys[-1]


def setsu_date(year: int, month: int) -> dt.date:
    """その年・暦月の節入日（JST暦日）。month=2 は立春、month=1 は小寒。"""
    try:
        s = _load()[str(year)][f"{month:02d}"]["date"]
    except KeyError as e:  # pragma: no cover
        raise ValueError(f"節入日データの範囲外: {year}-{month:02d}") from e
    return dt.date.fromisoformat(s)


def setsu_name(month: int) -> str:
    return {2: "立春", 3: "啓蟄", 4: "清明", 5: "立夏", 6: "芒種", 7: "小暑", 8: "立秋",
            9: "白露", 10: "寒露", 11: "立冬", 12: "大雪", 1: "小寒"}[month]


def prev_setsu(d: dt.date) -> dt.date:
    """d 以前（当日を含む）で最も近い節入日。"""
    y, m = d.year, d.month
    for _ in range(3):
        s = setsu_date(y, m)
        if s <= d:
            return s
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    raise AssertionError  # pragma: no cover


def next_setsu(d: dt.date) -> dt.date:
    """d より後で最も近い節入日。"""
    y, m = d.year, d.month
    for _ in range(3):
        s = setsu_date(y, m)
        if s > d:
            return s
        m += 1
        if m == 13:
            m, y = 1, y + 1
    raise AssertionError  # pragma: no cover
