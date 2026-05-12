from sqlalchemy import select, func, asc, desc, or_, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.domain.pagination.schema.pagination_schema import PaginationParams, PaginatedResponse


class PostgresBaseRepository:
    """
    Base class for all the postgres adapters. Gives the _fetch_paginated method
    that can be reused by all the repositories that need pagination.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_paginated(
            self,
            model,
            params: PaginationParams,
            search_columns: list = None,
            extra_filters: list = None,
            joins: list = None,
            load_options: list = None,
            to_domain=None,
    ) -> PaginatedResponse:
        """
        This function allows for paginated fetching, returning a Paginated response

        :param model: ORM model of the entity to fetch
        :param params: PaginatedParams, to define pagination and ordering
        :param search_columns: columns of the model to search
        :param extra_filters: possible extra filters to search
        :param joins: possible joins on other tables
        :param load_options: possible load options for joined tables
        :param to_domain:

        :return: PaginatedResponse
        """
        query = select(model)

        if joins:
            for join_model in joins:
                query = query.join(join_model)

        if load_options:
            for opt in load_options:
                query = query.options(opt)

        if extra_filters:
            for f in extra_filters:
                query = query.where(f)

        if params.search and search_columns:
            query = query.where(
                or_(*[
                    cast(col, String).ilike(f"%{params.search}%")
                    for col in search_columns
                ])
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        order_col = getattr(model, params.sort_by, None)
        if order_col is not None:
            query = query.order_by(
                desc(order_col) if params.sort_dir == "desc" else asc(order_col)
            )

        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        result = await self._session.execute(query)
        orm_items = result.scalars().all()

        converter = to_domain or (lambda x: x.to_domain())
        items = [converter(item) for item in orm_items]

        return PaginatedResponse(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=-(-total // params.page_size),
        )