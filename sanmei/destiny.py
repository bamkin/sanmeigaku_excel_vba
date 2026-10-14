"""宿命表の組み立て。compute_destiny(birth, sex) → JSONにできる dict。"""
from __future__ import annotations

import datetime as dt
import json
import os
from functools import lru_cache

from .constants import BRANCH_MONTH, BRANCH_SEASON
from .iso import relation_labels, shukumei_iso
from .pillars import compute_pillars
from .stars import yosen
from .suri import exhaust, hachimon, suri, uchuban
from .tenchusatsu import group_of, shukumei
from .unki import nenun, taiun

_ROKUJU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rokuju.json")


@lru_cache(maxsize=1)
def rokuju_table() -> dict:
    with open(_ROKUJU, encoding="utf-8") as fp:
        return json.load(fp)


def rokuju_entry(number: int) -> dict:
    r = rokuju_table()[str(number)]
    branch = r["kanshi"][1]
    return {"number": number, "kanshi": r["kanshi"], "name": r["name"], "jusei": r["jusei"],
            "season": BRANCH_SEASON[branch], "month": BRANCH_MONTH[branch]}


def _pillar_dict(p) -> dict:
    return {"number": p.number, "kanshi": p.kanshi, "stem": p.stem, "branch": p.branch,
            "zokan": p.zokan, "zokan_selected": p.selected_zokan}


def compute_destiny(birth: dt.date | str, sex: str = "unknown", nenun_years: int = 120) -> dict:
    if isinstance(birth, str):
        birth = dt.date.fromisoformat(birth)
    sex_norm = {"male": "male", "男": "male", "m": "male", "female": "female", "女": "female", "f": "female"}.get(
        sex, "unknown")

    pl = compute_pillars(birth)
    day, month, year = pl["day"], pl["month"], pl["year"]

    stars = yosen(day.stem, year.stem, month.stem,
                  month.selected_zokan, year.selected_zokan, day.selected_zokan,
                  year.branch, month.branch, day.branch)

    group = group_of(day.number)
    tcs = shukumei(group, year.branch, month.branch, day.branch)

    iso = shukumei_iso(day, month, year)
    iso_out = {
        "pairs": {k: relation_labels(v) for k, v in iso["pairs"].items()},
        "pairs_detail": iso["pairs"],
        "triple": iso["triple"],
        "total_score": iso["total_score"],
    }

    sr = suri(day, month, year)
    branches = [year.branch, month.branch, day.branch]
    out = {
        "input": {"birth": birth.isoformat(), "sex": sex_norm},
        "setsu": {
            "current_month": pl["current_month"],
            "setsu_date": pl["setsu_date"].isoformat(),
            "setsu_month": pl["setsu_month"],
            "d": pl["d"],
            "risshun": pl["year_boundary"].isoformat(),
        },
        "insen": {"day": _pillar_dict(day), "month": _pillar_dict(month), "year": _pillar_dict(year)},
        "yosen": stars,
        "tenchusatsu": tcs,
        "iso": iso_out,
        "suri": {**sr, "exhaust": exhaust(day.stem, branches)},
        "hachimon": hachimon(day.stem, sr["per_element"]),
        "uchuban": uchuban([day.number, month.number, year.number]),
        "rokuju": {"day": rokuju_entry(day.number), "month": rokuju_entry(month.number),
                   "year": rokuju_entry(year.number)},
    }
    if sex_norm != "unknown":
        out["taiun"] = taiun(birth, sex_norm, pl, group)
    else:
        out["taiun"] = {"male": taiun(birth, "male", pl, group), "female": taiun(birth, "female", pl, group)}
    out["nenun"] = nenun(birth, pl, group, nenun_years)
    return out
