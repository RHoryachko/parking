from typing import Annotated

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.services import booking_service

router = APIRouter()


@router.post("/liqpay/callback")
def liqpay_callback(
    db: Annotated[Session, Depends(get_db)],
    data: Annotated[str, Form()],
    signature: Annotated[str, Form()],
):
    """
    LiqPay server-to-server callback (application/x-www-form-urlencoded).
    Must be reachable at APP_PUBLIC_API_URL + /api/payments/liqpay/callback
    """
    payload = booking_service.apply_liqpay_callback(db=db, data_b64=data, signature=signature)
    return JSONResponse(payload, status_code=status.HTTP_200_OK)
