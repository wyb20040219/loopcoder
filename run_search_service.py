
from control_store import get_run_history


def search_runs(
    *,
    limit: int,
    min_event_count: int,
    run_id_contains: str | None
) -> list[dict]:

    """
    从最近最多100条Run中筛选记录。

    不启动Agent。
    不修改Goal。
    不写入Trace。
    """

    # 1. 从 Store 获取最近100条历史记录
    recent_runs = get_run_history(
        limit=100
    )

    # 2. 统一大小写，方便匹配
    keyword = (
        run_id_contains or ""
    ).casefold()

    results = []

    # 3. 遍历历史 Run
    for record in recent_runs:

        run_id = str(
            record.get("run_id", "")
        )

        # 如果用户指定了Run ID关键词
        if (
            keyword
            and keyword not in run_id.casefold()
        ):
            continue

        # 过滤事件数量不足的记录
        if (
            record.get("event_count", 0)
            < min_event_count
        ):
            continue

        # 记录符合筛选条件
        results.append(record)

        # 最多返回 limit 条
        if len(results) >= limit:
            break

    return results
