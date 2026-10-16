class AppError(Exception):

    def __init__(
        self,
        detail: str,
        status_code: int = 400
    ):

        super().__init__(
            detail
        )

        self.detail = detail

        self.status_code = (
            status_code
        )


# ==========================================
# Run 不存在
# ==========================================

class RunNotFoundError(
    AppError
):

    def __init__(
        self
    ):

        super().__init__(
            detail=(
                "找不到该Run Trace"
            ),
            status_code=404
        )


# ==========================================
# 服务尚未准备好
# ==========================================

class ServiceUnavailableError(
    AppError
):

    def __init__(
        self,
        detail: str
        =
        "服务暂时不可用"
    ):

        super().__init__(
            detail=detail,
            status_code=503
        )