"""位相法：二柱間の融合・分離条件と、三柱の三合会局・方三位。docs/40「位相法」。"""
from __future__ import annotations

from .constants import (CHU, CONTROLS, GAI, GAI_SITE, HA, HOSANI, ISO_SCORE, JIKEI, KEI, KEI_NAME,
                        SANGO, SHIGO, STEM_ELEMENT, STEM_YANG)


def _pair_in(a: str, b: str, pairs) -> bool:
    return (a, b) in pairs or (b, a) in pairs


def _is_hankai(a: str, b: str) -> bool:
    return a != b and any(a in s and b in s for s in SANGO)


def _is_shichisatsu(a: str, b: str) -> bool:
    """七殺＝同じ陰陽で剋し合う天干の対（甲戊・戊壬・壬丙・丙庚・庚甲、乙己・己癸・癸丁・丁辛・辛乙）。

    docs/40 の列挙（6対）は部分で、鑑定書サンプルの 己未×癸丑＝天剋地冲 から
    同陰陽の相剋すべてを七殺として扱う。
    """
    if STEM_YANG[a] != STEM_YANG[b]:
        return False
    ea, eb = STEM_ELEMENT[a], STEM_ELEMENT[b]
    return CONTROLS[ea] == eb or CONTROLS[eb] == ea


def pair_relations(stem_a: str, branch_a: str, stem_b: str, branch_b: str) -> list[dict]:
    """二つの干支の位相を列挙する。各要素 {"name","score",("detail")}。

    冲と刑は重なって成立しうる（丑未＝冲＋庫気刑）。律音・納音・天剋地冲・大半会は
    地支の条件（比和・冲・半会）に天干の条件が加わった特殊変化で、基の条件に加えて返す。
    """
    rel: list[dict] = []
    a, b = branch_a, branch_b
    same_stem = stem_a == stem_b

    if a == b:
        if same_stem:
            rel.append({"name": "律音", "score": ISO_SCORE["律音"]})
        else:
            rel.append({"name": "比和", "score": ISO_SCORE["比和"]})
        if a in JIKEI:
            rel.append({"name": "刑", "kind": "自刑", "score": ISO_SCORE["刑"]})
    if _is_hankai(a, b):
        if same_stem:
            rel.append({"name": "大半会", "score": ISO_SCORE["大半会"]})
        else:
            rel.append({"name": "半会", "score": ISO_SCORE["半会"]})
    if _pair_in(a, b, SHIGO):
        rel.append({"name": "支合", "score": ISO_SCORE["支合"]})
    if _pair_in(a, b, CHU):
        if _is_shichisatsu(stem_a, stem_b):
            rel.append({"name": "天剋地冲", "score": ISO_SCORE["天剋地冲"]})
        elif same_stem:
            rel.append({"name": "納音", "score": ISO_SCORE["納音"]})
        else:
            rel.append({"name": "冲", "score": ISO_SCORE["冲"]})
    if _pair_in(a, b, GAI):
        direction, site = GAI_SITE[frozenset((a, b))]
        rel.append({"name": "害", "direction": direction, "site": site, "score": ISO_SCORE["害"]})
    for pair, kind in KEI:
        if {a, b} == set(pair):
            rel.append({"name": "刑", "kind": KEI_NAME[kind], "score": ISO_SCORE["刑"]})
    if _pair_in(a, b, HA):
        rel.append({"name": "破", "score": ISO_SCORE["破"]})
    return rel


def relation_labels(rels: list[dict]) -> list[str]:
    out = []
    for r in rels:
        if r["name"] == "刑":
            out.append(r["kind"])
        elif r["name"] == "害":
            out.append(f"{r['direction']}害")
        else:
            out.append(r["name"])
    return out


def triple_relations(stems: tuple[str, str, str], branches: tuple[str, str, str]) -> list[dict]:
    """三柱（日・月・年）そろって成立する条件。

    大三合会局は教材に定義が見当たらないため、三合会局が成立しかつ三つの天干が
    同じ場合として扱う（要確認）。
    """
    out = []
    bs = set(branches)
    for s in SANGO:
        if bs == set(s):
            if len(set(stems)) == 1:
                out.append({"name": "大三合会局", "score": ISO_SCORE["大三合会局"]})
            else:
                out.append({"name": "三合会局", "score": ISO_SCORE["三合会局"]})
    for s in HOSANI:
        if bs == set(s):
            out.append({"name": "方三位", "score": ISO_SCORE["方三位"]})
    return out


def shukumei_iso(day, month, year) -> dict:
    """宿命内の位相（日−月、月−年、日−年）と三柱の特殊変化。"""
    pairs = {
        "日−月": pair_relations(day.stem, day.branch, month.stem, month.branch),
        "月−年": pair_relations(month.stem, month.branch, year.stem, year.branch),
        "日−年": pair_relations(day.stem, day.branch, year.stem, year.branch),
    }
    triple = triple_relations((day.stem, month.stem, year.stem), (day.branch, month.branch, year.branch))
    total = sum(r["score"] for rs in pairs.values() for r in rs) + sum(r["score"] for r in triple)
    return {"pairs": pairs, "triple": triple, "total_score": total}
