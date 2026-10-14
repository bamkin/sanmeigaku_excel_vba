"""無料診断の本体。生年月日 → 表示に使う辞書。"""
from __future__ import annotations

import datetime as dt
import os
from functools import lru_cache

from sanmei import compute_destiny
from sanmei.setsu import year_range
from seisei.landscape import Landscape, int_to_kanji, load_landscapes

from .hitokoto import hitokoto

DOCS_DIR = os.environ.get("ROKUJU_DOCS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs"))


@lru_cache(maxsize=1)
def landscapes() -> dict[int, Landscape]:
    return load_landscapes(DOCS_DIR)


def paragraphs(l: Landscape) -> list[str]:
    return [p.strip() for p in l.body.split("\n\n") if p.strip()]


def first_paragraph(l: Landscape) -> str:
    """季節行の次の段落。"""
    ps = paragraphs(l)
    return ps[1] if len(ps) > 1 else ps[0]


def season_line(l: Landscape) -> str:
    return paragraphs(l)[0]


def closing_line(l: Landscape) -> str:
    """結びの一行（最後の段落）。"""
    return paragraphs(l)[-1]


def parse_birth(text: str) -> dt.date:
    try:
        d = dt.date.fromisoformat(text.strip())
    except ValueError as e:
        raise ValueError("生年月日は 1973-11-23 の形で入れてください") from e
    lo, hi = year_range()
    if not (lo <= d.year <= hi):
        raise ValueError(f"{lo}年から{hi}年のあいだの生年月日に対応しています")
    return d


def free_diagnosis(birth: str | dt.date, sex: str = "unknown") -> dict:
    d = parse_birth(birth) if isinstance(birth, str) else birth
    destiny = compute_destiny(d, sex, nenun_years=0)
    n = destiny["rokuju"]["day"]["number"]
    l = landscapes()[n]
    return {
        "birth": d.isoformat(),
        "number": n,
        "number_kanji": int_to_kanji(n),
        "kanshi": l.kanshi,
        "name": l.name,
        "heading": l.heading,
        "season": destiny["rokuju"]["day"]["season"],
        "season_line": season_line(l),
        "paragraph": first_paragraph(l),
        "closing": closing_line(l),
        "hitokoto": hitokoto(destiny),
        "card_path": f"/card/{n}.svg",
        "share_text": f"六十の風景　{l.heading}　{closing_line(l)}",
    }


def card_data(number: int) -> dict:
    l = landscapes()[number]
    return {"number": number, "number_kanji": int_to_kanji(number), "kanshi": l.kanshi, "name": l.name,
            "heading": l.heading, "closing": closing_line(l)}
