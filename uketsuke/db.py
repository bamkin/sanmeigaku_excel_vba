"""SQLite（単一ファイル）。申込・宿命表JSON・生成結果・承認履歴・送付記録。"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, name TEXT, birth TEXT NOT NULL, sex TEXT NOT NULL,
  email TEXT NOT NULL, answers TEXT NOT NULL, plan TEXT NOT NULL, status TEXT NOT NULL,
  payment_ref TEXT, destiny TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS generations (
  id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, created_at TEXT NOT NULL,
  model TEXT, effort TEXT, stop_reason TEXT, raw TEXT, markdown TEXT, issues TEXT, notes TEXT, usage TEXT, error TEXT);
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, generation_id INTEGER, created_at TEXT NOT NULL,
  action TEXT NOT NULL, note TEXT, markdown TEXT);
CREATE TABLE IF NOT EXISTS deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL, created_at TEXT NOT NULL,
  channel TEXT NOT NULL, to_addr TEXT, subject TEXT, body TEXT, attachment TEXT, result TEXT);
"""

# 申込の状態
PENDING_PAYMENT = "pending_payment"   # 決済待ち
PAID = "paid"                         # 入金済み・生成前
GENERATING = "generating"             # 生成中
REVIEW = "review"                     # 生成済み・承認待ち
FAILED = "failed"                     # 生成失敗（再生成できる）
APPROVED = "approved"                 # 承認済み・送付前
SENT = "sent"                         # 送付済み

STATUS_LABELS = {
    PENDING_PAYMENT: "決済待ち", PAID: "入金済み", GENERATING: "生成中", REVIEW: "承認待ち",
    FAILED: "生成失敗", APPROVED: "承認済み", SENT: "送付済み",
}

PLANS = {"kanzen": ("完全版", 3980), "kanshu": ("監修版", 9800)}


def db_path() -> str:
    return os.environ.get("ROKUJU_DB", "rokuju.sqlite3")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path())
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


@dataclass
class Order:
    id: str
    created_at: str
    name: str | None
    birth: str
    sex: str
    email: str
    answers: dict
    plan: str
    status: str
    payment_ref: str | None
    destiny: dict

    @classmethod
    def from_row(cls, r: sqlite3.Row) -> "Order":
        return cls(r["id"], r["created_at"], r["name"], r["birth"], r["sex"], r["email"],
                   json.loads(r["answers"]), r["plan"], r["status"], r["payment_ref"], json.loads(r["destiny"]))

    @property
    def plan_label(self) -> str:
        return PLANS[self.plan][0]

    @property
    def price(self) -> int:
        return PLANS[self.plan][1]

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)


def insert_order(o: Order) -> None:
    with connect() as con:
        con.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (o.id, o.created_at, o.name, o.birth, o.sex, o.email, json.dumps(o.answers, ensure_ascii=False),
                     o.plan, o.status, o.payment_ref, json.dumps(o.destiny, ensure_ascii=False)))


def get_order(order_id: str) -> Order | None:
    with connect() as con:
        r = con.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return Order.from_row(r) if r else None


def list_orders(limit: int = 200) -> list[Order]:
    with connect() as con:
        rows = con.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [Order.from_row(r) for r in rows]


def set_status(order_id: str, status: str, payment_ref: str | None = None) -> None:
    with connect() as con:
        if payment_ref is not None:
            con.execute("UPDATE orders SET status=?, payment_ref=? WHERE id=?", (status, payment_ref, order_id))
        else:
            con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))


def insert_generation(order_id: str, *, model: str | None, effort: str | None, stop_reason: str | None,
                      raw: str | None, markdown: str | None, issues: list, notes: list, usage: dict,
                      error: str | None = None) -> int:
    with connect() as con:
        cur = con.execute(
            "INSERT INTO generations (order_id, created_at, model, effort, stop_reason, raw, markdown, issues, notes, usage, error)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (order_id, now(), model, effort, stop_reason, raw, markdown, json.dumps(issues, ensure_ascii=False),
             json.dumps(notes, ensure_ascii=False), json.dumps(usage, ensure_ascii=False, default=str), error))
        return int(cur.lastrowid)


def latest_generation(order_id: str) -> dict | None:
    with connect() as con:
        r = con.execute("SELECT * FROM generations WHERE order_id=? ORDER BY id DESC LIMIT 1", (order_id,)).fetchone()
    if not r:
        return None
    d = dict(r)
    for k in ("issues", "notes", "usage"):
        d[k] = json.loads(d[k]) if d[k] else ([] if k != "usage" else {})
    return d


def insert_approval(order_id: str, generation_id: int | None, action: str, note: str | None, markdown: str | None) -> int:
    with connect() as con:
        cur = con.execute("INSERT INTO approvals (order_id, generation_id, created_at, action, note, markdown) VALUES (?,?,?,?,?,?)",
                          (order_id, generation_id, now(), action, note, markdown))
        return int(cur.lastrowid)


def list_approvals(order_id: str) -> list[dict]:
    with connect() as con:
        rows = con.execute("SELECT * FROM approvals WHERE order_id=? ORDER BY id", (order_id,)).fetchall()
    return [dict(r) for r in rows]


def approved_markdown(order_id: str) -> str | None:
    """最後に承認された本文（加筆後）。"""
    with connect() as con:
        r = con.execute("SELECT markdown FROM approvals WHERE order_id=? AND action='approve' ORDER BY id DESC LIMIT 1",
                        (order_id,)).fetchone()
    return r["markdown"] if r else None


def insert_delivery(order_id: str, channel: str, to_addr: str, subject: str, body: str, attachment: str | None, result: str) -> int:
    with connect() as con:
        cur = con.execute("INSERT INTO deliveries (order_id, created_at, channel, to_addr, subject, body, attachment, result)"
                          " VALUES (?,?,?,?,?,?,?,?)", (order_id, now(), channel, to_addr, subject, body, attachment, result))
        return int(cur.lastrowid)


def list_deliveries(order_id: str) -> list[dict]:
    with connect() as con:
        rows = con.execute("SELECT * FROM deliveries WHERE order_id=? ORDER BY id", (order_id,)).fetchall()
    return [dict(r) for r in rows]
