# Paid parking MVP

Backend: **FastAPI + SQLAlchemy + Alembic + PostgreSQL**, JWT auth, REST under `/api`.  
Admin UI: **React + TypeScript + Vite + Tailwind** (Apple-style layout).

## Quick start (Docker)

From repo root:

```bash
docker compose up --build
```

- API: `http://localhost:8000` (OpenAPI: `http://localhost:8000/docs`)
- Postgres: `localhost:5432` (`parking` / `parking`)

Run migrations are executed automatically on API container start. Then seed demo data:

```bash
docker compose exec api python -m app.seeds.seed
```

## Local dev (without Docker for API)

1. Start Postgres and set `DATABASE_URL` in `backend/.env` (see `backend/.env.example`).
2. Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
alembic upgrade head
python -m app.seeds.seed
uvicorn app.main:app --reload --port 8000
```

3. Admin UI:

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` → `http://127.0.0.1:8000` (see `frontend/vite.config.ts`).  
Optional: `frontend/.env` with `VITE_API_URL=http://localhost:8000/api`.

## Seeded accounts

| Role   | Email                 | Password   |
|--------|----------------------|------------|
| Admin  | `admin@parking.local` | `admin123` |
| Worker | `worker@parking.local`| `worker123`|
| Client | `client@parking.local`| `client123`|

Also creates **Central Lot** (Kyiv), **A1–A10** spots, **50 UAH/h** tariff, worker assignment, client vehicle plate **`AA1234BC`**.

## Role matrix (high level)

| Area            | Client | Worker | Admin |
|-----------------|--------|--------|-------|
| Auth register   | yes    | no     | no    |
| Book / pay mock | yes    | —      | —     |
| Entry / exit    | —      | yes    | —     |
| CRUD parkings   | —      | —      | yes   |
| AI check-entry  | public | —      | —     |

## Example `curl` flows

Replace `TOKEN` with JWT from login.

### Register + login (client)

```bash
curl -s -X POST http://localhost:8000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"full_name\":\"Test\",\"email\":\"test@example.com\",\"password\":\"secret12\"}"

curl -s -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"client@parking.local\",\"password\":\"client123\"}"
```

### Admin stats

```bash
curl -s http://localhost:8000/api/admin/stats ^
  -H "Authorization: Bearer TOKEN"
```

### Client: list parkings in Kyiv + create booking (example IDs)

```bash
curl -s "http://localhost:8000/api/client/parkings?city=Kyiv" ^
  -H "Authorization: Bearer CLIENT_TOKEN"

curl -s -X POST http://localhost:8000/api/client/bookings ^
  -H "Authorization: Bearer CLIENT_TOKEN" -H "Content-Type: application/json" ^
  -d "{\"vehicle_id\":1,\"parking_id\":1,\"spot_id\":1,\"tariff_id\":1,\"planned_start_time\":\"2026-04-30T10:00:00Z\",\"planned_end_time\":\"2026-04-30T12:00:00Z\"}"
```

### Client: mock pay

```bash
curl -s -X POST http://localhost:8000/api/client/bookings/1/pay ^
  -H "Authorization: Bearer CLIENT_TOKEN"
```

### Worker: register entry / exit

```bash
curl -s -X POST http://localhost:8000/api/worker/entry ^
  -H "Authorization: Bearer WORKER_TOKEN" -H "Content-Type: application/json" ^
  -d "{\"parking_id\":1,\"plate_number\":\"AA1234BC\"}"

curl -s -X POST http://localhost:8000/api/worker/exit ^
  -H "Authorization: Bearer WORKER_TOKEN" -H "Content-Type: application/json" ^
  -d "{\"session_id\":1}"
```

### AI check-entry (no auth)

```bash
curl -s -X POST http://localhost:8000/api/ai/check-entry ^
  -H "Content-Type: application/json" ^
  -d "{\"parking_id\":1,\"recognized_plate\":\"AA1234BC\",\"confidence\":0.92}"
```

## Project structure

- `backend/app` — FastAPI app (`main.py`, `routers/`, `services/`, `models/`, `schemas/`)
- `backend/app/alembic` — migrations
- `backend/app/seeds/seed.py` — demo data
- `frontend/src` — admin UI (`pages/`, `components/`, `api/`)

## Notes

- Payments are **mock** only (`/api/client/bookings/{id}/pay`).
- `POST /api/ai/check-entry` is **unauthenticated** in MVP (tighten with a shared secret / network policy later).
- Plate numbers are normalized to **uppercase** without spaces or hyphens.
