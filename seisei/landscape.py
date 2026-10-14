"""六十の風景（docs/30〜39_風景_*.md）の読み込み。

各風景の本文を番号で引く。斜体の「出典の言葉」「制作メモ」「書き方の約束」節は
制作用なので取り除く（商品にもプロンプトの手本にも載せない）。
"""
from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass

KANJI_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def kanji_to_int(s: str) -> int:
    """一〜六十の漢数字を整数に。"""
    if "十" not in s:
        return KANJI_DIGITS[s]
    tens, _, ones = s.partition("十")
    return (KANJI_DIGITS[tens] if tens else 1) * 10 + (KANJI_DIGITS[ones] if ones else 0)


def int_to_kanji(n: int) -> str:
    digits = "〇一二三四五六七八九"
    if n < 10:
        return digits[n]
    tens, ones = divmod(n, 10)
    return ("" if tens == 1 else digits[tens]) + "十" + (digits[ones] if ones else "")


@dataclass
class Landscape:
    number: int
    kanshi: str
    name: str
    body: str  # 季節の行から結びの一行まで。出典の言葉は含まない

    @property
    def heading(self) -> str:
        return f"{int_to_kanji(self.number)}　{self.kanshi}　{self.name}"


_HEADING = re.compile(r"^##\s+([一二三四五六七八九十]+)\s+(\S+)\s+(.+?)\s*$")


def _strip_production_notes(lines: list[str]) -> list[str]:
    out = []
    for ln in lines:
        t = ln.strip()
        if t.startswith("*出典の言葉") or t.startswith("*制作メモ"):
            continue
        out.append(ln)
    while out and not out[-1].strip():
        out.pop()
    while out and not out[0].strip():
        out.pop(0)
    return out


def parse_landscape_file(text: str) -> tuple[str, list[Landscape]]:
    """1冊（十干ひとつ）のMarkdown → (扉ページの一段落, 風景の一覧)。"""
    lines = text.splitlines()
    intro_lines: list[str] = []
    landscapes: list[Landscape] = []
    cur: tuple[int, str, str] | None = None
    buf: list[str] = []
    skipping = False  # 「## 書き方の約束」など風景でない節

    def flush():
        if cur is not None:
            body = "\n".join(_strip_production_notes(buf))
            landscapes.append(Landscape(cur[0], cur[1], cur[2], body))

    for ln in lines:
        if ln.startswith("# "):
            continue
        if ln.startswith("## "):
            flush()
            m = _HEADING.match(ln)
            if m:
                cur = (kanji_to_int(m.group(1)), m.group(2), m.group(3))
                buf = []
                skipping = False
            else:
                cur = None
                skipping = True
            continue
        if skipping:
            continue
        if cur is None:
            intro_lines.append(ln)
        else:
            buf.append(ln)
    flush()
    intro = "\n".join(_strip_production_notes(intro_lines)).strip()
    return intro, landscapes


def load_landscapes(docs_dir: str) -> dict[int, Landscape]:
    """docs/30〜39_風景_*.md を全部読み、番号 → Landscape。"""
    out: dict[int, Landscape] = {}
    for path in sorted(glob.glob(os.path.join(docs_dir, "3[0-9]_風景_*.md"))):
        with open(path, encoding="utf-8") as fp:
            _, ls = parse_landscape_file(fp.read())
        for l in ls:
            out[l.number] = l
    return out


def load_intros(docs_dir: str) -> dict[str, str]:
    """十干 → 扉ページの一段落。"""
    out = {}
    for path in sorted(glob.glob(os.path.join(docs_dir, "3[0-9]_風景_*.md"))):
        stem = os.path.basename(path).split("_")[-1].replace(".md", "")
        with open(path, encoding="utf-8") as fp:
            intro, _ = parse_landscape_file(fp.read())
        out[stem] = intro
    return out
