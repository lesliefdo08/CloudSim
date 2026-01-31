"""
Common Pydantic Schemas
Reusable response models and pagination schemas
"""

from typing import TypeVar, Generic, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Generic type for paginated responses
T = TypeVar('T')


class ErrorDetail(BaseModel):
    """AWS-style error detail"""
    code: str = Field(..., description="Error code (e.g., InvalidParameterValue)")
    message: str = Field(..., description="Human-readable error message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "InvalidParameterValue",
                "message": "Invalid value 'stopped' for parameter 'state'"
            }
        }
    )


class SuccessResponse(BaseModel):
    """Generic success response"""
    
    success: bool = True
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: ErrorDetail
    request_id: str = Field(..., description="Unique request ID for debugging")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "ResourceNotFound",
                    "message": "Instance 'i-0123456789' not found"
                },
                "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
            }
        }
    )


class PaginationParams(BaseModel):
    """Query parameters for pagination"""
    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias for page_size"""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response
    
    Usage:
        PaginatedResponse[InstanceSchema](
            items=[...],
            total=100,
            page=1,
            page_size=20
        )
    """
    items: list[T] = Field(..., description="List of items in current page")
    total: int = Field(..., description="Total number of items across all pages")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(cls, items: list[T], total: int, pagination: PaginationParams) -> "PaginatedResponse[T]":
        """
        Factory method to create paginated response
        
        Args:
            items: List of items for current page
            total: Total count of items
            pagination: Pagination parameters
        
        Returns:
            PaginatedResponse with calculated metadata
        """
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        
        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )


class ResourceTags(BaseModel):
    """Resource tags (key-value pairs)"""
    key: str = Field(..., min_length=1, max_length=128)
    value: str = Field(..., max_length=256)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "Environment",
                "value": "Production"
            }
        }
    )


class TimestampMixin(BaseModel):
    """Mixin for created_at/updated_at timestamps"""
    created_at: datetime = Field(..., description="Resource creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Resource last update timestamp (UTC)")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status (healthy/unhealthy)")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Current server time")
    services: dict[str, str] = Field(default_factory=dict, description="Status of dependent services")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-31T12:00:00Z",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "docker": "healthy"
                }
            }
        }
    )


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[dict[str, Any]] = Field(None, description="Additional response data")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Instance started successfully",
                "data": {"instance_id": "i-0123456789"}
            }
        }
    )


class FilterParam(BaseModel):
    """Generic filter parameter for list operations"""
    name: str = Field(..., description="Filter name (e.g., 'instance-state-name')")
    values: list[str] = Field(..., description="Filter values")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "instance-state-name",
                "values": ["running", "stopped"]
            }
        }
    )
