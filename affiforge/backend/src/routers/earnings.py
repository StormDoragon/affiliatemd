from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.earning_event import EarningEvent
from ..models.user import User
from ..schemas.earnings import EarningCreate, EarningRead

router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.post("/", response_model=EarningRead, status_code=status.HTTP_201_CREATED)
def create_earning(
    payload: EarningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EarningEvent:
    entry = EarningEvent(
        network=payload.network,
        amount=payload.amount,
        currency=payload.currency,
        content_item_id=payload.content_item_id,
        owner_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[EarningRead])
def list_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EarningEvent]:
    return db.query(EarningEvent).filter(EarningEvent.owner_id == current_user.id).all()
