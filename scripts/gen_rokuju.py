"""docs/45_六十花甲子_照合表.md から sanmei/data/rokuju.json を生成する。

出力用の列（番号・干支・風景の名・従星）だけを書き出す。
教材の呼び名の列は JSON に入れない（照合表の中だけに置く）。
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "docs", "45_六十花甲子_照合表.md")
DST = os.path.join(HERE, "..", "sanmei", "data", "rokuju.json")


def main() -> None:
    rows = {}
    with open(SRC, encoding="utf-8") as fp:
        for line in fp:
            m = re.match(r"^\|\s*(\d+)\s*\|\s*(\S+)\s*\|\s*([^|]+?)\s*\|\s*(\S+)\s*\|", line)
            if not m:
                continue
            n, kanshi, name, jusei = m.groups()
            rows[n] = {"kanshi": kanshi, "name": name, "jusei": jusei}
    assert len(rows) == 60, len(rows)
    with open(DST, "w", encoding="utf-8") as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=1)
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
