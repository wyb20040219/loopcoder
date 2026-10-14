
from fastapi import FastAPI, Request

from fastapi.responses import JSONResponse

from api.errors import AppError


def register_exception_handlers(
    app: FastAPI
) -> None:
    """
    给 FastAPI 主应用注册统一业务异常处理器。
    """

    @app.exception_handler(AppError)
    async def handle_app_error(
        request: Request,
        exc: AppError
    ) -> JSONResponse:

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail
            }
        )
