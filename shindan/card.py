"""SNS共有用の風景カード（SVG、1200×630）。番号・干支・名・結びの一行。写真は使わない。"""
from __future__ import annotations

from xml.sax.saxutils import escape

FONT = "'Noto Serif JP', 'Hiragino Mincho ProN', 'Yu Mincho', 'IPAexMincho', serif"


def card_svg(number_kanji: str, kanshi: str, name: str, closing: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#f7f4ec"/>
  <rect x="40" y="40" width="1120" height="550" fill="none" stroke="#9fb3c8" stroke-width="2"/>
  <line x1="120" y1="300" x2="1080" y2="300" stroke="#3b5b7a" stroke-width="1.5"/>
  <text x="120" y="130" font-family="{FONT}" font-size="30" fill="#3b5b7a" letter-spacing="6">{escape(number_kanji)}　{escape(kanshi)}</text>
  <text x="120" y="240" font-family="{FONT}" font-size="80" fill="#1f1f1f" letter-spacing="4">{escape(name)}</text>
  <text x="120" y="390" font-family="{FONT}" font-size="36" fill="#1f1f1f">{escape(closing)}</text>
  <text x="1080" y="540" text-anchor="end" font-family="{FONT}" font-size="26" fill="#3b5b7a" letter-spacing="8">六十の風景</text>
</svg>
"""
