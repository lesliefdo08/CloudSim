"""
Pagination Utilities
Helper functions for paginated responses
"""

from typing import TypeVar, Generic, Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.common import PaginationParams, PaginatedResponse


T = TypeVar('T')


async def paginate_query(
    db: AsyncSession,
    query: Select,
    pagination: PaginationParams,
    model_class: type[T]
) -> PaginatedResponse[T]:
    """
    Execute paginated query and return results
    
    Args:
        db: Database session
        query: SQLAlchemy select query (without limit/offset)
        pagination: Pagination parameters
        model_class: Pydantic model class for items
    
    Returns:
        PaginatedResponse with items and metadata
    
    Example:
        query = select(Instance).where(Instance.state == "running")
        result = await paginate_query(db, query, pagination, InstanceSchema)
    """
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0
    
    # Get paginated items
    paginated_query = query.limit(pagination.limit).offset(pagination.offset)
    result = await db.execute(paginated_query)
    items = result.scalars().all()
    
    # Convert to Pydantic models
    pydantic_items = [model_class.model_validate(item) for item in items]
    
    return PaginatedResponse.create(
        items=pydantic_items,
        total=total,
        pagination=pagination
    )


def apply_filters(query: Select, filters: dict) -> Select:
    """
    Apply filters to SQLAlchemy query
    
    Args:
        query: Base query
        filters: Dictionary of field -> value filters
    
    Returns:
        Query with filters applied
    
    Example:
        query = select(Instance)
        query = apply_filters(query, {"state": "running", "instance_type": "t2.micro"})
    """
    for field, value in filters.items():
        if value is not None:
            query = query.where(getattr(query.column_descriptions[0]['entity'], field) == value)
    
    return query
