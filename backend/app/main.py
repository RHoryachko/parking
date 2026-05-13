from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_cors_origins
from app.routers import admin, ai, auth, client, payments, worker

app = FastAPI(title="Parking API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = FastAPI()
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
