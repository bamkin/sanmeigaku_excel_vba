"""陰占：年干支・月干支・日干支と二十八元（蔵干）。docs/60 §1〜§4。"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from .constants import BRANCHES, MONTH_BRANCH, STEMS, ZOKAN, kanshi, kanshi_number
from .setsu import setsu_date

DAY_BASE = dt.date(1930, 6, 1)  # 壬午
DAY_BASE_NUMBER = 19

# 五虎遁：年干 → 寅月の月干
GOKOTON = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚",
           "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}


@dataclass
class Pillar:
    number: int
    stem: str
    branch: str
    zokan: list[dict] = field(default_factory=list)  # [{"stem","days","kind","selected"}]

    @property
    def kanshi(self) -> str:
        return self.stem + self.branch

    @property
    def selected_zokan(self) -> str:
        return next(z["stem"] for z in self.zokan if z["selected"])

    @property
    def all_zokan(self) -> list[str]:
        return [z["stem"] for z in self.zokan]


def year_number(year: int) -> int:
    return (year - 4) % 60 + 1


def _pillar(n: int) -> Pillar:
    ks = kanshi(n)
    return Pillar(n, ks[0], ks[1])


def day_number(d: dt.date) -> int:
    days = (d - DAY_BASE).days
    return (DAY_BASE_NUMBER - 1 + days) % 60 + 1


def month_number(year_stem: str, month: int) -> int:
    """年干と暦月（2=寅月 … 1=丑月）から月干支番号。"""
    base = kanshi_number(GOKOTON[year_stem], "寅")
    offset = (month - 2) % 12
    return (base - 1 + offset) % 60 + 1


def _assign_zokan(branch: str, d: int | None) -> list[dict]:
    """d=None は前月扱い（本元固定）。"""
    table = ZOKAN[branch]
    kinds = ["初元", "中元", "本元"][-len(table):] if len(table) < 3 else ["初元", "中元", "本元"]
    if len(table) == 1:
        kinds = ["本元"]
    elif len(table) == 2:
        kinds = ["初元", "本元"]
    sel = len(table) - 1  # 本元
    if d is not None:
        acc = 0
        for i, (_, days) in enumerate(table):
            if days is None:
                sel = i
                break
            acc += days
            if d <= acc:
                sel = i
                break
    return [{"stem": s, "days": days, "kind": k, "selected": (i == sel)}
            for i, ((s, days), k) in enumerate(zip(table, kinds))]


def compute_pillars(birth: dt.date) -> dict:
    """年・月・日の干支と蔵干、節入日情報を返す。"""
    # 年
    risshun = setsu_date(birth.year, 2)
    yr = birth.year if birth >= risshun else birth.year - 1
    year_p = _pillar(year_number(yr))

    # 月：当月節入日以後なら当月、前なら前月
    cur_setsu = setsu_date(birth.year, birth.month)
    if birth >= cur_setsu:
        m_year, m_month = birth.year, birth.month
        d = (birth - cur_setsu).days
        current_month = True
    else:
        m_month = birth.month - 1 or 12
        m_year = birth.year if birth.month != 1 else birth.year - 1
        d = None
        current_month = False
    month_p = _pillar(month_number(year_p.stem, m_month))
    assert month_p.branch == MONTH_BRANCH[m_month]

    # 日：暦日そのもの
    day_p = _pillar(day_number(birth))

    for p in (day_p, month_p, year_p):
        p.zokan = _assign_zokan(p.branch, d)

    return {
        "day": day_p, "month": month_p, "year": year_p,
        "d": d, "current_month": current_month,
        "setsu_date": cur_setsu if current_month else setsu_date(m_year, m_month),
        "setsu_month": m_month, "year_boundary": risshun,
    }
