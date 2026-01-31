"""
Global Error Handler Middleware
Convert exceptions to AWS-style error responses
"""

import uuid
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import CloudSimException
from app.schemas.common import ErrorResponse, ErrorDetail


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to catch all exceptions and convert to standardized error responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle request and catch exceptions"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except CloudSimException as exc:
            # Our custom exceptions - convert to JSON response
            logger.warning(
                f"CloudSim exception: {exc.error_code}",
                extra={
                    "request_id": request_id,
                    "error_code": exc.error_code,
                    "status_code": exc.status_code,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code=exc.error_code,
                    message=exc.message
                ),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=exc.status_code,
                content=error_response.model_dump()
            )
            
        except RequestValidationError as exc:
            # Pydantic validation errors
            logger.warning(
                "Request validation failed",
                extra={
                    "request_id": request_id,
                    "errors": exc.errors(),
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code="ValidationError",
                    message="Request validation failed. Check your input parameters."
                ),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=error_response.model_dump()
            )
            
        except Exception as exc:
            # Unexpected errors - log and return generic error
            logger.exception(
                "Unexpected error occurred",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
            error_response = ErrorResponse(
                error=ErrorDetail(
                    code="InternalError",
                    message="An internal error occurred. Please try again later."
                ),
                request_id=request_id
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump()
            )


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state
    
    Usage in route:
        @app.get("/items")
        def get_items(request: Request):
            request_id = get_request_id(request)
    """
    return getattr(request.state, "request_id", "unknown")
