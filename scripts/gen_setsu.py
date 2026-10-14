"""節入日JSONの生成スクリプト（開発時のみ使用。算出層の実行時依存ではない）。

太陽黄経が 315,345,15,...,285 度に達する瞬間（視位置・地心・分点は当日）を
ephem で二分法により求め、JST の暦日を 1900〜2100 年ぶん書き出す。

使い方:
    pip install ephem
    python scripts/gen_setsu.py            # sanmei/data/setsu.json を上書き
    python scripts/gen_setsu.py --year 1974   # 1年ぶんを標準出力に表示（突合用）

生成後は干支暦の早見表と目視で突合してから採用する。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys

try:
    import ephem
except ImportError:  # pragma: no cover
    sys.exit("ephem が必要です: pip install ephem")

# 月（暦月）→ 太陽黄経。2月=立春(315) … 1月=小寒(285)
SETSU_LON = {2: 315, 3: 345, 4: 15, 5: 45, 6: 75, 7: 105, 8: 135, 9: 165, 10: 195, 11: 225, 12: 255, 1: 285}
SETSU_NAME = {2: "立春", 3: "啓蟄", 4: "清明", 5: "立夏", 6: "芒種", 7: "小暑", 8: "立秋", 9: "白露", 10: "寒露", 11: "立冬", 12: "大雪", 1: "小寒"}
JST = dt.timedelta(hours=9)


def sun_apparent_lon(d: ephem.Date) -> float:
    s = ephem.Sun(d)
    eq = ephem.Equatorial(s.g_ra, s.g_dec, epoch=d)  # 視位置・地心・当日の分点
    return math.degrees(ephem.Ecliptic(eq).lon)


def find_crossing(target: float, lo: ephem.Date, hi: ephem.Date) -> dt.datetime:
    def f(d):
        return ((sun_apparent_lon(d) - target + 180.0) % 360.0) - 180.0

    flo = f(lo)
    for _ in range(60):
        mid = (lo + hi) / 2
        fm = f(mid)
        if flo * fm <= 0:
            hi = mid
        else:
            lo, flo = mid, fm
    return ephem.Date((lo + hi) / 2).datetime()  # UTC


def setsu_for_year(year: int) -> dict[str, dict]:
    out = {}
    for month in range(1, 13):
        lo = ephem.Date((year, month, 1))
        hi = ephem.Date((year, month, 15))
        utc = find_crossing(SETSU_LON[month], lo, hi)
        jst = utc + JST
        out[f"{month:02d}"] = {
            "name": SETSU_NAME[month],
            "date": jst.strftime("%Y-%m-%d"),
            "jst": jst.strftime("%Y-%m-%d %H:%M"),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int)
    ap.add_argument("--start", type=int, default=1900)
    ap.add_argument("--end", type=int, default=2100)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "sanmei", "data", "setsu.json"))
    args = ap.parse_args()

    if args.year:
        for m, v in setsu_for_year(args.year).items():
            print(m, v["name"], v["jst"])
        return

    data = {
        "_note": "各年の12節の節入日（JST暦日）。scripts/gen_setsu.py で天文計算により生成。干支暦と突合してから採用する。",
        "_lon": SETSU_LON,
        "years": {str(y): setsu_for_year(y) for y in range(args.start, args.end + 1)},
    }
    with open(args.out, "w", encoding="utf-8") as fp:
        json.dump(data, fp, ensure_ascii=False, indent=1)
    print(f"wrote {args.out} ({args.start}-{args.end})")


if __name__ == "__main__":
    main()
