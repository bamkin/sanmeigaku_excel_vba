"""Web の経路（FastAPI ルーター）。shindan.app に組み込む。

GET  /apply                    申込フォーム（生年月日は無料診断から引き継ぐ）
POST /apply                    申込を保存して決済へ
GET/POST /pay/dummy/{id}       ダミー決済（Stripe の鍵が無いとき）
POST /webhook/stripe           Stripe の入金通知 → 生成を開始
GET  /order/{id}               受付状況（申込者向け）
GET  /admin                    承認画面：一覧
GET  /admin/order/{id}         承認画面：本文の表示・加筆・承認・再生成・送付
GET  /admin/order/{id}/pdf     PDF の試し刷り
"""
from __future__ import annotations

import os
import secrets

import markdown
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from . import db, flow
from .adapters import DummyPayment, adapters_from_env

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIRS = [os.path.join(HERE, "..", "shindan", "templates"), os.path.join(HERE, "templates")]
templates = Jinja2Templates(directory=TEMPLATE_DIRS)
router = APIRouter()
basic = HTTPBasic(auto_error=False)


def base_url(request: Request) -> str:
    return os.environ.get("ROKUJU_BASE_URL") or str(request.base_url).rstrip("/")


def admin_guard(credentials: HTTPBasicCredentials | None = Depends(basic)) -> str:
    """ROKUJU_ADMIN_PASSWORD があれば Basic 認証。無ければ開放（画面に注意書きを出す）。"""
    password = os.environ.get("ROKUJU_ADMIN_PASSWORD")
    if not password:
        return "open"
    if credentials and secrets.compare_digest(credentials.password.encode(), password.encode()):
        return "ok"
    raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})


def render_markdown(md: str) -> str:
    return markdown.markdown(md, extensions=["tables", "sane_lists"])


# ---------- 申込者側 ----------

@router.get("/apply", response_class=HTMLResponse)
def apply_form(request: Request, birth: str = ""):
    return templates.TemplateResponse(request, "apply.html", {"birth": birth, "error": None, "form": {}, "plans": db.PLANS})


@router.post("/apply")
def apply_submit(request: Request, name: str = Form(""), birth: str = Form(...), sex: str = Form("unknown"),
                 email: str = Form(...), plan: str = Form("kanzen"), q1: str = Form(""), q2: str = Form(""),
                 q3: str = Form(""), q4: str = Form(""), q5: str = Form(""), optional: str = Form("")):
    form = dict(name=name, birth=birth, sex=sex, email=email, plan=plan, q1=q1, q2=q2, q3=q3, q4=q4, q5=q5, optional=optional)
    try:
        order = flow.create_order(name=name, birth=birth, sex=sex, email=email, plan=plan,
                                  answers=dict(q1=q1, q2=q2, q3=q3, q4=q4, q5=q5, optional=optional))
    except ValueError as e:
        return templates.TemplateResponse(request, "apply.html", {"birth": birth, "error": str(e), "form": form, "plans": db.PLANS},
                                          status_code=400)
    url = adapters_from_env().payment.checkout_url(order, base_url(request))
    return RedirectResponse(url, status_code=303)


@router.get("/pay/dummy/{order_id}", response_class=HTMLResponse)
def pay_dummy(request: Request, order_id: str):
    order = db.get_order(order_id)
    if order is None or not isinstance(adapters_from_env().payment, DummyPayment):
        raise HTTPException(404)
    return templates.TemplateResponse(request, "pay_dummy.html", {"o": order})


@router.post("/pay/dummy/{order_id}")
def pay_dummy_submit(order_id: str, background: BackgroundTasks):
    if db.get_order(order_id) is None or not isinstance(adapters_from_env().payment, DummyPayment):
        raise HTTPException(404)
    flow.mark_paid(order_id, "dummy")
    background.add_task(flow.run_generation, order_id)
    return RedirectResponse(f"/order/{order_id}", status_code=303)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, background: BackgroundTasks):
    payload = await request.body()
    payment = adapters_from_env().payment
    try:
        hit = payment.webhook_order_id(payload, request.headers.get("stripe-signature"))
    except Exception as e:  # noqa: BLE001 — 署名不正など
        raise HTTPException(400, str(e)) from e
    if hit:
        order_id, ref = hit
        if db.get_order(order_id) is None:
            raise HTTPException(404)
        order = flow.mark_paid(order_id, ref)
        if order.status == db.PAID:
            background.add_task(flow.run_generation, order_id)
    return {"ok": True}


@router.get("/order/{order_id}", response_class=HTMLResponse)
def order_status(request: Request, order_id: str):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)
    return templates.TemplateResponse(request, "order.html", {"o": order})


# ---------- 承認画面 ----------

@router.get("/admin", response_class=HTMLResponse)
def admin_list(request: Request, auth: str = Depends(admin_guard)):
    return templates.TemplateResponse(request, "admin_list.html", {"orders": db.list_orders(), "auth": auth})


@router.get("/admin/order/{order_id}", response_class=HTMLResponse)
def admin_order(request: Request, order_id: str, auth: str = Depends(admin_guard)):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)
    gen = db.latest_generation(order_id)
    approved = db.approved_markdown(order_id)
    md = approved if approved is not None else ((gen or {}).get("markdown") or "")
    ctx = {"o": order, "gen": gen, "md": md, "preview": render_markdown(md) if md else "",
           "approvals": db.list_approvals(order_id), "deliveries": db.list_deliveries(order_id),
           "auth": auth, "char_count": None}
    if md:
        from seisei.checker import count_chars
        ctx["char_count"] = count_chars(md)
    return templates.TemplateResponse(request, "admin_order.html", ctx)


@router.post("/admin/order/{order_id}/generate")
def admin_generate(order_id: str, background: BackgroundTasks, auth: str = Depends(admin_guard)):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)
    if order.status in (db.PAID, db.FAILED):
        background.add_task(flow.run_generation, order_id)
    return RedirectResponse(f"/admin/order/{order_id}", status_code=303)


@router.post("/admin/order/{order_id}/regenerate")
def admin_regenerate(order_id: str, background: BackgroundTasks, auth: str = Depends(admin_guard)):
    if db.get_order(order_id) is None:
        raise HTTPException(404)
    background.add_task(flow.regenerate, order_id)
    return RedirectResponse(f"/admin/order/{order_id}", status_code=303)


@router.post("/admin/order/{order_id}/approve")
def admin_approve(order_id: str, markdown_text: str = Form(..., alias="markdown"), note: str = Form(""),
                  auth: str = Depends(admin_guard)):
    if db.get_order(order_id) is None:
        raise HTTPException(404)
    flow.approve(order_id, markdown_text.replace("\r\n", "\n"), note or None)
    return RedirectResponse(f"/admin/order/{order_id}", status_code=303)


@router.post("/admin/order/{order_id}/send")
def admin_send(request: Request, order_id: str, auth: str = Depends(admin_guard)):
    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)
    if order.status != db.APPROVED:
        raise HTTPException(409, "承認してから送付してください")
    flow.send(order_id, base_url=base_url(request))
    return RedirectResponse(f"/admin/order/{order_id}", status_code=303)


@router.get("/admin/order/{order_id}/pdf")
def admin_pdf(order_id: str, auth: str = Depends(admin_guard)):
    from seihon import report_pdf

    order = db.get_order(order_id)
    if order is None:
        raise HTTPException(404)
    md = db.approved_markdown(order_id) or ((db.latest_generation(order_id) or {}).get("markdown"))
    if not md:
        raise HTTPException(404, "本文がまだありません")
    pdf = report_pdf(md, order.destiny, name=order.name)
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{order.birth}_{order.id}.pdf"'})
