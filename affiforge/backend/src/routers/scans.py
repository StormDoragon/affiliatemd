from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.scan import Scan
from ..models.user import User
from ..schemas.scan import ScanCreate, ScanRead

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("/", response_model=ScanRead, status_code=status.HTTP_201_CREATED)
def create_scan(
    payload: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Scan:
    scan = Scan(
        source=payload.source,
        query=payload.query,
        summary=payload.summary,
        owner_id=current_user.id,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    return scan


@router.get("/", response_model=list[ScanRead])
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Scan]:
    return db.query(Scan).filter(Scan.owner_id == current_user.id).all()
