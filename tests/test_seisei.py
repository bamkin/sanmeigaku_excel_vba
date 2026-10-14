"""生成層：風景の読み込み・プロンプト組み立て・禁則チェック（APIは呼ばない）。"""
from __future__ import annotations

import datetime as dt
import json
import os

from sanmei import compute_destiny
from seisei.checker import check_report, textbook_names
from seisei.landscape import int_to_kanji, kanji_to_int, load_landscapes
from seisei.prompt import build_system_prompt, build_user_message, insert_landscapes

DOCS = os.path.join(os.path.dirname(__file__), "..", "docs")


def test_kanji_numbers():
    assert [kanji_to_int(s) for s in ("一", "十", "十一", "二十", "二十一", "六十")] == [1, 10, 11, 20, 21, 60]
    for n in range(1, 61):
        assert kanji_to_int(int_to_kanji(n)) == n


def test_landscapes_complete_and_clean():
    ls = load_landscapes(DOCS)
    assert sorted(ls) == list(range(1, 61))
    with open(os.path.join(os.path.dirname(__file__), "..", "sanmei", "data", "rokuju.json"), encoding="utf-8") as fp:
        rokuju = json.load(fp)
    for n, l in ls.items():
        assert l.kanshi == rokuju[str(n)]["kanshi"]
        assert l.name == rokuju[str(n)]["name"]
        assert "出典の言葉" not in l.body and "制作メモ" not in l.body and "書き方の約束" not in l.body
        assert l.body.strip() and "それが、あなたの風景です" in l.body
        for tb in textbook_names(DOCS):
            # 既知の衝突：丁卯「香木」・甲辰「常緑の木」は風景本文に普通名詞として出る（逆井に判断を仰ぐ）
            if (n, tb) in ((4, "香木"), (41, "常緑の木")):
                continue
            assert tb not in l.body, (n, tb)
    assert ls[60].heading == "六十　癸亥　源へ帰る水"


def test_system_prompt_sections():
    sp = build_system_prompt(DOCS)
    for key in ("# 文体ガイド", "# 学理リファレンス", "鑑定書の構成（固定）", "# 出力形式", "# 手本", "### 六十　癸亥　源へ帰る水"):
        assert key in sp
    assert "出典の言葉" not in sp.split("# 六十の風景")[1]
    for tb in textbook_names(DOCS):
        if tb in ("香木", "常緑の木"):
            continue
        assert tb not in sp, tb


def test_user_message_and_insertion():
    d = compute_destiny("1973-11-23", "male")
    answers = {"q1": "帝王として陽転し自分が源という生き方をしたい。", "q4": "一人で抱える。"}
    ls = load_landscapes(DOCS)
    um = build_user_message(d, answers, "逆井 勤", dt.date(2026, 10, 14), ls)
    assert "逆井 勤 様" in um and "今年＝2026年" in um and "帝王として陽転し" in um
    assert "六十　癸亥　源へ帰る水" in um and "2027" in um

    md = "## はじめに\n\nx\n\n## 一、源へ帰る水\n\n[[風景:日]]\n\n続き\n"
    out, notes = insert_landscapes(md, d, ls)
    assert "[[風景" not in out and "初冬、十一月。" in out and notes == []
    md2 = "## はじめに\n\nx\n\n## 一、源へ帰る水\n\n続き\n"
    out2, notes2 = insert_landscapes(md2, d, ls)
    assert "初冬、十一月。" in out2 and notes2


def test_checker_on_sample():
    with open(os.path.join(DOCS, "50_鑑定書サンプル.md"), encoding="utf-8") as fp:
        md = fp.read().split("---", 1)[1].split("## 申込回答")[0]
    issues = check_report(md, DOCS)
    codes = {i.code for i in issues}
    assert "forbidden_word" not in codes and "textbook_name" not in codes
    assert "missing_heading" in codes  # サンプルは第八章（言い換え表）が無い
    assert any(i.code == "phrase_limit" for i in issues)  # 「ではなく」が多い（サンプル冒頭の注記どおり）


def test_checker_exempt():
    md = "## はじめに\n常緑の木です。\n" + "\n".join(f"## {k}、x" for k in "一二三四五六七八")
    assert any(i.code == "textbook_name" for i in check_report(md, DOCS))
    assert not any(i.code == "textbook_name" for i in check_report(md, DOCS, exempt=("常緑の木です。",)))


def test_checker_flags():
    md = "## はじめに\n教材によれば溝渠の水です！つまり、つまり。"
    issues = check_report(md, DOCS)
    codes = [i.code for i in issues]
    assert "forbidden_word" in codes and "textbook_name" in codes and "exclamation" in codes
    assert "phrase_limit" in codes and "missing_heading" in codes and "char_count" in codes
