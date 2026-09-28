import os
import threading
import time


# ==========================================
# 全进程共享
#
# Bare Agent 和 LoopCoder
# import的是同一个Python模块实例，
# 所以会共享下面这些状态。
# ==========================================

_lock = threading.Lock()

_last_request_time: float | None = None

_total_wait_seconds: float = 0.0


# ==========================================
# 获取最小请求间隔
# ==========================================

def get_min_interval_seconds() -> float:

    raw = (
        os.getenv(
            "AGENT_LLM_MIN_INTERVAL_SECONDS",
            "0"
        )
        .strip()
    )


    try:

        value = float(
            raw
        )


    except ValueError:

        value = 0.0


    return max(
        0.0,
        value
    )


# ==========================================
# 调LLM之前先申请一个Request Slot
# ==========================================

def wait_for_llm_slot() -> float:

    global _last_request_time
    global _total_wait_seconds


    min_interval = (
        get_min_interval_seconds()
    )


    # ======================================
    # 普通开发模式：
    #
    # 没配置限速就立即执行
    # ======================================

    if min_interval <= 0:

        return 0.0


    with _lock:

        now = (
            time.monotonic()
        )


        wait_seconds = 0.0


        if (
            _last_request_time
            is not None
        ):

            elapsed = (
                now
                -
                _last_request_time
            )


            wait_seconds = max(

                0.0,

                min_interval
                -
                elapsed
            )


        if wait_seconds > 0:

            print(

                "\n[LLM Rate Limiter] "
                f"主动等待 "
                f"{wait_seconds:.1f} 秒..."
            )


            time.sleep(
                wait_seconds
            )


        # ==================================
        # 记录“真正准备发请求”的时刻
        # ==================================

        _last_request_time = (
            time.monotonic()
        )


        _total_wait_seconds += (
            wait_seconds
        )


        return wait_seconds


# ==========================================
# Benchmark统计：
#
# 到目前为止因为主动限速
# 总共等了多少秒
# ==========================================

def get_total_wait_seconds() -> float:

    with _lock:

        return (
            _total_wait_seconds
        )


# ==========================================
# 测试时可以重置
# ==========================================

def reset_rate_limiter():

    global _last_request_time
    global _total_wait_seconds


    with _lock:

        _last_request_time = None

        _total_wait_seconds = 0.0