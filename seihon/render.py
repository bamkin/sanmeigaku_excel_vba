"""Markdown の鑑定書を HTML に組み、WeasyPrint で PDF にする。

表紙：番号・日干支・自前の名・風景の一行・宛名・日付。本文：章ごとに改ページ、明朝、横書き。巻末：言い換え表（第八章）。
色は墨（#1f1f1f）・薄い藍（#3b5b7a／#9fb3c8）・和紙（#f7f4ec）。写真・図版は使わない。
フォントは fonts/（scripts/get_fonts.py で取得）の Noto Serif JP。無ければ Noto Serif CJK JP → IPAexMincho → serif。
"""
from __future__ import annotations

import datetime as dt
import html
import os
import re

import markdown

from seisei.landscape import int_to_kanji, load_landscapes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FONTS_DIR = os.environ.get("ROKUJU_FONTS", os.path.join(ROOT, "fonts"))
DOCS_DIR = os.environ.get("ROKUJU_DOCS", os.path.join(ROOT, "docs"))

CSS = """
@page { size: A4; margin: 24mm 22mm 26mm;
  @top-right { content: "六十の風景"; font-family: inherit; font-size: 8.5pt; letter-spacing: .3em; color: #3b5b7a; }
  @bottom-center { content: counter(page); font-size: 9pt; color: #3b5b7a; } }
@page cover { margin: 0; @top-right { content: none; } @bottom-center { content: none; } }
html { font-family: "Noto Serif JP", "Noto Serif CJK JP", "IPAexMincho", "IPAMincho", "Hiragino Mincho ProN", serif; }
body { margin: 0; color: #1f1f1f; font-size: 10.5pt; line-height: 1.95; letter-spacing: .03em; }
.cover { page: cover; width: 210mm; height: 297mm; box-sizing: border-box; padding: 36mm 28mm; background: #f7f4ec; position: relative; }
.cover .brand { font-size: 10pt; letter-spacing: .45em; color: #3b5b7a; }
.cover .kind { margin-top: 2mm; font-size: 9pt; letter-spacing: .3em; color: #3b5b7a; }
.cover .num { margin-top: 52mm; font-size: 13pt; letter-spacing: .35em; color: #3b5b7a; }
.cover .lname { margin-top: 5mm; font-size: 32pt; letter-spacing: .14em; line-height: 1.4; font-weight: 500; }
.cover .rule { width: 36mm; height: 0; border-top: 1px solid #3b5b7a; margin: 12mm 0 10mm; }
.cover .line { font-size: 12.5pt; line-height: 2.1; }
.cover .to { position: absolute; left: 28mm; bottom: 42mm; font-size: 12pt; letter-spacing: .08em; }
.cover .date { position: absolute; left: 28mm; bottom: 32mm; font-size: 9pt; letter-spacing: .15em; color: #3b5b7a; }
section.ch { break-before: page; }
h2 { font-size: 15pt; font-weight: 500; letter-spacing: .12em; line-height: 1.5; margin: 0 0 7mm; padding-bottom: 2.5mm;
     border-bottom: 1px solid #9fb3c8; break-after: avoid; }
p { margin: 0 0 1.45em; text-align: justify; orphans: 2; widows: 2; }
blockquote { margin: 0 0 1.45em; padding: 2.5mm 5mm; border-left: 2px solid #3b5b7a; background: #f3f1ea; }
blockquote p { margin: 0; }
strong { font-weight: 700; }
ol { padding-left: 1.6em; margin: 0 0 1.45em; } ol li { margin-bottom: .7em; } ol li p { margin: 0; }
table { border-collapse: collapse; width: 100%; font-size: 9.3pt; line-height: 1.65; margin: 0 0 1.8em; break-inside: avoid; }
th, td { text-align: left; vertical-align: top; padding: 1.8mm 2.4mm; border-bottom: 1px solid #dfe5ec; }
th { color: #3b5b7a; font-weight: 500; border-bottom: 1px solid #9fb3c8; }
tr { break-inside: avoid; }
td:first-child { white-space: nowrap; }
.colophon { margin-top: 18mm; padding-top: 4mm; border-top: 1px solid #9fb3c8; font-size: 8.5pt; color: #3b5b7a; letter-spacing: .1em; }
"""


def font_css() -> str | None:
    """fonts/noto-serif-jp.css（相対 URL）。無ければ None（システムの明朝に落ちる）。"""
    path = os.path.join(FONTS_DIR, "noto-serif-jp.css")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fp:
        return fp.read()


def cover_meta(destiny: dict, name: str | None = None, today: dt.date | None = None) -> dict:
    r = destiny["rokuju"]["day"]
    l = load_landscapes(DOCS_DIR)[r["number"]]
    closing = [p.strip() for p in l.body.split("\n\n") if p.strip()][-1]
    today = today or dt.date.today()
    return {"number": r["number"], "number_kanji": int_to_kanji(r["number"]), "kanshi": r["kanshi"], "name": r["name"],
            "heading": l.heading, "closing": closing, "to": f"{name} 様" if name else "あなたへ",
            "date": f"{today.year}年{today.month}月{today.day}日", "birth": destiny["input"]["birth"]}


def _sections(md: str) -> list[tuple[str, str]]:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    if "## 申込回答" in md:
        md = md[: md.index("## 申込回答")]
    parts = re.split(r"^## (.+)$", md.strip(), flags=re.M)
    out = []
    if parts[0].strip():
        out.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1].strip()))
    return out


def report_html(md: str, destiny: dict, name: str | None = None, today: dt.date | None = None) -> str:
    m = cover_meta(destiny, name, today)
    body = []
    for heading, text in _sections(md):
        inner = markdown.markdown(text, extensions=["tables", "sane_lists"])  # sane_lists: 処方箋の 3. 4. … の連番を保つ
        # WeasyPrint は <ol start> を読まないので counter-reset で明示する
        inner = re.sub(r'<ol start="(\d+)">', lambda m: f'<ol start="{m[1]}" style="counter-reset: list-item {int(m[1]) - 1}">', inner)
        h = f"<h2>{html.escape(heading)}</h2>" if heading else ""
        body.append(f'<section class="ch">{h}{inner}</section>')
    colophon = (f'<p class="colophon">六十の風景　鑑定書　{html.escape(m["heading"])}　{html.escape(m["date"])}</p>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>六十の風景 鑑定書</title>
<style>{CSS}</style></head><body>
<div class="cover">
  <div class="brand">六十の風景</div><div class="kind">鑑定書</div>
  <div class="num">{html.escape(m['number_kanji'])}　{html.escape(m['kanshi'])}</div>
  <div class="lname">{html.escape(m['name'])}</div>
  <div class="rule"></div>
  <div class="line">{html.escape(m['closing'])}</div>
  <div class="to">{html.escape(m['to'])}</div>
  <div class="date">{html.escape(m['date'])}</div>
</div>
{''.join(body)}
{colophon}
</body></html>"""


def report_pdf(md: str, destiny: dict, name: str | None = None, today: dt.date | None = None) -> bytes:
    import weasyprint

    from weasyprint.text.fonts import FontConfiguration

    doc_html = report_html(md, destiny, name, today)
    # @font-face は FontConfiguration を HTML と CSS で共有しないと無視される
    font_config = FontConfiguration()
    sheets = []
    fc = font_css()
    if fc:
        sheets.append(weasyprint.CSS(string=fc, base_url=FONTS_DIR + os.sep, font_config=font_config))
    return weasyprint.HTML(string=doc_html, base_url=ROOT + os.sep).write_pdf(stylesheets=sheets, font_config=font_config)
