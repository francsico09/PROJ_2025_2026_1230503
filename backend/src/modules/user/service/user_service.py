import uuid

from fastapi import HTTPException
from starlette import status

from src.core.repositories.repositories import Repositories
from src.modules.user.model.user_model import User
from src.modules.user.schema.user_schemas import UserResponse, UserCreate, UserUpdate

class UserService:
    def __init__(self, repos: Repositories) -> None:
        self._repos = repos

    """
    Asynchronous function to create a User. If successful, the newly added 
    User will be returned, else an exception will be raised.
    
    :param user_data UserCreate: the data of the user that will be created.
    
    :return UserResponse:
    
    :raises:
    """
    async def create_user(
            self,
            user_data: UserCreate
    ) -> UserResponse:
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

    """
    Asynchronous function to delete a User. Nothing is returned.
    
    :param user_id UUID: id of the user that will be deleted.
    
    :raises:
    """
    async def delete_user(
            self,
            user_id: uuid.UUID
    ) -> None:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            await repos.users.delete(user_id)
            await repos.commit()

    """
    Asynchronous function to update a User. If successful, the updated user
    is returned, else an exception will be raised.
    
    :param user_data UserUpdate: new data for the user that will be updated.
    
    :return UserResponse:
    
    :raises:
    """
    async def update_user(
            self,
            user_id: uuid.UUID,
            user_data: UserUpdate
    ) -> UserResponse:
        async with self._repos as repos:
            user = await repos.users.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            user.update(user_data)

            await repos.users.save(user)
            await repos.commit()

            return UserResponse.model_validate(user)

    """
    Asynchronous function to fetch a User by email. If successful, the user
    is returned, else an exception will be raised.

    :param email str: email of the user that will be fetched.

    :return UserResponse:

    :raises:
    """
    async def get_user_by_email(
            self,
            email: str
    ) -> UserResponse:
        async with self._repos as repos:
            user = await repos.users.get_by_email(email)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

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

    """
    Asynchronous function to fetch all User. If there are no User, 
    the list is returned empty.
    
    :return list[UserResponse]:
    """
    async def list_users(
            self
    ) -> list[UserResponse]:
        async with self._repos as repos:
            return await repos.users.get_all()
