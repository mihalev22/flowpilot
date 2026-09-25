from fastapi import APIRouter, Depends

from app.api.deps import get_client_service, get_current_user, get_request_service
from app.models import User
from app.schemas.client import ClientOut
from app.schemas.request import ClientDetailOut, RequestOut
from app.services.clients import ClientService
from app.services.requests import RequestService

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=list[ClientOut])
def list_clients(
    search: str | None = None,
    user: User = Depends(get_current_user),
    service: ClientService = Depends(get_client_service),
):
    return service.list(user.business_id, search=search)


@router.get("/{client_id}", response_model=ClientDetailOut)
def get_client(
    client_id: int,
    user: User = Depends(get_current_user),
    client_service: ClientService = Depends(get_client_service),
    request_service: RequestService = Depends(get_request_service),
):
    client = client_service.get(user.business_id, client_id)
    requests = request_service.list_by_client(user.business_id, client_id)
    return ClientDetailOut(
        client=ClientOut.model_validate(client),
        requests=[RequestOut.model_validate(item) for item in requests],
    )
