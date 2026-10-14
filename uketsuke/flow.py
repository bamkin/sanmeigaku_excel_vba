"""導線の本体。申込 → 決済 → 生成 → 承認 → 送付。Web からも CLI からも呼べる。"""
from __future__ import annotations

import os
import secrets
import traceback

from sanmei import compute_destiny
from shindan.service import parse_birth

from . import db
from .adapters import Adapters, adapters_from_env
from .db import Order

ANSWER_KEYS = ("q1", "q2", "q3", "q4", "q5", "optional")


def create_order(*, name: str | None, birth: str, sex: str, email: str, answers: dict, plan: str) -> Order:
    d = parse_birth(birth)
    if plan not in db.PLANS:
        raise ValueError("プランが不正です")
    if not email or "@" not in email:
        raise ValueError("メールアドレスを入れてください")
    if sex not in ("male", "female", "unknown"):
        sex = "unknown"
    clean = {k: (answers.get(k) or "").strip() for k in ANSWER_KEYS}
    if not clean["q1"]:
        raise ValueError("1 の問いは必ず書いてください")
    destiny = compute_destiny(d, sex)
    order = Order(id=secrets.token_urlsafe(8), created_at=db.now(), name=(name or "").strip() or None,
                  birth=d.isoformat(), sex=sex, email=email.strip(), answers=clean, plan=plan,
                  status=db.PENDING_PAYMENT, payment_ref=None, destiny=destiny)
    db.insert_order(order)
    return order


def mark_paid(order_id: str, payment_ref: str) -> Order:
    order = db.get_order(order_id)
    if order is None:
        raise KeyError(order_id)
    if order.status == db.PENDING_PAYMENT:
        db.set_status(order_id, db.PAID, payment_ref)
    return db.get_order(order_id)


def run_generation(order_id: str, adapters: Adapters | None = None) -> dict:
    """生成して保存。失敗しても例外を外に出さず、状態を failed にして記録する。"""
    adapters = adapters or adapters_from_env()
    order = db.get_order(order_id)
    if order is None:
        raise KeyError(order_id)
    db.set_status(order_id, db.GENERATING)
    try:
        res = adapters.generator.generate(order)
    except Exception as e:  # noqa: BLE001 — 失敗は記録して承認画面に出す
        gid = db.insert_generation(order_id, model=None, effort=None, stop_reason=None, raw=None, markdown=None,
                                   issues=[], notes=[], usage={}, error=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
        db.set_status(order_id, db.FAILED)
        return {"id": gid, "ok": False}
    gid = db.insert_generation(order_id, model=res.model, effort=os.environ.get("SEISEI_EFFORT"),
                               stop_reason=res.stop_reason, raw=res.raw, markdown=res.markdown or res.raw,
                               issues=[{"level": i.level, "code": i.code, "message": i.message} for i in res.issues],
                               notes=list(res.notes), usage=res.usage)
    db.set_status(order_id, db.REVIEW if res.markdown else db.FAILED)
    return {"id": gid, "ok": bool(res.markdown)}


def regenerate(order_id: str, adapters: Adapters | None = None) -> dict:
    db.insert_approval(order_id, None, "regenerate", None, None)
    return run_generation(order_id, adapters)


def approve(order_id: str, markdown: str, note: str | None = None) -> None:
    order = db.get_order(order_id)
    if order is None:
        raise KeyError(order_id)
    gen = db.latest_generation(order_id)
    db.insert_approval(order_id, gen["id"] if gen else None, "approve", note, markdown)
    db.set_status(order_id, db.APPROVED)


def send(order_id: str, adapters: Adapters | None = None, base_url: str = "") -> dict:
    """承認済みの本文を PDF にしてメールで送る。"""
    from seihon import report_pdf

    adapters = adapters or adapters_from_env()
    order = db.get_order(order_id)
    if order is None:
        raise KeyError(order_id)
    md = db.approved_markdown(order_id)
    if md is None:
        raise ValueError("承認された本文がありません")
    pdf = report_pdf(md, order.destiny, name=order.name)
    filename = f"六十の風景_鑑定書_{order.birth}_{order.id}.pdf"
    subject = "六十の風景 — 鑑定書をお届けします"
    body = mail_body(order)
    result = adapters.mail.send(order.email, subject, body, (filename, pdf))
    db.insert_delivery(order_id, adapters.mail.name, order.email, subject, body, filename, result)
    db.insert_approval(order_id, None, "send", result, None)
    db.set_status(order_id, db.SENT)
    return {"result": result, "filename": filename, "bytes": len(pdf)}


def mail_body(order: Order) -> str:
    r = order.destiny["rokuju"]["day"]
    name = f"{order.name} 様" if order.name else "あなたへ"
    line = os.environ.get("ROKUJU_LINE_URL", "")
    parts = [
        f"{name}",
        "",
        "お申込みいただいた鑑定書ができました。PDF を添えています。",
        f"あなたの日干支の風景は、{r['kanshi']}　{r['name']}。",
        "",
        "読み終えたあと、思ったことがあれば、そのままの言葉で返してください。",
    ]
    if line:
        parts += ["", f"LINE 公式：{line}"]
    parts += ["", "六十の風景"]
    return "\n".join(parts)
