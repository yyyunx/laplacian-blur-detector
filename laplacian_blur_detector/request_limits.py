"""Streaming ASGI request limits, including uploads without Content-Length."""

from starlette.responses import JSONResponse
from starlette.formparsers import MultiPartException
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class _BodyTooLarge(MultiPartException):
    pass


class UploadBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, limits: dict[str, int]):
        self.app = app
        self.limits = limits

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        limit = self.limits.get(scope.get("path", ""))
        if scope["type"] != "http" or scope.get("method") != "POST" or limit is None:
            await self.app(scope, receive, send)
            return
        response_started = False
        exceeded = False
        consumed = 0

        async def limited_receive() -> Message:
            nonlocal consumed, exceeded
            message = await receive()
            if message["type"] == "http.request":
                consumed += len(message.get("body", b""))
                if consumed > limit:
                    exceeded = True
                    raise _BodyTooLarge("Upload request is too large.")
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal response_started
            # Multipart parsers may convert a receive exception to HTTP 400.
            # Suppress that response and send the actual 413 below.
            if not exceeded:
                if message["type"] == "http.response.start":
                    response_started = True
                await send(message)

        async def reject() -> None:
            await JSONResponse({
                "detail": "Upload request is too large. Send fewer or smaller images.",
                "error_code": "REQUEST_TOO_LARGE",
            }, status_code=413)(scope, receive, send)

        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length")
        if length is not None:
            try:
                if int(length) > limit:
                    await reject()
                    return
            except ValueError:
                pass  # The streaming byte count still applies.
        try:
            await self.app(scope, limited_receive, guarded_send)
        except _BodyTooLarge:
            if not exceeded:
                raise
        except Exception:
            if not exceeded:
                raise
        if exceeded and not response_started:
            await reject()
