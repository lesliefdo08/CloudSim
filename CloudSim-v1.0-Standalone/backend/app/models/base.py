"""
SQLAlchemy Base Model
Base class for all database models with common fields
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when record was last updated"
    )


class ResourceMixin(TimestampMixin):
    """
    Mixin for AWS resource models
    Includes common fields for all AWS resources
    """
    
    # Resource ARN
    arn: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
        comment="Amazon Resource Name (ARN)"
    )
    
    # Owner information
    account_id: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
        comment="AWS account ID that owns this resource"
    )
    
    region: Mapped[str] = mapped_column(
        nullable=False,
        index=True,
        comment="AWS region where resource exists"
    )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
