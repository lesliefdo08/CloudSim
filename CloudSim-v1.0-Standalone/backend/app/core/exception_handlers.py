"""
Global Exception Handlers
Configure FastAPI to return AWS-style error responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import CloudSimException


def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    
    @app.exception_handler(CloudSimException)
    async def cloudsim_exception_handler(request: Request, exc: CloudSimException):
        """Handle CloudSim custom exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": {
                    "error_code": exc.error_code,
                    "message": exc.message,
                    **exc.details
                }
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle standard HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": {
                    "error_code": "HTTPException",
                    "message": exc.detail
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "error_code": "ValidationError",
                    "message": "Request validation failed",
                    "errors": errors
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": {
                    "error_code": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "error": str(exc)
                }
            }
        )
