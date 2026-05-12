import uuid

from fastapi import APIRouter, status, Depends

from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse
from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin, get_current_user
from src.modules.user.service.user_service import UserService
from src.core.domain.user.user_model.user_model import User

from src.core.domain.user.user_schema.user_schemas import UserResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service() -> UserService:
    return UserService(Repositories())


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Fetch users with pagination and search",
)
async def fetch_users(
        params: PaginationParams = Depends(),
        service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    return await service.fetch_users(params)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user by id",
)
async def get_user_by_id(
        user_id: uuid.UUID,
        current_user: User = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
) -> UserResponse:
    if current_user.role != "admin" and current_user.id != user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return await service.get_user_by_id(user_id)

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
)
async def create_user(
        user_data: UserCreate,
        _: User = Depends(require_admin),
        service: UserService = Depends(get_user_service),
) -> UserResponse:
    return await service.create_user(user_data)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user",
)
async def update_user(
        user_id: uuid.UUID,
        user_data: UserUpdate,
        current_user: User = Depends(get_current_user),
        service: UserService = Depends(get_user_service),
) -> UserResponse:
    if current_user.role != "admin" and current_user.id != user_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return await service.update_user(user_id, user_data)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user",
)
async def delete_user(
        user_id: uuid.UUID,
        _: User = Depends(require_admin),
        service: UserService = Depends(get_user_service),
) -> None:
    await service.delete_user(user_id)