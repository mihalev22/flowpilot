from fastapi import APIRouter, Depends

from app.api.deps import get_catalog_service, get_current_user
from app.models import User
from app.schemas.service import ServiceOut
from app.services.catalog import CatalogService

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("", response_model=list[ServiceOut])
def list_services(
    user: User = Depends(get_current_user),
    service: CatalogService = Depends(get_catalog_service),
) -> list[ServiceOut]:
    return service.list(user.business_id)
