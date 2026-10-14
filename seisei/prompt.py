"""システムプロンプトと依頼メッセージの組み立て。

システムプロンプト（固定・キャッシュ対象）＝
  役割 ＋ 文体ガイド(10) ＋ 書き方の約束(29) ＋ 学理(40) ＋ 構成と禁則(00 §3.2) ＋ 出力形式 ＋ 手本(50) ＋ 六十の風景(30〜39)
依頼メッセージ（毎回変わる）＝ 宛名・生年月日・本日 ＋ 宿命表 ＋ 申込回答 ＋ 差し込む風景
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from sanmei.render import render_text

from .landscape import Landscape, load_landscapes

LANDSCAPE_PLACEHOLDER = "[[風景:{col}]]"

OUTPUT_FORMAT = """
## 出力形式（厳守）

- 出力は鑑定書の Markdown 本文だけ。前置き・後書き・説明・コードフェンスを付けない
- 見出しは次の九つを、この順で、この形で置く（二重 # ）
  - `## はじめに`
  - `## 一、{日干支の風景の名}`（例：`## 一、源へ帰る水`）
  - `## 二、あなたという構造`
  - `## 三、「{本人が書いたパターンの言葉}」の正体`
  - `## 四、あなたの時間軸`
  - `## 五、{本人の問いに答える見出し}`（例：`## 五、帝王として陽転するということ`）
  - `## 六、処方箋`
  - `## 七、羅針盤の一枚`
  - `## 八、用語の言い換え表`
- 第一章「一、」の見出しの直後に、`[[風景:日]]` という一行だけを置く。日干支の風景の本文は事前執筆したものがそこに差し込まれる。風景の本文を書き直したり要約して並べたりしない。差し込まれる本文を前提に、その続きから書く
- 月干支・年干支の風景に触れるときは、番号・干支・名を言い、像を一文か二文で引く。全文を再掲しない。必要なら `[[風景:月]]` `[[風景:年]]` の一行で差し込める
- 第二章は七つの角度の表（角度／あなたの値／意味）、第四章は年運の表、第七章は二列の表を Markdown の表で書く
- 本文は 6,000〜9,000 字（空白を除く）
- 専門用語は初出時に括弧で言い換えを添え、第八章に言い換え表を付ける
- 本日の日付を「今年」の基準にする。年運の読みは今年から始める
"""

ROLE = """あなたは「六十の風景」の鑑定書を書く書き手です。算命学の宿命表（算出済み）と申込者の回答から、本人への手紙として鑑定書を書きます。
目的は、読まれた先で本人がエンパワーメントされること。苦労を「輝くための段取りだった」と読み替え、同時に「これからどう生きるかは自分が決める」を必ず対で渡します。
以下の文体ガイド・学理・構成・禁則・手本・六十の風景に従ってください。学理は宿命表を読むための知識で、本文に学理の出典や用語の説明文を並べるためのものではありません。"""


def _read(docs_dir: str, name: str) -> str:
    with open(os.path.join(docs_dir, name), encoding="utf-8") as fp:
        return fp.read()


def _structure_and_rules(docs_dir: str) -> str:
    """docs/00 §3.2 の「鑑定書の構成（固定）」から「生成後の自動チェック」の手前まで。"""
    spec = _read(docs_dir, "00_仕様書.md")
    start = spec.index("鑑定書の構成（固定）")
    end = spec.index("生成後の自動チェック")
    text = spec[start:end].strip()
    # 仕様書の禁則に例として挙がる教材由来の呼び名は、プロンプトに入れない
    from .checker import textbook_names
    names = textbook_names(docs_dir)
    text = re.sub(r"（例：[^）]*）", lambda m: "" if any(n in m.group(0) for n in names) else m.group(0), text)
    for n in names:
        text = text.replace(n, "")
    return text


def _landscapes_block(landscapes: dict[int, Landscape]) -> str:
    parts = []
    for n in sorted(landscapes):
        l = landscapes[n]
        parts.append(f"### {l.heading}\n\n{l.body}")
    return "\n\n".join(parts)


def build_system_prompt(docs_dir: str) -> str:
    landscapes = load_landscapes(docs_dir)
    sections = [
        ROLE,
        "# 文体ガイド\n\n" + _read(docs_dir, "10_文体ガイド.md"),
        "# 六十の風景 書き方の約束（風景は差し込むので生成しない。文体の参照用）\n\n" + _read(docs_dir, "29_風景_書き方の約束.md"),
        "# 学理リファレンス\n\n" + _read(docs_dir, "40_学理リファレンス.md"),
        "# 鑑定書の構成と禁則\n\n" + _structure_and_rules(docs_dir),
        "# 出力形式\n" + OUTPUT_FORMAT,
        "# 手本：鑑定書サンプル（構成・言い切り・本人の言葉の引用・対で書く結びの型。文体は文体ガイドを優先）\n\n"
        + _read(docs_dir, "50_鑑定書サンプル.md"),
        "# 六十の風景（事前執筆・全六十本。差し込まれる本文であり、像を引く元）\n\n" + _landscapes_block(landscapes),
    ]
    return "\n\n---\n\n".join(sections)


ANSWER_LABELS = [
    ("q1", "1. 今、一番気になっていること"),
    ("q2", "2. 本当はこうしたいという方向"),
    ("q3", "3. 転機だった年"),
    ("q4", "4. 繰り返し起きている気がすること・いつもこうなるパターン"),
    ("q5", "5. 読み終えたときどうなっていたら「受けてよかった」と思うか"),
    ("optional", "任意. 今の体調や体で気になっていること"),
]


def _compact_destiny(destiny: dict, today: dt.date, years_ahead: int = 12) -> dict:
    """依頼メッセージに載せる宿命表の抜粋（JSON）。年運は今年の前年から12年。"""
    tu = destiny["taiun"]
    tu_rows = tu["periods"] if "periods" in tu else tu["male"]["periods"]
    nenun = [r for r in destiny["nenun"] if today.year - 1 <= r["year"] <= today.year + years_ahead]
    return {
        "陰占": destiny["insen"],
        "陽占": destiny["yosen"],
        "天中殺": destiny["tenchusatsu"],
        "位相": {"pairs": destiny["iso"]["pairs"], "triple": destiny["iso"]["triple"]},
        "数理": {"per_stem": {k: v["value"] for k, v in destiny["suri"]["per_stem"].items()},
               "per_element": destiny["suri"]["per_element"], "total": destiny["suri"]["total"],
               "exhaust": destiny["suri"]["exhaust"]},
        "八門": destiny["hachimon"],
        "宇宙盤": destiny["uchuban"],
        "六十花甲子": destiny["rokuju"],
        "大運": {"forward": tu.get("forward", tu.get("male", {}).get("forward")),
               "start_age": tu.get("start_age", tu.get("male", {}).get("start_age")),
               "periods": tu_rows},
        "年運": nenun,
    }


def build_user_message(destiny: dict, answers: dict, name: str | None, today: dt.date,
                       landscapes: dict[int, Landscape]) -> str:
    birth = destiny["input"]["birth"]
    sex = {"male": "男性", "female": "女性"}.get(destiny["input"]["sex"], "未記入")
    r = destiny["rokuju"]
    age = today.year - int(birth[:4])
    parts = ["# 鑑定の依頼", ""]
    parts.append(f"- 宛名：{name + ' 様' if name else '（氏名なし。宛名は「あなた」）'}")
    parts.append(f"- 生年月日：{birth}（{sex}）")
    parts.append(f"- 本日：{today.isoformat()}（今年＝{today.year}年、{age}歳）")
    parts.append("")
    parts.append("## 宿命表（テキスト）")
    parts.append("")
    parts.append("```")
    parts.append(render_text(destiny, nenun_from=today.year - 1, nenun_count=14))
    parts.append("```")
    parts.append("")
    parts.append("## 宿命表（構造データ）")
    parts.append("")
    parts.append("```json")
    parts.append(json.dumps(_compact_destiny(destiny, today), ensure_ascii=False, indent=1))
    parts.append("```")
    parts.append("")
    parts.append("## 申込回答（本人の言葉。引用はこのまま）")
    parts.append("")
    for key, label in ANSWER_LABELS:
        v = (answers.get(key) or "").strip()
        parts.append(f"{label}：{v if v else '（記入なし）'}")
    parts.append("")
    parts.append("## 差し込まれる風景（本文は生成しない。像を引く元）")
    parts.append("")
    for col, key in (("日", "day"), ("月", "month"), ("年", "year")):
        l = landscapes[r[key]["number"]]
        parts.append(f"### {col}干支　{l.heading}\n\n{l.body}\n")
    parts.append("以上を元に、鑑定書を書いてください。")
    return "\n".join(parts)


def insert_landscapes(md: str, destiny: dict, landscapes: dict[int, Landscape]) -> tuple[str, list[str]]:
    """差し込み印を風景の本文に置き換える。日の印が無ければ第一章の見出し直後に差し込む。"""
    notes: list[str] = []
    r = destiny["rokuju"]
    for col, key in (("日", "day"), ("月", "month"), ("年", "year")):
        ph = LANDSCAPE_PLACEHOLDER.format(col=col)
        l = landscapes[r[key]["number"]]
        if ph in md:
            md = md.replace(ph, l.body)
        elif col == "日":
            lines = md.splitlines()
            for i, ln in enumerate(lines):
                if ln.startswith("## 一、"):
                    lines.insert(i + 1, "\n" + l.body + "\n")
                    notes.append("日の風景の差し込み印が無かったので第一章の見出し直後に差し込んだ")
                    break
            else:
                notes.append("第一章の見出しが見つからず、日の風景を差し込めなかった")
            md = "\n".join(lines)
    return md, notes
