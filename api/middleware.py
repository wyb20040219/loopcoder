import logging
import time
import uuid

from fastapi import (
    FastAPI,
    Request
)


# ==========================================
# Logger
# ==========================================

logger = logging.getLogger(
    "loopcoder.api"
)


# ==========================================
# HTTP Middleware 注册
# ==========================================

def register_http_middleware(
    app: FastAPI
) -> None:

    @app.middleware("http")
    async def request_context_middleware(
        request: Request,
        call_next
    ):

        # ==================================
        # 1. 获取 / 创建 Request ID
        # ==================================

        incoming_request_id = (
            request.headers.get(
                "X-Request-ID"
            )
        )


        request_id = (
            incoming_request_id
            or str(
                uuid.uuid4()
            )
        )


        # 保存到当前 Request 对象
        request.state.request_id = (
            request_id
        )


        # ==================================
        # 2. 开始计时
        # ==================================

        start_time = (
            time.perf_counter()
        )


        logger.info(
            "request_started "
            "request_id=%s "
            "method=%s "
            "path=%s",
            request_id,
            request.method,
            request.url.path
        )


        try:

            # ==============================
            # 3. 把请求继续交给 FastAPI
            # ==============================

            response = await call_next(
                request
            )


        except Exception:

            # ==============================
            # 4. 记录未处理异常
            # ==============================

            duration_ms = (
                time.perf_counter()
                -
                start_time
            ) * 1000


            logger.exception(
                "request_failed "
                "request_id=%s "
                "method=%s "
                "path=%s "
                "duration_ms=%.2f",
                request_id,
                request.method,
                request.url.path,
                duration_ms
            )


            # 不在这里偷偷变成200/400
            # 继续交给FastAPI的错误处理机制
            raise


        # ==================================
        # 5. 请求结束，计算耗时
        # ==================================

        duration_ms = (
            time.perf_counter()
            -
            start_time
        ) * 1000


        # ==================================
        # 6. Response Header 加 Request ID
        # ==================================

        response.headers[
            "X-Request-ID"
        ] = request_id


        # ==================================
        # 7. 记录访问日志
        # ==================================

        logger.info(
            "request_finished "
            "request_id=%s "
            "method=%s "
            "path=%s "
            "status_code=%s "
            "duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms
        )


        return response