"""宿命表の簡易テキスト表示（確認用）。"""
from __future__ import annotations


def render_text(d: dict, nenun_from: int | None = None, nenun_count: int = 12) -> str:
    L = []
    i = d["insen"]
    L.append(f"生年月日 {d['input']['birth']}  性別 {d['input']['sex']}")
    s = d["setsu"]
    L.append(f"節入日 {s['setsu_date']}（{'当月' if s['current_month'] else '前月'}扱い, d={s['d']}）")
    L.append("")
    L.append("【陰占】（天干／地支／蔵干：＞は陽占に使う元）")
    for k, label in (("day", "日"), ("month", "月"), ("year", "年")):
        p = i[k]
        zk = "・".join(("＞" if z["selected"] else "") + z["stem"] + f"（{z['kind']}）" for z in p["zokan"])
        L.append(f"  {label} {p['kanshi']}（{p['number']}）  {zk}")
    y = d["yosen"]
    L.append("")
    L.append("【陽占】")
    L.append(f"         {y['北']}")
    L.append(f"  {y['西']}  {y['中央']}  {y['東']}      初年 {y['初年期']} / 中年 {y['中年期']} / 晩年 {y['晩年期']}")
    L.append(f"         {y['南']}")
    t = d["tenchusatsu"]
    L.append("")
    L.append(f"【天中殺】{t['group']}（{t['role']}） {'・'.join(t['kinds']) or '宿命天中殺なし'}")
    iso = d["iso"]
    L.append("【位相】" + "  ".join(f"{k}: {'・'.join(v) or '―'}" for k, v in iso["pairs"].items())
             + ("  三柱: " + "・".join(r["name"] for r in iso["triple"]) if iso["triple"] else ""))
    sr = d["suri"]
    L.append("【数理】" + " ".join(f"{k}{v['value']}" for k, v in sr["per_stem"].items())
             + f"  合計{sr['total']}  " + " ".join(f"{k}{v}" for k, v in sr["per_element"].items())
             + f"  排気口{sr['exhaust']}")
    h = d["hachimon"]
    L.append(f"【八門】{h['type']}型（{h['max_direction']}） {h['orientation']}（北中南{h['vertical']} / 東中西{h['horizontal']}）")
    u = d["uchuban"]
    L.append(f"【宇宙盤】{u['shape']} {u['numbers']}")
    r = d["rokuju"]
    L.append(f"【風景】日 {r['day']['number']} {r['day']['kanshi']} {r['day']['name']}・{r['day']['jusei']} / "
             f"月 {r['month']['number']} {r['month']['kanshi']} {r['month']['name']} / "
             f"年 {r['year']['number']} {r['year']['kanshi']} {r['year']['name']}")

    def taiun_lines(tu, label=""):
        out = [f"【大運{label}】{'順行' if tu['forward'] else '逆行'} {tu['start_age']}歳起運（{tu['start_days']}日）"]
        for p in tu["periods"]:
            rel = " ".join(f"{k}:{'・'.join(v)}" for k, v in p["relations"].items() if v)
            out.append(f"  {p['age']:>3}歳 {p['year']} {p['kanshi']}({p['number']:>2}) {p['main_star']}・{p['sub_star']}"
                       f"{' ＞' if p['tenchusatsu'] else '  '} {rel}")
        return out

    L.append("")
    tu = d["taiun"]
    if "periods" in tu:
        L += taiun_lines(tu)
    else:
        L += taiun_lines(tu["male"], "・男") + taiun_lines(tu["female"], "・女")
    L.append("")
    L.append("【年運】")
    rows = d["nenun"]
    if nenun_from is not None:
        rows = [r for r in rows if r["year"] >= nenun_from][:nenun_count]
    else:
        rows = rows[:nenun_count]
    for p in rows:
        rel = " ".join(f"{k}:{'・'.join(v)}" for k, v in p["relations"].items() if v)
        L.append(f"  {p['year']} {p['age']:>3}歳 {p['kanshi']}({p['number']:>2}) {p['main_star']}・{p['sub_star']}"
                 f"{' ＞' if p['tenchusatsu'] else '  '} {rel}")
    return "\n".join(L)
