import uuid

from fastapi import APIRouter, status, Depends

from src.core.repositories.repositories import Repositories
from src.modules.auth.auth import require_admin
from src.modules.user.model.user_model import User
from src.modules.user.schema.user_schemas import UserResponse, UserCreate, UserUpdate
from src.modules.user.service.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

def get_user_service() -> UserService:
    return UserService(Repositories())


@router.post(
    "/create_user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user"
)
async def create_user(
        user_data: UserCreate,
        _: User = Depends(require_admin),
        service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await service.create_user(user_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user"
)
async def delete_user(
        user_id: uuid.UUID,
        _: User = Depends(require_admin),
        service: UserService = Depends(get_user_service)
) -> None:
    await service.delete_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user"
)
async def update_user(
        user_id: uuid.UUID,
        user_data: UserUpdate,
        _: User = Depends(require_admin),
        service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await service.update_user(user_id, user_data)


@router.get(
    "/by-id/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user by id"
)
async def get_user_by_id(
        user_id: uuid.UUID,
        service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await service.get_user_by_id(user_id)


@router.get(
    "/by-email/{user_email}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a user by email"
)
async def get_user_by_email(
        email: str,
        service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await service.get_user_by_email(email)


@router.get(
    "/",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users"
)
async def list_users(
        service: UserService = Depends(get_user_service)
) -> list[UserResponse]:
    return await service.list_users()
