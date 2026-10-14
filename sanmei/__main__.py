"""CLI: python -m sanmei 1973-11-23 male [--json] [--years N]"""
from __future__ import annotations

import argparse
import json
import sys

from .destiny import compute_destiny
from .render import render_text


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sanmei")
    ap.add_argument("birth", help="生年月日 YYYY-MM-DD")
    ap.add_argument("sex", nargs="?", default="unknown", help="male/female（省略可）")
    ap.add_argument("--json", action="store_true", help="宿命表JSONを出力")
    ap.add_argument("--years", type=int, default=120, help="年運の年数")
    a = ap.parse_args(argv)
    d = compute_destiny(a.birth, a.sex, a.years)
    if a.json:
        json.dump(d, sys.stdout, ensure_ascii=False, indent=1)
        print()
    else:
        print(render_text(d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
