"""周辺サービスのアダプタ。環境変数で差し替え、鍵が無ければダミー（コンソール出力）。

決済   STRIPE_SECRET_KEY（＋STRIPE_WEBHOOK_SECRET）があれば Stripe Checkout、無ければダミーの決済ページ
メール RESEND_API_KEY（＋ROKUJU_MAIL_FROM）があれば Resend、無ければコンソールに出して outbox/ に保存
生成   ROKUJU_GENERATOR=dummy なら samples の実機出力を返す。それ以外は Claude API（seisei）
"""
from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from typing import Protocol

from .db import Order

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DOCS_DIR = os.environ.get("ROKUJU_DOCS", os.path.join(ROOT, "docs"))


# ---------- 決済 ----------

class Payment(Protocol):
    name: str

    def checkout_url(self, order: Order, base_url: str) -> str: ...

    def webhook_order_id(self, payload: bytes, signature: str | None) -> tuple[str, str] | None:
        """(order_id, payment_ref) を返す。対象外のイベントなら None。"""
        ...


class DummyPayment:
    name = "dummy"

    def checkout_url(self, order: Order, base_url: str) -> str:
        return f"{base_url}/pay/dummy/{order.id}"

    def webhook_order_id(self, payload: bytes, signature: str | None):
        data = json.loads(payload or b"{}")
        return (data["order_id"], "dummy") if "order_id" in data else None


class StripeCheckout:
    name = "stripe"

    def __init__(self, secret_key: str, webhook_secret: str | None):
        import stripe  # 任意依存。STRIPE_SECRET_KEY があるときだけ要る

        stripe.api_key = secret_key
        self.stripe = stripe
        self.webhook_secret = webhook_secret

    def checkout_url(self, order: Order, base_url: str) -> str:
        session = self.stripe.checkout.Session.create(
            mode="payment",
            client_reference_id=order.id,
            customer_email=order.email,
            line_items=[{"quantity": 1, "price_data": {
                "currency": "jpy", "unit_amount": order.price,
                "product_data": {"name": f"六十の風景 鑑定書（{order.plan_label}）"}}}],
            success_url=f"{base_url}/order/{order.id}?paid=1",
            cancel_url=f"{base_url}/apply?birth={order.birth}",
        )
        return session.url

    def webhook_order_id(self, payload: bytes, signature: str | None):
        if self.webhook_secret:
            event = self.stripe.Webhook.construct_event(payload, signature, self.webhook_secret)
        else:
            event = json.loads(payload)
        if event["type"] != "checkout.session.completed":
            return None
        obj = event["data"]["object"]
        return obj["client_reference_id"], obj.get("payment_intent") or obj["id"]


# ---------- メール ----------

class Mail(Protocol):
    name: str

    def send(self, to: str, subject: str, body: str, attachment: tuple[str, bytes] | None) -> str: ...


class DummyMail:
    name = "dummy"

    def __init__(self, outbox: str | None = None):
        self.outbox = outbox or os.environ.get("ROKUJU_OUTBOX", os.path.join(ROOT, "outbox"))

    def send(self, to: str, subject: str, body: str, attachment: tuple[str, bytes] | None) -> str:
        os.makedirs(self.outbox, exist_ok=True)
        saved = None
        if attachment:
            saved = os.path.join(self.outbox, attachment[0])
            with open(saved, "wb") as fp:
                fp.write(attachment[1])
        print(f"[mail:dummy] to={to} subject={subject}\n{body}\n[attachment] {saved}", file=sys.stderr)
        return saved or "console"


class ResendMail:
    name = "resend"

    def __init__(self, api_key: str, sender: str):
        self.api_key, self.sender = api_key, sender

    def send(self, to: str, subject: str, body: str, attachment: tuple[str, bytes] | None) -> str:
        import httpx

        payload: dict = {"from": self.sender, "to": [to], "subject": subject, "text": body}
        if attachment:
            payload["attachments"] = [{"filename": attachment[0],
                                       "content": base64.b64encode(attachment[1]).decode()}]
        r = httpx.post("https://api.resend.com/emails", json=payload, timeout=60,
                       headers={"Authorization": f"Bearer {self.api_key}"})
        r.raise_for_status()
        return r.json().get("id", "")


# ---------- 生成 ----------

class Generator(Protocol):
    name: str

    def generate(self, order: Order): ...   # -> seisei.generate.GenerationResult


class ClaudeGenerator:
    name = "claude"

    def generate(self, order: Order):
        from seisei.generate import generate_report

        return generate_report(order.destiny, order.answers, order.name, docs_dir=DOCS_DIR)


class DummyGenerator:
    """API を呼ばない。samples の実機出力（生）を本人の宿命表で後処理して返す。導線の確認用。"""
    name = "dummy"
    SAMPLE = os.path.join(ROOT, "samples", "1973-11-23_実機2.raw.md")

    def generate(self, order: Order):
        from seisei.generate import GenerationResult, postprocess

        with open(self.SAMPLE, encoding="utf-8") as fp:
            raw = fp.read()
        md, notes, issues = postprocess(raw, order.destiny, DOCS_DIR)
        res = GenerationResult(markdown=md, raw=raw, system_prompt="", user_message="", model="dummy",
                               stop_reason="end_turn", usage={"dummy": True}, issues=issues, notes=notes)
        res.notes.insert(0, "ダミー生成：samples/1973-11-23_実機2.raw.md を返した（API 未使用）")
        return res


# ---------- 束ね ----------

@dataclass
class Adapters:
    payment: Payment
    mail: Mail
    generator: Generator


def adapters_from_env() -> Adapters:
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    payment: Payment = StripeCheckout(stripe_key, os.environ.get("STRIPE_WEBHOOK_SECRET")) if stripe_key else DummyPayment()
    resend_key = os.environ.get("RESEND_API_KEY")
    mail: Mail = ResendMail(resend_key, os.environ.get("ROKUJU_MAIL_FROM", "六十の風景 <noreply@example.com>")) if resend_key else DummyMail()
    generator: Generator = DummyGenerator() if os.environ.get("ROKUJU_GENERATOR", "").lower() == "dummy" else ClaudeGenerator()
    return Adapters(payment, mail, generator)
