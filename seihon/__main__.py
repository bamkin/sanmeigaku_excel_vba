"""CLI。

  python -m seihon samples/1973-11-23_実機2.md --birth 1973-11-23 --sex male --name "逆井 勤" --out samples/1973-11-23_実機2.pdf
  python -m seihon ... --html out.html      # 組版の確認用に HTML も書く
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

from sanmei import compute_destiny

from .render import report_html, report_pdf


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="seihon")
    ap.add_argument("markdown")
    ap.add_argument("--birth", required=True)
    ap.add_argument("--sex", default="unknown")
    ap.add_argument("--name")
    ap.add_argument("--today", help="YYYY-MM-DD（表紙の日付）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--html", help="HTML も書き出す")
    a = ap.parse_args(argv)
    with open(a.markdown, encoding="utf-8") as fp:
        md = fp.read()
    destiny = compute_destiny(a.birth, a.sex)
    today = dt.date.fromisoformat(a.today) if a.today else None
    if a.html:
        with open(a.html, "w", encoding="utf-8") as fp:
            fp.write(report_html(md, destiny, a.name, today))
        print(f"wrote {a.html}")
    pdf = report_pdf(md, destiny, a.name, today)
    with open(a.out, "wb") as fp:
        fp.write(pdf)
    print(f"wrote {a.out} ({len(pdf):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
