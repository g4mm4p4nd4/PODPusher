import asyncio
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from .service import log_event


class AnalyticsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Avoid logging analytics endpoints to prevent recursion
        if not request.url.path.startswith(("/analytics", "/api/analytics")):
            asyncio.create_task(log_event("page_view", request.url.path))
        return response
