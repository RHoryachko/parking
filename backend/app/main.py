from contextlib import asynccontextmanager
from html import escape

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.config import get_cors_origins
from app.db.session import bootstrap_sqlite_schema, maybe_seed_empty_db
from app.routers import admin, ai, auth, client, payments, worker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    bootstrap_sqlite_schema()
    maybe_seed_empty_db()
    yield


app = FastAPI(title="Parking API", version="0.1.0", lifespan=lifespan)

# CORS must live on the mounted `api` app: preflight OPTIONS to /api/* is handled inside
# the sub-app; middleware on the parent does not reliably short-circuit those requests.
api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api.include_router(auth.router, prefix="/auth", tags=["auth"])
api.include_router(client.router, prefix="/client", tags=["client"])
api.include_router(worker.router, prefix="/worker", tags=["worker"])
api.include_router(admin.router, prefix="/admin", tags=["admin"])
api.include_router(payments.router, prefix="/payments", tags=["payments"])
api.include_router(ai.router, prefix="/ai", tags=["ai"])

app.mount("/api", api)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/payment/success", response_class=HTMLResponse)
def payment_success(booking_id: str | None = None):
    """Shown after LiqPay redirects the payer (result_url). Server callback may finish a moment later."""
    bid_html = ""
    if booking_id and booking_id.isdigit():
        b = escape(booking_id)
        bid_html = f'<p class="muted">Номер бронювання: <strong>#{b}</strong></p>'
    html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Оплата пройшла</title>
  <style>
    body {{
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
      background: linear-gradient(160deg, #eef2ff 0%, #f8fafc 45%, #ecfdf5 100%);
      color: #0f172a;
    }}
    .card {{
      max-width: 420px; padding: 2rem 2.25rem; background: #fff; border-radius: 18px;
      box-shadow: 0 18px 50px rgba(15, 23, 42, 0.12); border: 1px solid #e2e8f0;
    }}
    h1 {{ font-size: 1.45rem; margin: 0 0 0.5rem; font-weight: 800; letter-spacing: -0.02em; }}
    p {{ margin: 0.65rem 0; line-height: 1.55; color: #334155; }}
    .muted {{ color: #64748b; font-size: 0.95rem; }}
    .ok {{ display: inline-flex; align-items: center; gap: 0.5rem; color: #15803d; font-weight: 700; margin-bottom: 1rem; }}
    .hint {{ font-size: 0.9rem; background: #f1f5f9; padding: 0.85rem 1rem; border-radius: 12px; margin-top: 1.25rem; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="ok">✓ Оплату прийнято</div>
    <h1>Замовлення оплачене</h1>
    <p>Дякуємо! Платіж у LiqPay оброблено. Бронювання зʼявиться як <strong>оплачене</strong> у вашому застосунку.</p>
    {bid_html}
    <div class="hint">
      Якщо статус ще не оновився — зачекайте кілька секунд (сервер отримує підтвердження окремо), потім відкрийте
      <strong>«Мої бронювання»</strong> у клієнтському застосунку або оновіть список.
    </div>
    <p class="muted" style="margin-top:1.5rem">Можете закрити цю вкладку і повернутися в застосунок.</p>
  </div>
</body>
</html>"""
    return HTMLResponse(html)
