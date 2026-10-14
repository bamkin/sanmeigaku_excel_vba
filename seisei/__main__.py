"""CLI。

  python -m seisei --birth 1973-11-23 --sex male --answers samples/1973-11-23_申込回答.json --name "逆井 勤" --out out.md
  python -m seisei ... --dry-run          # APIを呼ばず、プロンプトを out.system.md / out.user.md に書く
  python -m seisei --check docs/50_鑑定書サンプル.md   # 既存の鑑定書に禁則チェックだけ通す
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

from sanmei import compute_destiny

from .checker import check_report
from .generate import DEFAULT_EFFORT, DEFAULT_MODEL, build_request, generate_report, postprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOCS = os.path.join(HERE, "..", "docs")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="seisei")
    ap.add_argument("--birth")
    ap.add_argument("--sex", default="unknown")
    ap.add_argument("--answers", help="申込回答JSON（q1〜q5, optional）")
    ap.add_argument("--name")
    ap.add_argument("--out", default="鑑定書.md")
    ap.add_argument("--docs", default=DEFAULT_DOCS)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--effort", default=DEFAULT_EFFORT)
    ap.add_argument("--today", help="YYYY-MM-DD（年運の「今年」）")
    ap.add_argument("--dry-run", action="store_true", help="APIを呼ばずプロンプトだけ書き出す")
    ap.add_argument("--check", help="既存のMarkdownに禁則チェックを通す")
    ap.add_argument("--postprocess", help="モデル出力（生）のMarkdownに風景差し込みとチェックを通す")
    a = ap.parse_args(argv)

    if a.check:
        with open(a.check, encoding="utf-8") as fp:
            md = fp.read()
        issues = check_report(md, a.docs)
        for i in issues:
            print(i)
        print(f"{len([i for i in issues if i.level == 'error'])} errors, "
              f"{len([i for i in issues if i.level == 'warning'])} warnings")
        return 1 if any(i.level == "error" for i in issues) else 0

    if not a.birth:
        ap.error("--birth が必要")
    destiny = compute_destiny(a.birth, a.sex)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()

    if a.postprocess:
        with open(a.postprocess, encoding="utf-8") as fp:
            raw = fp.read()
        md, notes, issues = postprocess(raw, destiny, a.docs)
        with open(a.out, "w", encoding="utf-8") as fp:
            fp.write(md)
        for n in notes:
            print("note:", n)
        for i in issues:
            print(i)
        print(f"wrote {a.out}")
        return 0

    answers = {}
    if a.answers:
        with open(a.answers, encoding="utf-8") as fp:
            answers = json.load(fp)

    if a.dry_run:
        system, user = build_request(destiny, answers, a.name, a.docs, today)
        base = os.path.splitext(a.out)[0]
        with open(base + ".system.md", "w", encoding="utf-8") as fp:
            fp.write(system)
        with open(base + ".user.md", "w", encoding="utf-8") as fp:
            fp.write(user)
        print(f"system prompt {len(system)} 字 → {base}.system.md")
        print(f"user message  {len(user)} 字 → {base}.user.md")
        return 0

    res = generate_report(destiny, answers, a.name, docs_dir=a.docs, model=a.model, effort=a.effort, today=today)
    with open(a.out, "w", encoding="utf-8") as fp:
        fp.write(res.markdown or res.raw)
    base = os.path.splitext(a.out)[0]
    with open(base + ".raw.md", "w", encoding="utf-8") as fp:
        fp.write(res.raw)
    print(f"model={res.model} stop={res.stop_reason} usage={res.usage}")
    for n in res.notes:
        print("note:", n)
    for i in res.issues:
        print(i)
    print(f"wrote {a.out}" + ("" if res.ok else "  （エラーあり）"))
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
