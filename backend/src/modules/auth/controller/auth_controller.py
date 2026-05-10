from fastapi import APIRouter, Depends
from starlette import status

from src.core.repositories.repositories import Repositories
from src.modules.auth.schemas.auth_schemas import TokenResponse, LoginRequest
from src.modules.auth.service.auth_service import AuthService
from src.modules.ldap.service.ldap_service import LDAPService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service() -> AuthService:
    return AuthService(
        repos=Repositories(),
        ldap_service=LDAPService(),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate via LDAP and receive JWT token",
)
async def login(
        credentials: LoginRequest,
        service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.login(credentials)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Obter dados do utilizador autenticado",
)
async def me(current_user=Depends(__import__('src.modules.auth.auth', fromlist=['get_current_user']).get_current_user)):
    return {
        "id":    str(current_user.id),
        "name":  current_user.name,
        "email": current_user.email,
        "role":  current_user.role,
    }
