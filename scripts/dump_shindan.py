"""無料診断の文面を全部書き出す（目視確認用）。

    python scripts/dump_shindan.py   # samples/無料診断_風景一覧.md と samples/構造の一言_一覧.md
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shindan.hitokoto import all_variants  # noqa: E402
from shindan.service import closing_line, first_paragraph, landscapes, season_line  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")


def main() -> None:
    ls = landscapes()
    lines = ["# 無料診断に出る風景の一段落と結びの一行（60本）", "",
             "無料診断の出力：番号・干支・名、季節の行、最初の段落、結びの一行（カードにも使う）。", ""]
    for n in sorted(ls):
        l = ls[n]
        lines += [f"## {l.heading}", "", season_line(l), "", first_paragraph(l), "", f"結び：{closing_line(l)}", ""]
    with open(os.path.join(OUT, "無料診断_風景一覧.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    lines = ["# 構造の一言（25通り）", "",
             "数理法で最大の五行 × 八門法の型。生成せず定型で出す。", "",
             "| 最大の五行 | 型 | 一言 |", "|---|---|---|"]
    for e, t, s in all_variants():
        lines.append(f"| {e} | {t} | {s} |")
    with open(os.path.join(OUT, "構造の一言_一覧.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")
    print("wrote samples/無料診断_風景一覧.md, samples/構造の一言_一覧.md")


if __name__ == "__main__":
    main()
