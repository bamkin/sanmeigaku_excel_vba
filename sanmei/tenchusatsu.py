"""天中殺。docs/60 §6。"""
from __future__ import annotations

from .constants import TENCHUSATSU_GROUPS, TENCHUSATSU_ROLE


def group_of(number: int) -> str:
    return TENCHUSATSU_GROUPS[(number - 1) // 10]


def in_group(group: str, branch: str) -> bool:
    return branch in group


def shukumei(group: str, year_branch: str, month_branch: str, day_branch: str) -> dict:
    y, m, d = (in_group(group, b) for b in (year_branch, month_branch, day_branch))
    kinds = []
    if y:
        kinds.append("生年天中殺")
    if m:
        kinds.append("生月天中殺")
    if y and m:
        kinds.append("二天中殺")
    if d:
        kinds.append("生日天中殺（日座天中殺）")
    if y and d:
        kinds.append("互換天中殺")
    return {"group": group, "role": TENCHUSATSU_ROLE[group],
            "year": y, "month": m, "day": d, "kinds": kinds}
