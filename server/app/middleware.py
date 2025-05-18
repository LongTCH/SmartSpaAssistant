from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import Response


async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except HTTPException as http_exception:
        # you probably want some kind of logging here
        print(http_exception)
        return Response(http_exception.detail, status_code=http_exception.status_code)
    except Exception as e:
        # you probably want some kind of logging here
        print(e)
        return Response("Internal server error", status_code=500)
