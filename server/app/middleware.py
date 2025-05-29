from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as http_exception:
        # you probably want some kind of logging here
        print(http_exception)
        return JSONResponse(
            status_code=http_exception.status_code,
            content={"detail": http_exception.detail},
        )
    except Exception as e:
        # you probably want some kind of logging here
        print(e)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
