"""早見表の総当たり検証（docs/60 §5）。"""
from __future__ import annotations

from sanmei.constants import BRANCHES, STEMS, TENCHUSATSU_GROUPS, kanshi, kanshi_number
from sanmei.stars import main_star, sub_star
from sanmei.tenchusatsu import group_of

MAIN_TABLE = """
甲 甲 乙 丙 丁 戊 己 庚 辛 壬 癸
乙 乙 甲 丁 丙 己 戊 辛 庚 癸 壬
丙 丙 丁 戊 己 庚 辛 壬 癸 甲 乙
丁 丁 丙 己 戊 辛 庚 癸 壬 乙 甲
戊 戊 己 庚 辛 壬 癸 甲 乙 丙 丁
己 己 戊 辛 庚 癸 壬 乙 甲 丁 丙
庚 庚 辛 壬 癸 甲 乙 丙 丁 戊 己
辛 辛 庚 癸 壬 乙 甲 丁 丙 己 戊
壬 壬 癸 甲 乙 丙 丁 戊 己 庚 辛
癸 癸 壬 乙 甲 丁 丙 己 戊 辛 庚
"""
MAIN_STARS = ["貫索", "石門", "鳳閣", "調舒", "禄存", "司禄", "車騎", "牽牛", "龍高", "玉堂"]

SUB_TABLE = """
甲 酉 戌 亥 子 丑 寅 卯 辰 巳 午 未 申
乙 申 未 午 巳 辰 卯 寅 丑 子 亥 戌 酉
丙 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
丁 亥 戌 酉 申 未 午 巳 辰 卯 寅 丑 子
戊 子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
己 亥 戌 酉 申 未 午 巳 辰 卯 寅 丑 子
庚 卯 辰 巳 午 未 申 酉 戌 亥 子 丑 寅
辛 寅 丑 子 亥 戌 酉 申 未 午 巳 辰 卯
壬 午 未 申 酉 戌 亥 子 丑 寅 卯 辰 巳
癸 巳 辰 卯 寅 丑 子 亥 戌 酉 申 未 午
"""
SUB_STARS = ["天報", "天印", "天貴", "天恍", "天南", "天禄", "天将", "天堂", "天胡", "天極", "天庫", "天馳"]


def test_main_star_table():
    for line in MAIN_TABLE.strip().splitlines():
        day, *targets = line.split()
        for star, t in zip(MAIN_STARS, targets):
            assert main_star(day, t) == star, (day, t)


def test_sub_star_table():
    for line in SUB_TABLE.strip().splitlines():
        day, *branches = line.split()
        for star, b in zip(SUB_STARS, branches):
            assert sub_star(day, b) == star, (day, b)


def test_kanshi_roundtrip():
    assert kanshi(1) == "甲子" and kanshi(60) == "癸亥" and kanshi(19) == "壬午"
    for n in range(1, 61):
        assert kanshi_number(kanshi(n)[0], kanshi(n)[1]) == n


def test_tenchusatsu_groups():
    assert [group_of(n) for n in (1, 10, 11, 20, 21, 30, 31, 40, 41, 50, 51, 60)] == [
        g for g in TENCHUSATSU_GROUPS for _ in (0, 1)]
