"""無料診断：サービス・一言・カード・Webの経路。"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from seisei.checker import FORBIDDEN_WORDS
from shindan.app import app
from shindan.hitokoto import all_variants, compose
from shindan.service import closing_line, first_paragraph, free_diagnosis, landscapes, season_line


def test_free_diagnosis_sakasai():
    r = free_diagnosis("1973-11-23")
    assert (r["number"], r["number_kanji"], r["kanshi"], r["name"]) == (60, "六十", "癸亥", "源へ帰る水")
    assert r["season"] == "初冬" and r["season_line"] == "初冬、十一月。"
    assert r["paragraph"].startswith("崐崙は、大河が")
    assert r["closing"] == "どこへ流れても、源へ帰る水です。"
    assert r["hitokoto"] == compose("水", "騰蛇")
    assert r["card_path"] == "/card/60.svg"


def test_all_landscapes_have_parts():
    for n, l in landscapes().items():
        assert season_line(l).endswith("。") and "、" in season_line(l), n
        assert len(first_paragraph(l)) > 20, n
        assert closing_line(l).endswith("。") and "\n" not in closing_line(l), n


def test_hitokoto_variants():
    vs = all_variants()
    assert len(vs) == 25 and len({s for _, _, s in vs}) == 25
    for _, _, s in vs:
        assert s.count("。") == 1 and "あなた" in s
        assert not any(w in s for w in FORBIDDEN_WORDS + ["ではなく", "つまり", "だからこそ", "！"])


@pytest.mark.parametrize("bad", ["", "1973/11/23", "1850-01-01", "2200-01-01", "abc"])
def test_invalid_birth(bad):
    with pytest.raises(ValueError):
        free_diagnosis(bad)


def test_web_routes():
    c = TestClient(app)
    assert c.get("/").status_code == 200
    r = c.get("/shindan", params={"birth": "1973-11-23"})
    assert r.status_code == 200
    assert "六十　癸亥　源へ帰る水" in r.text and "どこへ流れても、源へ帰る水です。" in r.text
    assert "問いを書いて、続きを読む" in r.text and "/card/60.svg" in r.text
    bad = c.get("/shindan", params={"birth": "1850-01-01"})
    assert bad.status_code == 400 and "1900年から" in bad.text
    svg = c.get("/card/60.svg")
    assert svg.status_code == 200 and svg.headers["content-type"].startswith("image/svg+xml")
    assert "源へ帰る水" in svg.text and "六十　癸亥" in svg.text
    assert c.get("/card/61.svg").status_code == 404
    assert c.get("/apply", params={"birth": "1973-11-23"}).status_code == 200
