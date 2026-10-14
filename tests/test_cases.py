"""docs/60_算出手順.md §9 のテストケース6件（＋干支暦・算出資料の例）。"""
from __future__ import annotations

import datetime as dt

import pytest

from sanmei import compute_destiny
from sanmei.pillars import day_number
from sanmei.setsu import setsu_date


def insen(d):
    i = d["insen"]
    return {k: (i[k]["kanshi"], i[k]["number"], i[k]["zokan_selected"]) for k in ("day", "month", "year")}


def yosen(d):
    y = d["yosen"]
    return [y[k] for k in ("北", "南", "中央", "東", "西")], [y[k] for k in ("初年期", "中年期", "晩年期")]


def per_stem(d):
    return {k: v["value"] for k, v in d["suri"]["per_stem"].items()}


def taiun_head(d, n=3):
    return [(p["age"], p["year"], p["kanshi"], p["tenchusatsu"]) for p in d["taiun"]["periods"][:n]]


def nenun(d, year):
    return next(r for r in d["nenun"] if r["year"] == year)


# ---------------------------------------------------------------- 1973-11-23 男
class TestSakasai19731123:
    @pytest.fixture
    def d(self):
        return compute_destiny("1973-11-23", "male")

    def test_setsu(self, d):
        assert setsu_date(1973, 11) in (dt.date(1973, 11, 7), dt.date(1973, 11, 8))
        assert d["setsu"]["current_month"] and d["setsu"]["d"] in (15, 16)

    def test_insen(self, d):
        assert insen(d) == {"day": ("癸亥", 60, "壬"), "month": ("癸亥", 60, "壬"), "year": ("癸丑", 50, "己")}

    def test_yosen(self, d):
        assert yosen(d) == (["貫索", "貫索", "石門", "車騎", "石門"], ["天南", "天将", "天将"])

    def test_tenchusatsu(self, d):
        t = d["tenchusatsu"]
        assert t["group"] == "子丑" and t["role"] == "初代運"
        assert t["kinds"] == ["生年天中殺"]

    def test_iso(self, d):
        assert d["iso"]["pairs"] == {"日−月": ["律音", "自刑"], "月−年": [], "日−年": []}

    def test_taiun(self, d):
        tu = d["taiun"]
        assert tu["forward"] is False and tu["start_age"] == 5
        ks = [p["kanshi"] for p in tu["periods"]]
        assert ks == ["壬戌", "辛酉", "庚申", "己未", "戊午", "丁巳", "丙辰", "乙卯", "甲寅", "癸丑", "壬子", "辛亥"]
        assert [p["age"] for p in tu["periods"]][:3] == [5, 15, 25]
        assert [p["kanshi"] for p in tu["periods"] if p["tenchusatsu"]] == ["癸丑", "壬子"]
        p35 = tu["periods"][3]
        assert (p35["main_star"], p35["sub_star"]) == ("車騎", "天庫")
        assert p35["relations"] == {"日": ["半会"], "月": ["半会"], "年": ["天剋地冲", "庫気刑"]}
        p55 = tu["periods"][5]
        assert (p55["main_star"], p55["sub_star"]) == ("禄存", "天報")
        assert p55["relations"] == {"日": ["天剋地冲"], "月": ["天剋地冲"], "年": ["半会"]}

    def test_suri(self, d):
        assert per_stem(d) == {"甲": 56, "己": 11, "辛": 20, "壬": 60, "癸": 136}
        assert d["suri"]["total"] == 283
        assert d["suri"]["per_element"] == {"木": 56, "火": 0, "土": 11, "金": 20, "水": 196}
        assert d["suri"]["exhaust"] == 11.3

    def test_hachimon(self, d):
        h = d["hachimon"]
        assert h["type"] == "騰蛇" and h["max_direction"] == "中央"
        assert h["orientation"] == "順型" and (h["vertical"], h["horizontal"]) == (272, 207)

    def test_uchuban(self, d):
        assert d["uchuban"] == {"numbers": [60, 60, 50], "shape": "直線"}

    def test_rokuju(self, d):
        r = d["rokuju"]
        assert (r["day"]["number"], r["day"]["name"], r["day"]["jusei"], r["day"]["season"]) == (60, "源へ帰る水", "天将", "初冬")
        assert r["year"]["name"] == "凍らない水"

    def test_nenun(self, d):
        y = nenun(d, 2026)
        assert (y["kanshi"], y["main_star"], y["sub_star"]) == ("丙午", "司禄", "天馳")
        assert y["relations"] == {"日": [], "月": [], "年": ["南方害"]}
        y = nenun(d, 2027)
        assert (y["kanshi"], y["main_star"], y["sub_star"]) == ("丁未", "禄存", "天庫")
        assert y["relations"] == {"日": ["半会"], "月": ["半会"], "年": ["天剋地冲", "庫気刑"]}
        y = nenun(d, 2028)
        assert (y["kanshi"], y["main_star"], y["sub_star"]) == ("戊申", "牽牛", "天極")
        assert y["relations"] == {"日": ["西方害"], "月": ["西方害"], "年": []}
        assert nenun(d, 2032)["tenchusatsu"] and nenun(d, 2033)["tenchusatsu"] and not nenun(d, 2034)["tenchusatsu"]
        assert nenun(d, 2033)["relations"]["年"] == ["律音"]


# ---------------------------------------------------------------- 1974-01-15 女／男
class Test19740115:
    @pytest.fixture
    def f(self):
        return compute_destiny("1974-01-15", "female")

    @pytest.fixture
    def m(self):
        return compute_destiny("1974-01-15", "male")

    def test_setsu(self, f):
        assert setsu_date(1974, 1) == dt.date(1974, 1, 6)
        assert f["setsu"]["d"] == 9

    def test_insen(self, f):
        assert insen(f) == {"day": ("丙辰", 53, "乙"), "month": ("乙丑", 2, "癸"), "year": ("癸丑", 50, "癸")}

    def test_yosen(self, f):
        assert yosen(f) == (["牽牛", "玉堂", "牽牛", "牽牛", "玉堂"], ["天印", "天印", "天南"])

    def test_tenchusatsu(self, f):
        t = f["tenchusatsu"]
        assert t["group"] == "子丑" and t["month"] and t["year"] and "二天中殺" in t["kinds"]

    def test_iso(self, f):
        assert f["iso"]["pairs"] == {"日−月": ["破"], "月−年": ["比和"], "日−年": ["破"]}

    def test_suri(self, f):
        assert per_stem(f) == {"乙": 52, "丙": 22, "戊": 22, "己": 36, "辛": 34, "癸": 104}
        assert f["suri"]["total"] == 270

    def test_hachimon(self, f):
        pos = {k: v["value"] for k, v in f["hachimon"]["positions"].items()}
        assert pos == {"北": 52, "南": 58, "東": 34, "西": 104, "中央": 22}

    def test_taiun(self, f, m):
        assert f["taiun"]["forward"] and f["taiun"]["start_age"] == 7
        assert taiun_head(f, 2) == [(7, 1981, "丙寅", False), (17, 1991, "丁卯", False)]
        assert not m["taiun"]["forward"] and m["taiun"]["start_age"] == 3
        assert taiun_head(m, 3) == [(3, 1977, "甲子", True), (13, 1987, "癸亥", False), (23, 1997, "壬戌", False)]

    def test_nenun(self, f):
        assert (nenun(f, 2025)["main_star"], nenun(f, 2025)["sub_star"]) == ("玉堂", "天禄")
        assert (nenun(f, 2026)["main_star"], nenun(f, 2026)["sub_star"]) == ("貫索", "天将")
        y = nenun(f, 2027)
        assert (y["main_star"], y["sub_star"]) == ("石門", "天堂")
        # アプリ出力で確認済み：日は無し、月に冲＋庫気刑、年に天剋地冲＋庫気刑
        assert y["relations"]["年"] == ["天剋地冲", "庫気刑"]
        assert y["relations"]["月"] == ["冲", "庫気刑"]


# ---------------------------------------------------------------- 1974-01-10 女／男
class Test19740110:
    @pytest.fixture
    def f(self):
        return compute_destiny("1974-01-10", "female")

    @pytest.fixture
    def m(self):
        return compute_destiny("1974-01-10", "male")

    def test_insen(self, f):
        assert f["setsu"]["d"] == 4
        assert insen(f) == {"day": ("辛亥", 48, "甲"), "month": ("乙丑", 2, "癸"), "year": ("癸丑", 50, "癸")}

    def test_yosen(self, f):
        assert yosen(f) == (["鳳閣", "禄存", "鳳閣", "鳳閣", "司禄"], ["天印", "天印", "天恍"])

    def test_tenchusatsu(self, f):
        assert f["tenchusatsu"]["group"] == "寅卯" and f["tenchusatsu"]["kinds"] == []

    def test_suri(self, f):
        assert per_stem(f) == {"甲": 29, "乙": 18, "己": 26, "辛": 57, "壬": 27, "癸": 96}
        assert f["suri"]["total"] == 253

    def test_taiun(self, f, m):
        assert f["taiun"]["start_age"] == 8 and taiun_head(f, 1) == [(8, 1982, "丙寅", True)]
        assert m["taiun"]["start_age"] == 1 and taiun_head(m, 1) == [(1, 1975, "甲子", False)]


# ---------------------------------------------------------------- 1962-03-10 女
class Test19620310:
    @pytest.fixture
    def d(self):
        return compute_destiny("1962-03-10", "female")

    def test_insen(self, d):
        assert setsu_date(1962, 3) == dt.date(1962, 3, 6) and d["setsu"]["d"] == 4
        assert insen(d) == {"day": ("丁未", 44, "丁"), "month": ("癸卯", 40, "乙"), "year": ("壬寅", 39, "戊")}

    def test_yosen(self, d):
        assert yosen(d) == (["牽牛", "車騎", "龍高", "調舒", "貫索"], ["天極", "天胡", "天南"])

    def test_tenchusatsu(self, d):
        t = d["tenchusatsu"]
        assert t["group"] == "寅卯" and t["year"]

    def test_suri(self, d):
        assert per_stem(d) == {"甲": 28, "乙": 58, "丙": 24, "丁": 32, "戊": 24, "己": 16, "壬": 12, "癸": 21}
        assert d["suri"]["total"] == 215

    def test_taiun(self, d):
        assert not d["taiun"]["forward"] and d["taiun"]["start_age"] == 1
        assert taiun_head(d, 1) == [(1, 1963, "壬寅", True)]


# ---------------------------------------------------------------- 1951-02-03 女
class Test19510203:
    @pytest.fixture
    def d(self):
        return compute_destiny("1951-02-03", "female")

    def test_insen(self, d):
        assert setsu_date(1951, 2) == dt.date(1951, 2, 5)
        assert not d["setsu"]["current_month"] and d["setsu"]["d"] is None
        assert insen(d) == {"day": ("甲戌", 11, "戊"), "month": ("己丑", 26, "己"), "year": ("庚寅", 27, "甲")}

    def test_yosen(self, d):
        # アプリ出力で確認済み：南 司禄（月干 己）、西 禄存（日支本元 戊）
        assert yosen(d) == (["車騎", "司禄", "司禄", "貫索", "禄存"], ["天禄", "天南", "天印"])

    def test_tenchusatsu(self, d):
        assert d["tenchusatsu"]["group"] == "申酉"

    def test_suri(self, d):
        assert per_stem(d) == {"甲": 54, "丙": 20, "丁": 13, "戊": 40, "己": 26, "庚": 14, "辛": 38, "癸": 25}
        assert d["suri"]["total"] == 230

    def test_taiun(self, d):
        assert not d["taiun"]["forward"] and d["taiun"]["start_age"] == 9 and d["taiun"]["start_days"] == 28
        assert taiun_head(d, 1) == [(9, 1960, "戊子", False)]


# ---------------------------------------------------------------- 1930-06-15（干支暦の例）
class Test19300615:
    @pytest.fixture
    def d(self):
        return compute_destiny("1930-06-15")

    def test_insen(self, d):
        assert setsu_date(1930, 6) == dt.date(1930, 6, 6) and d["setsu"]["d"] == 9
        assert insen(d) == {"day": ("丙申", 33, "戊"), "month": ("壬午", 19, "己"), "year": ("庚午", 7, "己")}

    def test_yosen(self, d):
        assert yosen(d) == (["禄存", "車騎", "調舒", "調舒", "鳳閣"], ["天将", "天将", "天胡"])


# ---------------------------------------------------------------- 日干支の基準日検算
@pytest.mark.parametrize("date,expected", [
    (dt.date(1930, 6, 1), 19), (dt.date(1973, 11, 23), 60), (dt.date(1962, 3, 10), 44),
    (dt.date(1951, 2, 3), 11), (dt.date(1974, 1, 15), 53), (dt.date(1974, 1, 10), 48),
])
def test_day_number(date, expected):
    assert day_number(date) == expected


def test_json_serializable():
    import json
    json.dumps(compute_destiny("1973-11-23", "male"), ensure_ascii=False)
