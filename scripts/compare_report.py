"""鑑定書二通の数値比較（文字数・頻度・見出し・禁則チェック）を Markdown の表で出す。

    python scripts/compare_report.py samples/1973-11-23_実機.md docs/50_鑑定書サンプル.md

出力を samples/1973-11-23_比較.md の「数字」の表に貼る。
"""
from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from seisei.checker import LIMITED_PHRASES, check_report, count_chars  # noqa: E402

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")


def body_of(path: str) -> str:
    with open(path, encoding="utf-8") as fp:
        s = fp.read()
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    if "## はじめに" in s:
        s = s[s.index("## はじめに"):]
    if "## 申込回答" in s:
        s = s[: s.index("## 申込回答")]
    return s


def main(paths: list[str]) -> None:
    bodies = {p: body_of(p) for p in paths}
    rows = [("文字数（空白除く）", [str(count_chars(b)) for b in bodies.values()])]
    for ph in LIMITED_PHRASES:
        rows.append((f"「{ph}」", [str(b.count(ph)) for b in bodies.values()]))
    checks = {p: check_report(b, DOCS) for p, b in bodies.items()}
    rows.append(("禁則チェック", [f"エラー{sum(i.level == 'error' for i in c)}・警告{sum(i.level == 'warning' for i in c)}"
                           for c in checks.values()]))
    rows.append(("見出し", [" / ".join(l[3:] for l in b.splitlines() if l.startswith("## ")) for b in bodies.values()]))
    print("| | " + " | ".join(os.path.basename(p) for p in paths) + " |")
    print("|---|" + "---|" * len(paths))
    for label, vals in rows:
        print(f"| {label} | " + " | ".join(vals) + " |")
    print()
    for p, c in checks.items():
        for i in c:
            print(f"- {os.path.basename(p)}: {i}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["docs/50_鑑定書サンプル.md"])
