import uuid

from fastapi import HTTPException
from starlette import status

from src.core.repositories.repositories import Repositories

from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_schema.user_schemas import UserCreate, UserResponse, UserUpdate

from src.core.domain.pagination.schema.pagination_schema import PaginatedResponse, PaginationParams


class UserService:
    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    async def create_user(
            self,
            user_data: UserCreate
    ) -> UserResponse:
        """
        Asynchronous function to create a User. If successful, the newly added
        User will be returned, else an exception will be raised.

        :param user_data: the data of the user that will be created.

        :return UserResponse:
        """
        async with self._repos as repos:
            with_same_email = await repos.users.get_by_email(user_data.email)

            if with_same_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

            user = User(
                id=uuid.uuid4(),
                name=user_data.name,
                email=user_data.email,
                active=True,
                researcherProfile=user_data.researcherProfile,
                role=user_data.role
            )

            await repos.users.save(user)
            await repos.commit()

            return UserResponse.model_validate(user)

    async def delete_user(
            self,
            user_id: uuid.UUID
    ) -> None:
        """
        Asynchronous function to delete a User. Nothing is returned.

        :param user_id: id of the user that will be deleted.

        :raises:
        """
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            await repos.users.delete(user_id)
            await repos.commit()

    async def update_user(
            self,
            user_id: uuid.UUID,
            user_data: UserUpdate
    ) -> UserResponse:
        """
        Asynchronous function to update a User. If successful, the updated user
        is returned, else an exception will be raised.

        :param user_id: id of the user that will be updated.
        :param user_data: new data for the user that will be updated.

        :return UserResponse:
        """
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            user.update(user_data)

            await repos.users.save(user)
            await repos.commit()

            return UserResponse.model_validate(user)

    async def get_user_by_id(
            self,
            user_id: uuid.UUID
    ) -> UserResponse:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            return UserResponse.model_validate(user)

    async def fetch_users(
            self,
            params: PaginationParams
    ) -> PaginatedResponse[UserResponse]:
        """
        Asynchronous function to fetch all User. If there are no User,
        the list is returned empty.

        :return list[UserResponse]:
        """
        async with self._repos as repos:
            result = await repos.users.fetch(params)

            return PaginatedResponse(
                items=[UserResponse.model_validate(u) for u in result.items],
                total=result.total,
                page=result.page,
                page_size=result.page_size,
                pages=result.pages,
            )