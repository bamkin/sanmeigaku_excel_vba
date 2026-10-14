"""Noto Serif JP を Google Fonts から fonts/ に取得する（PDF 用。リポジトリには入れない）。

    python scripts/get_fonts.py

古いクライアントを名乗ると、分割されていない TTF（ウェイトごとに一つ）が返る。ブラウザ向けの分割 woff2（372 ファイル、
unicode-range 付き）は WeasyPrint の埋め込みでグリフが化けるので使わない。
fonts/noto-serif-jp.css（@font-face、相対 URL）と fonts/*.ttf を置く。seihon が読む。
"""
from __future__ import annotations

import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONTS = os.path.join(ROOT, "fonts")
CSS_URL = "https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;700&display=swap"
UA = "curl/7.0"   # woff2 非対応のクライアントとして、分割なしの truetype を受け取る


def fetch(url: str) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()


def main() -> int:
    os.makedirs(FONTS, exist_ok=True)
    css = fetch(CSS_URL).decode()
    faces = re.findall(r"font-weight: (\d+);.*?src: url\((https://fonts\.gstatic\.com/[^)]+\.ttf)\)", css, re.S)
    if not faces:
        print("Google Fonts が truetype を返さなかった", file=sys.stderr)
        return 1
    out = []
    for weight, url in faces:
        name = f"NotoSerifJP-{weight}.ttf"
        dst = os.path.join(FONTS, name)
        if not os.path.exists(dst):
            with open(dst, "wb") as fp:
                fp.write(fetch(url))
        out.append(f"@font-face {{ font-family: 'Noto Serif JP'; font-style: normal; font-weight: {weight}; "
                   f"src: url({name}) format('truetype'); }}")
        print(f"{name}  {os.path.getsize(dst):,} bytes")
    with open(os.path.join(FONTS, "noto-serif-jp.css"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(out) + "\n")
    print(f"{len(faces)} faces → {FONTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
