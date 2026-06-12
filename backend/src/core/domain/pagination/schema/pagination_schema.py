from typing import Generic, TypeVar
from pydantic import BaseModel
from fastapi import Query
from dataclasses import dataclass

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int


@dataclass
class PaginationParams:
    page:      int = Query(1, ge=1)
    page_size: int = Query(20, ge=1, le=100)
    search:    str = Query("", description="Search term")
    sort_by:   str = Query("created_at")
    sort_dir:  str = Query("desc", pattern="^(asc|desc)$")
