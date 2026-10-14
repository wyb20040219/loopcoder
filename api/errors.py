
class AppError(Exception):
    """
    应用级业务异常的基类。

    只描述错误，不负责构造 HTTP 响应。
    """

    def __init__(
        self,
        detail: str,
        status_code: int = 400
    ):
        super().__init__(detail)

        self.detail = detail
        self.status_code = status_code


class RunNotFoundError(AppError):
    """
    查询不到指定 Run 时抛出的异常。
    """

    def __init__(self):
        super().__init__(
            detail="找不到该Run Trace",
            status_code=404
        )
