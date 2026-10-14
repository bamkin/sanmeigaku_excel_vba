"""FastAPI アプリ（サーバー描画・JS最小）。

    uvicorn shindan.app:app --reload

GET /                     生年月日の入力
GET /shindan?birth=...    無料診断の結果
GET /card/{number}.svg    風景カード（SNS共有用）
申込〜承認〜送付の経路は uketsuke/routes.py（/apply, /pay/dummy, /order, /admin, /webhook/stripe）
"""
from __future__ import annotations

import os

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from uketsuke.routes import router as uketsuke_router

from .card import card_svg
from .service import card_data, free_diagnosis

HERE = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(HERE, "templates"))
app = FastAPI(title="六十の風景", docs_url=None, redoc_url=None)
app.include_router(uketsuke_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"error": None, "birth": ""})


@app.get("/shindan", response_class=HTMLResponse)
def shindan(request: Request, birth: str = Query(default=""), sex: str = Query(default="unknown")):
    try:
        result = free_diagnosis(birth, sex)
    except ValueError as e:
        return templates.TemplateResponse(request, "index.html", {"error": str(e), "birth": birth}, status_code=400)
    return templates.TemplateResponse(request, "result.html", {"r": result})


@app.get("/card/{number}.svg")
def card(number: int):
    if not 1 <= number <= 60:
        return Response("not found", status_code=404)
    c = card_data(number)
    return Response(card_svg(c["number_kanji"], c["kanshi"], c["name"], c["closing"]),
                    media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})
