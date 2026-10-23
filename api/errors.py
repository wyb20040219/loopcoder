class AppError(Exception):

    def __init__(
        self,
        detail: str,
        status_code: int = 400,
    ):

        super().__init__(detail)

        self.detail = detail
        self.status_code = status_code


# ==========================================
# 原文件 Trace Run 不存在
# ==========================================

class RunNotFoundError(
    AppError
):

    def __init__(
        self,
    ):

        super().__init__(
            detail="找不到该Run Trace",
            status_code=404,
        )


# ==========================================
# 服务不可用
# ==========================================

class ServiceUnavailableError(
    AppError
):

    def __init__(
        self,
        detail: str = "服务暂时不可用",
    ):

        super().__init__(
            detail=detail,
            status_code=503,
        )


# ==========================================
# 数据库 Run Record 不存在
# ==========================================

class RunRecordNotFoundError(
    AppError
):

    def __init__(
        self,
    ):

        super().__init__(
            detail="找不到该数据库Run记录",
            status_code=404,
        )


# ==========================================
# 数据库 Run ID 重复
# ==========================================

class RunRecordConflictError(
    AppError
):

    def __init__(
        self,
    ):

        super().__init__(
            detail="该run_id已经存在",
            status_code=409,
        )