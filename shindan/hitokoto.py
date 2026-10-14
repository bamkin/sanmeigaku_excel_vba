"""構造の一言。算出層の数理法（最大の五行）と八門法（型）から定型で作る。生成しない。

一文。文体ガイドに従い「あなた」「です」。教材・流派に触れない。
変種は 5（五行）× 5（型）＝ 25 通り。scripts/dump_shindan.py で一覧を出して目で確認する。
"""
from __future__ import annotations

from sanmei.constants import ELEMENTS

# 五行 → その力の言葉（五方向と本能：木 守備／火 伝達／土 引力／金 攻撃／水 習得）
ELEMENT_POWER = {
    "木": "自分の場所を守る力",
    "火": "伝える力",
    "土": "人とものを引き寄せる力",
    "金": "動いて切り開く力",
    "水": "学んで溜める力",
}

# 八門法の型 → 器の言葉
TYPE_VESSEL = {
    "青龍": "器は、目の前のものを見きわめて動かすときに大きくなります",
    "白虎": "器は、一人で技を磨き、向かい風を受けるほど大きくなります",
    "朱雀": "器は、人に頼られるときに大きくなります",
    "玄武": "器は、学びと表現の中で大きくなります",
    "騰蛇": "器は、あなたが真ん中にいるときに大きくなります",
}


def compose(element: str, hachimon_type: str) -> str:
    return f"あなたの中でいちばん多いのは{ELEMENT_POWER[element]}で、{TYPE_VESSEL[hachimon_type]}。"


def max_element(per_element: dict[str, int]) -> str:
    """最大の五行。同点なら木火土金水の順で先のもの。"""
    return max(ELEMENTS, key=lambda e: per_element.get(e, 0))


def hitokoto(destiny: dict) -> str:
    return compose(max_element(destiny["suri"]["per_element"]), destiny["hachimon"]["type"])


def all_variants() -> list[tuple[str, str, str]]:
    return [(e, t, compose(e, t)) for e in ELEMENTS for t in TYPE_VESSEL]
