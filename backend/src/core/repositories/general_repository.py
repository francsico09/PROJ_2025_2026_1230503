import uuid

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

"""
    This is the abstract interface for all types of repositories.
    
    Each entity repository has a specific entity repository interface
    that inherits from here. The concrete implementation of methods is
    made in the postgres adapter.
"""
class GeneralRepository(ABC, Generic[T]):

    """ """
    """
    :param id UUID: internal system id of the entity

    :return Optional[T]: return the entity if found, else None
    """
    @abstractmethod
    def get_by_id(self, id: uuid.UUID) -> Optional[T]: pass

    """
    :return list[T]: return the list of all entities T, if any, else return an empty list
    """
    @abstractmethod
    def get_all(self) -> list[T]: pass

    """
    :param entity T: entity to be saved
    
    :return T: return the saved entity
    """
    @abstractmethod
    def save(self, entity: T) -> T: pass

    """
    :param entity T: entity to be deleted
    """
    @abstractmethod
    def delete(self, id: uuid.UUID) -> None: pass
