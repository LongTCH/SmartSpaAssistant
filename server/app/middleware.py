import logging

from app.exceptions.custom_exception import BaseCustomException
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse

# Configure logging
logger = logging.getLogger(__name__)


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except BaseCustomException as custom_exception:
        # Log custom exceptions with appropriate level
        logger.warning(
            f"Custom exception: {custom_exception.message}",
            extra={
                "exception_type": custom_exception.__class__.__name__,
                "status_code": custom_exception.status_code,
                "details": custom_exception.details,
                "path": request.url.path,
            },
        )
        return JSONResponse(
            status_code=custom_exception.status_code,
            content=custom_exception.to_dict(),
        )
    except HTTPException as http_exception:
        # Log HTTP exceptions
        logger.warning(
            f"HTTP exception: {http_exception.detail}",
            extra={"status_code": http_exception.status_code, "path": request.url.path},
        )
        return JSONResponse(
            status_code=http_exception.status_code,
            content={"detail": http_exception.detail},
        )
    except Exception as e:
        # Log unexpected exceptions as errors
        logger.error(
            f"Unexpected exception: {str(e)}",
            extra={"exception_type": e.__class__.__name__, "path": request.url.path},
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Internal server error",
                "status_code": 500,
                "details": {},
            },
        )
