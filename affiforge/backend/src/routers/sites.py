from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import enforce_provider_use, get_current_user, get_db
from ..models.site import Site
from ..models.user import User
from ..schemas.site import SiteCreate, SiteCredentials, SiteRead
from ..services.credentials import encrypt_password
from ..services.wordpress_service import WordpressService

router = APIRouter(prefix="/sites", tags=["sites"])


def get_owned_site(db: Session, site_id: int, owner_id: int) -> Site:
    site = db.query(Site).filter(Site.id == site_id, Site.user_id == owner_id).first()
    if site is None:
        raise HTTPException(404, "Site not found")
    return site


def save_credentials(db: Session, site: Site, payload: SiteCredentials, owner_id: int) -> Site:
    enforce_provider_use(owner_id)
    password = payload.wp_app_password.get_secret_value()
    encrypted = encrypt_password(password)
    WordpressService().verify(site.wp_url, payload.wp_username, password)
    site.wp_username = payload.wp_username
    site.wp_app_password = encrypted
    site.amazon_tag = payload.amazon_tag
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.post("/", response_model=SiteRead, status_code=status.HTTP_201_CREATED)
def connect_site(
    payload: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Site:
    site = Site(user_id=current_user.id, wp_url=payload.wp_url)
    return save_credentials(db, site, payload, current_user.id)


@router.get("/", response_model=list[SiteRead])
def list_sites(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Site]:
    return (
        db.query(Site)
        .filter(Site.user_id == current_user.id)
        .order_by(Site.id.desc())
        .limit(100)
        .all()
    )


@router.get("/{site_id}", response_model=SiteRead)
def get_site(
    site_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Site:
    return get_owned_site(db, site_id, current_user.id)


@router.put("/{site_id}", response_model=SiteRead)
def reconnect_site(
    site_id: int,
    payload: SiteCredentials,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Site:
    site = get_owned_site(db, site_id, current_user.id)
    return save_credentials(db, site, payload, current_user.id)
