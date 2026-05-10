"""
Dependências de autenticação para injectar nos controllers via Depends().

Uso:
    @router.get("/something")
    async def endpoint(current_user: User = Depends(get_current_user)):
        ...

    @router.post("/admin-only")
    async def admin_endpoint(_: User = Depends(require_admin)):
        ...
"""
import logging
import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from starlette import status

from src.core.repositories.repositories import Repositories
from src.core.settings.settings import settings
from src.modules.user.model.user_model import User

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()

"""
Validated JWT and returns the user from DB.
Used in any endpoint that requires authentication.

:param credential HTTPAuthorizationCredentials: depends on the bearer.

:return User:
"""
async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from DB to get current role/active status
    async with Repositories() as repos:
        user = await repos.users.get_by_id(uuid.UUID(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated.",
        )

    return user

"""
Guarantees that the authenticated user has the admin role.
Used in management endpoints.

:param current_user User: 

:return User:
"""
async def require_admin(
        current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role.value != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action.",
        )
    return current_user
