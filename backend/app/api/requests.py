from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, get_request_service
from app.models import User
from app.models.enums import MessageSource, RequestStatus
from app.schemas.request import RequestCreateIn, RequestDetailOut, RequestOut, RequestUpdateIn
from app.services.requests import RequestService

router = APIRouter(prefix="/api/requests", tags=["requests"])


@router.get("", response_model=list[RequestOut])
def list_requests(
    status: RequestStatus | None = None,
    requires_review: bool | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    service: RequestService = Depends(get_request_service),
):
    return service.list(
        user.business_id,
        status=status,
        requires_review=requires_review,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=RequestDetailOut, status_code=201)
def create_request(
    data: RequestCreateIn,
    user: User = Depends(get_current_user),
    service: RequestService = Depends(get_request_service),
):
    return service.create_from_text(
        business_id=user.business_id,
        client_id=data.client_id,
        text=data.text,
        source=MessageSource.WEB,
        created_by_user_id=user.id,
    )


@router.get("/{request_id}", response_model=RequestDetailOut)
def get_request(
    request_id: int,
    user: User = Depends(get_current_user),
    service: RequestService = Depends(get_request_service),
):
    return service.get(user.business_id, request_id)


@router.patch("/{request_id}", response_model=RequestOut)
def update_request(
    request_id: int,
    data: RequestUpdateIn,
    user: User = Depends(get_current_user),
    service: RequestService = Depends(get_request_service),
):
    return service.update(user.business_id, request_id, data.model_dump(exclude_unset=True), user)
