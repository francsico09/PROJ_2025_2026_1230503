from abc import abstractmethod

from src.core.repositories.general_repository import GeneralRepository
from src.core.domain.user.user_model.user_model import User


class UserRepository(GeneralRepository[User]):
    @abstractmethod
    async def get_by_email(self, email: str) -> User: ...
