
from collections.abc import Callable

import run_search_service


# 业务搜索函数的类型
RunSearchCallable = Callable[..., list[dict]]


def get_run_search_service() -> RunSearchCallable:
    """
    提供运行历史搜索函数。

    FastAPI 通过 Depends 调用它。
    测试时可以替换这个依赖。
    """

    return run_search_service.search_runs
