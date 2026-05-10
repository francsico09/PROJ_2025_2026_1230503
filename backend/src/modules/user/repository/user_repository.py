from abc import abstractmethod

from src.core.repositories.general_repository import GeneralRepository
from src.modules.user.model.role.user_role import UserRole
from src.modules.user.model.user_model import User

class UserRepository(GeneralRepository[User]):
    @abstractmethod
    def get_by_name(self, name: str) -> list[User]: pass

    @abstractmethod
    def get_by_email(self, email: str) -> User: pass

    @abstractmethod
    def get_by_role(self, role: UserRole) -> list[User]: pass
