"""受付：申込 → ダミー決済 → ダミー生成 → 承認 → 送付（PDF はこのテストでは差し替え）。"""
from __future__ import annotations

import base64
import os

import pytest
from fastapi.testclient import TestClient

import seihon
from shindan.app import app
from uketsuke import db, flow


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ROKUJU_DB", str(tmp_path / "t.sqlite3"))
    monkeypatch.setenv("ROKUJU_OUTBOX", str(tmp_path / "outbox"))
    monkeypatch.setenv("ROKUJU_GENERATOR", "dummy")
    for k in ("STRIPE_SECRET_KEY", "RESEND_API_KEY", "ROKUJU_ADMIN_PASSWORD", "ROKUJU_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(seihon, "report_pdf", lambda md, destiny, name=None, today=None: b"%PDF-1.4 dummy " + md[:20].encode())
    return tmp_path


ANSWERS = dict(q1="帝王として陽転し自分が源という生き方をしたい。", q2="本心で生きる。", q3="35歳でギターをやめた。",
               q4="一人で抱える。", q5="前を向ける。", optional="")


def test_full_flow(env):
    c = TestClient(app, follow_redirects=False)
    r = c.get("/apply", params={"birth": "1973-11-23"})
    assert r.status_code == 200 and 'value="1973-11-23"' in r.text and "そのままの言葉で" in r.text

    r = c.post("/apply", data=dict(name="逆井 勤", birth="1973-11-23", sex="male", email="t@example.com", plan="kanzen", **ANSWERS))
    assert r.status_code == 303 and "/pay/dummy/" in r.headers["location"]
    order_id = r.headers["location"].rsplit("/", 1)[1]
    o = db.get_order(order_id)
    assert o.status == db.PENDING_PAYMENT and o.destiny["rokuju"]["day"]["number"] == 60 and o.price == 3980

    assert c.get(f"/pay/dummy/{order_id}").status_code == 200
    r = c.post(f"/pay/dummy/{order_id}")      # BackgroundTasks は TestClient では応答後に同期実行
    assert r.status_code == 303
    o = db.get_order(order_id)
    assert o.status == db.REVIEW and o.payment_ref == "dummy"
    gen = db.latest_generation(order_id)
    assert gen["model"] == "dummy" and "## 八、用語の言い換え表" in gen["markdown"] and "初冬、十一月。" in gen["markdown"]
    assert not any(i["level"] == "error" for i in gen["issues"])

    r = c.get(f"/order/{order_id}")
    assert r.status_code == 200 and "承認待ち" in r.text

    r = c.get("/admin")
    assert r.status_code == 200 and order_id in r.text and "ROKUJU_ADMIN_PASSWORD" in r.text
    r = c.get(f"/admin/order/{order_id}")
    assert r.status_code == 200 and "承認する" in r.text and "源へ帰る水" in r.text

    # 送付は承認前なら拒む
    assert c.post(f"/admin/order/{order_id}/send").status_code == 409

    edited = gen["markdown"].replace("## はじめに", "## はじめに\n\n（加筆）", 1)
    r = c.post(f"/admin/order/{order_id}/approve", data={"markdown": edited, "note": "一読"})
    assert r.status_code == 303
    assert db.get_order(order_id).status == db.APPROVED and db.approved_markdown(order_id).startswith("## はじめに\n\n（加筆）")

    r = c.get(f"/admin/order/{order_id}/pdf")
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")

    r = c.post(f"/admin/order/{order_id}/send")
    assert r.status_code == 303
    o = db.get_order(order_id)
    assert o.status == db.SENT
    d = db.list_deliveries(order_id)
    assert len(d) == 1 and d[0]["to_addr"] == "t@example.com" and d[0]["attachment"].endswith(".pdf")
    assert os.path.exists(d[0]["result"]) and open(d[0]["result"], "rb").read().startswith(b"%PDF")
    assert "送付済み" in c.get(f"/order/{order_id}").text


def test_apply_validation(env):
    c = TestClient(app, follow_redirects=False)
    r = c.post("/apply", data=dict(birth="1850-01-01", email="t@example.com", plan="kanzen", **ANSWERS))
    assert r.status_code == 400 and "1900年から" in r.text
    r = c.post("/apply", data=dict(birth="1973-11-23", email="t@example.com", plan="kanzen", **{**ANSWERS, "q1": ""}))
    assert r.status_code == 400 and "1 の問い" in r.text
    r = c.post("/apply", data=dict(birth="1973-11-23", email="nope", plan="kanzen", **ANSWERS))
    assert r.status_code == 400


def test_stripe_webhook_dummy_payload_and_regenerate(env):
    c = TestClient(app, follow_redirects=False)
    o = flow.create_order(name=None, birth="1960-02-05", sex="female", email="a@example.com", answers=ANSWERS, plan="kanshu")
    assert o.price == 9800
    # ダミー決済アダプタの webhook 形式
    r = c.post("/webhook/stripe", json={"order_id": o.id})
    assert r.status_code == 200 and db.get_order(o.id).status == db.REVIEW
    r = c.post(f"/admin/order/{o.id}/regenerate")
    assert r.status_code == 303 and db.get_order(o.id).status == db.REVIEW
    assert [a["action"] for a in db.list_approvals(o.id)] == ["regenerate"]
    assert c.post("/webhook/stripe", json={"order_id": "nope"}).status_code == 404


def test_generation_failure_is_recorded(env, monkeypatch):
    o = flow.create_order(name=None, birth="1973-11-23", sex="male", email="a@example.com", answers=ANSWERS, plan="kanzen")
    flow.mark_paid(o.id, "x")

    class Boom:
        name = "boom"

        def generate(self, order):
            raise RuntimeError("API down")

    from uketsuke.adapters import Adapters, DummyMail, DummyPayment
    res = flow.run_generation(o.id, Adapters(DummyPayment(), DummyMail(), Boom()))
    assert res["ok"] is False and db.get_order(o.id).status == db.FAILED
    assert "API down" in db.latest_generation(o.id)["error"]


def test_admin_auth(env, monkeypatch):
    monkeypatch.setenv("ROKUJU_ADMIN_PASSWORD", "himitsu")
    c = TestClient(app)
    assert c.get("/admin").status_code == 401
    ok = c.get("/admin", headers={"Authorization": "Basic " + base64.b64encode(b"rokuju:himitsu").decode()})
    assert ok.status_code == 200 and "ROKUJU_ADMIN_PASSWORD" not in ok.text
