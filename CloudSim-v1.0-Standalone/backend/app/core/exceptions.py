"""
CloudSim Custom Exceptions
AWS-style error responses with proper error codes
"""

from typing import Optional, Any


class CloudSimException(Exception):
    """Base exception for all CloudSim errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Errors

class AuthenticationError(CloudSimException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AuthenticationFailure",
            status_code=401
        )


class UnauthorizedError(CloudSimException):
    """User not authorized for action"""
    def __init__(self, message: str = "You are not authorized to perform this action"):
        super().__init__(
            message=message,
            error_code="UnauthorizedOperation",
            status_code=403
        )


class InvalidCredentialsError(CloudSimException):
    """Invalid access key or secret"""
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            error_code="InvalidClientTokenId",
            status_code=403
        )


# Resource Errors

class ResourceNotFoundError(CloudSimException):
    """Resource does not exist"""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"The {resource_type} '{resource_id}' does not exist",
            error_code=f"{resource_type}.NotFound",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class ResourceAlreadyExistsError(CloudSimException):
    """Resource already exists with that identifier"""
    def __init__(self, resource_type: str, identifier: str):
        super().__init__(
            message=f"The {resource_type} '{identifier}' already exists",
            error_code=f"{resource_type}.Duplicate",
            status_code=409,
            details={"resource_type": resource_type, "identifier": identifier}
        )


# Alias for backward compatibility
ConflictError = ResourceAlreadyExistsError


class InvalidParameterError(CloudSimException):
    """Invalid parameter value"""
    def __init__(self, parameter: str, value: Any, reason: str):
        super().__init__(
            message=f"Invalid value '{value}' for parameter '{parameter}': {reason}",
            error_code="InvalidParameterValue",
            status_code=400,
            details={"parameter": parameter, "value": str(value), "reason": reason}
        )


class InvalidParameterCombinationError(CloudSimException):
    """Invalid combination of parameters"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="InvalidParameterCombination",
            status_code=400
        )


# State Errors

class InvalidInstanceStateError(CloudSimException):
    """Operation not valid in current instance state"""
    def __init__(self, instance_id: str, current_state: str, required_state: str):
        super().__init__(
            message=f"Instance '{instance_id}' is in '{current_state}' state. This operation requires '{required_state}' state.",
            error_code="IncorrectInstanceState",
            status_code=400,
            details={
                "instance_id": instance_id,
                "current_state": current_state,
                "required_state": required_state
            }
        )


class ResourceInUseError(CloudSimException):
    """Resource is in use and cannot be modified/deleted"""
    def __init__(self, resource_type: str, resource_id: str, reason: str):
        super().__init__(
            message=f"The {resource_type} '{resource_id}' is in use: {reason}",
            error_code=f"{resource_type}.InUse",
            status_code=400,
            details={"resource_type": resource_type, "resource_id": resource_id, "reason": reason}
        )


# Limit Errors

class LimitExceededError(CloudSimException):
    """Service limit exceeded"""
    def __init__(self, resource_type: str, limit: int, current: int):
        super().__init__(
            message=f"You have reached the limit of {limit} {resource_type}(s). Current count: {current}",
            error_code="ResourceLimitExceeded",
            status_code=400,
            details={"resource_type": resource_type, "limit": limit, "current": current}
        )


class InsufficientCapacityError(CloudSimException):
    """Not enough capacity to fulfill request"""
    def __init__(self, message: str = "Insufficient capacity to fulfill request"):
        super().__init__(
            message=message,
            error_code="InsufficientInstanceCapacity",
            status_code=503
        )


# Dependency Errors

class DependencyViolationError(CloudSimException):
    """Cannot perform operation due to dependent resources"""
    def __init__(self, resource_type: str, resource_id: str, dependents: list[str]):
        super().__init__(
            message=f"Cannot delete {resource_type} '{resource_id}' because it has dependent resources: {', '.join(dependents)}",
            error_code="DependencyViolation",
            status_code=400,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "dependents": dependents
            }
        )


# Validation Errors

class ValidationError(CloudSimException):
    """Request validation failed"""
    def __init__(self, errors: list[dict[str, Any]]):
        super().__init__(
            message="Request validation failed",
            error_code="ValidationError",
            status_code=422,
            details={"errors": errors}
        )


# Docker/Container Errors

class ContainerError(CloudSimException):
    """Docker container operation failed"""
    def __init__(self, message: str, container_id: Optional[str] = None):
        super().__init__(
            message=f"Container operation failed: {message}",
            error_code="ContainerError",
            status_code=500,
            details={"container_id": container_id} if container_id else {}
        )


# Storage Errors

class StorageError(CloudSimException):
    """Storage operation failed"""
    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(
            message=f"Storage error: {message}",
            error_code="StorageError",
            status_code=500,
            details=details or {}
        )


# Internal Errors

class InternalServiceError(CloudSimException):
    """Internal service error"""
    def __init__(self, message: str = "An internal error occurred"):
        super().__init__(
            message=message,
            error_code="InternalError",
            status_code=500
        )


class ServiceUnavailableError(CloudSimException):
    """Service temporarily unavailable"""
    def __init__(self, message: str = "Service is temporarily unavailable"):
        super().__init__(
            message=message,
            error_code="ServiceUnavailable",
            status_code=503
        )
