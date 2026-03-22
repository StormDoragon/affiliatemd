from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.site import Site
from ..models.user import User
from ..schemas.site import SiteCreate, SiteRead

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("/", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def connect_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Site:
    site = Site(
        user_id=current_user.id,
        wp_url=payload.wp_url,
        wp_username=payload.wp_username,
        wp_app_password=payload.wp_app_password,
        amazon_tag=payload.amazon_tag,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/", response_model=list[SiteRead])
def list_sites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Site]:
    return db.query(Site).filter(Site.user_id == current_user.id).all()


@router.get("/{site_id}", response_model=SiteRead)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Site:
    site = db.query(Site).filter(Site.id == site_id, Site.user_id == current_user.id).first()
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site
