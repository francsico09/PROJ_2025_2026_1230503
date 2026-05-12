import uuid

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse

T = TypeVar('T')


class GeneralRepository(ABC, Generic[T]):
    """
    This is the abstract interface for all types of repositories.

    Each entity repository has a specific entity repository interface
    that inherits from here. The concrete implementation of methods is
    made in the postgres adapter.
    """

    @abstractmethod
    async def fetch(self, params: PaginationParams) -> PaginatedResponse:
        """
        For external use, with API's and such. Returns a paginated result.

        :param params: parameters for pagination, search and sorting

        :return PaginatedResponse:
        """
        ...

    @abstractmethod
    async def get_all(self) -> list[T]:
        """
        For internal use. Returns all entities without pagination.

        :return list[T]: list of all entities
        """
        ...

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[T]:
        """
        For internal use.

        :param id: internal system id of the entity

        :return Optional[T]: return the entity if found, else None
        """
        ...


    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        :param entity: entity to be saved

        :return T: return the saved entity
        """
        ...


    @abstractmethod
    async def delete(self, id: uuid.UUID) -> None:
        """
        :param id: id of the entity to be deleted
        """
        ...
