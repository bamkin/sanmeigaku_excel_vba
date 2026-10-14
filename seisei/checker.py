"""生成後の自動チェック（docs/00 §3.2）。

- 禁則語（教材・流派・出典・算命学の教科書・〜と書かれています）
- 六十花甲子の教材由来の呼び名（docs/45 の「教材の呼び名」列から生成）
- 構成見出しの欠落
- 文字数（完全版 6,000〜9,000 字目安）
- 文体ガイドの頻度制限（〜ではなく・つまり・だからこそ は一通に各一回まで）、感嘆符・絵文字
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache

FORBIDDEN_WORDS = ["教材", "流派", "出典", "算命学の教科書", "と書かれています", "と言われています"]
LIMITED_PHRASES = ["ではなく", "つまり", "だからこそ"]
REQUIRED_HEADINGS = ["はじめに", "一、", "二、", "三、", "四、", "五、", "六、", "七、", "八、"]
CHAR_RANGE = (6000, 9000)


@dataclass
class Issue:
    level: str  # "error" | "warning"
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level}] {self.code}: {self.message}"


@lru_cache(maxsize=4)
def textbook_names(docs_dir: str) -> tuple[str, ...]:
    """docs/45 の5列目（教材の呼び名）。"""
    path = os.path.join(docs_dir, "45_六十花甲子_照合表.md")
    names = []
    with open(path, encoding="utf-8") as fp:
        for line in fp:
            m = re.match(r"^\|\s*\d+\s*\|[^|]*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|", line)
            if m:
                names.append(m.group(1))
    return tuple(names)


def count_chars(md: str) -> int:
    return len(re.sub(r"\s", "", md))


def check_report(md: str, docs_dir: str, exempt: tuple[str, ...] = ()) -> list[Issue]:
    """exempt＝差し込んだ風景の本文など、事前執筆で承認済みの文字列。禁則チェックの対象から外す
    （文字数には含める）。"""
    issues: list[Issue] = []
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)  # HTMLコメント（注記）は対象外
    full = md
    for ex in exempt:
        if ex:
            md = md.replace(ex, "")

    for w in FORBIDDEN_WORDS:
        n = md.count(w)
        if n:
            issues.append(Issue("error", "forbidden_word", f"「{w}」が{n}回"))

    for name in textbook_names(docs_dir):
        if name in md:
            issues.append(Issue("error", "textbook_name", f"教材由来の呼び名「{name}」"))

    headings = [ln for ln in md.splitlines() if ln.startswith("#")]
    for key in REQUIRED_HEADINGS:
        if not any(key in h for h in headings):
            issues.append(Issue("error", "missing_heading", f"見出し「{key}」が無い"))

    n = count_chars(full)
    if not (CHAR_RANGE[0] <= n <= CHAR_RANGE[1]):
        issues.append(Issue("warning", "char_count", f"{n}字（目安 {CHAR_RANGE[0]}〜{CHAR_RANGE[1]}）"))

    for p in LIMITED_PHRASES:
        c = md.count(p)
        if c > 1:
            issues.append(Issue("warning", "phrase_limit", f"「{p}」が{c}回（一通に一回まで）"))

    if "！" in md or "!" in md:
        issues.append(Issue("warning", "exclamation", "感嘆符がある"))
    if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", md):
        issues.append(Issue("warning", "emoji", "絵文字がある"))

    if "[[風景" in full:
        issues.append(Issue("error", "placeholder", "風景の差し込み印が残っている"))

    return issues
