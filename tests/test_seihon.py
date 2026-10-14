"""製本：表紙の情報と HTML の組み立て、実機サンプルの PDF 化（WeasyPrint）。"""
from __future__ import annotations

import datetime as dt
import io
import os

from pypdf import PdfReader

from sanmei import compute_destiny
from seihon import cover_meta, report_html, report_pdf

ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_cover_meta():
    d = compute_destiny("1973-11-23", "male")
    m = cover_meta(d, "逆井 勤", dt.date(2026, 10, 14))
    assert (m["number_kanji"], m["kanshi"], m["name"]) == ("六十", "癸亥", "源へ帰る水")
    assert m["closing"] == "どこへ流れても、源へ帰る水です。" and m["to"] == "逆井 勤 様" and m["date"] == "2026年10月14日"
    assert cover_meta(d)["to"] == "あなたへ"


def test_report_html_sections():
    d = compute_destiny("1973-11-23", "male")
    md = "## はじめに\n\nこんにちは。\n\n## 一、源へ帰る水\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n## 申込回答\n\n（入力）"
    h = report_html(md, d, "逆井 勤", dt.date(2026, 10, 14))
    assert h.count('<section class="ch">') == 2 and "<table>" in h and "（入力）" not in h
    assert '<div class="lname">源へ帰る水</div>' in h and "逆井 勤 様" in h


def test_pdf_of_real_sample():
    d = compute_destiny("1973-11-23", "male")
    with open(os.path.join(ROOT, "samples", "1973-11-23_実機2.md"), encoding="utf-8") as fp:
        md = fp.read()
    pdf = report_pdf(md, d, "逆井 勤", dt.date(2026, 10, 14))
    assert pdf.startswith(b"%PDF")
    reader = PdfReader(io.BytesIO(pdf))
    assert 10 <= len(reader.pages) <= 40
    fonts = {v.get_object().get("/BaseFont", "") for p in reader.pages for v in (p["/Resources"].get("/Font") or {}).values()}
    assert any("Noto-Serif-JP" in str(f) or "NotoSerif" in str(f) for f in fonts), fonts
