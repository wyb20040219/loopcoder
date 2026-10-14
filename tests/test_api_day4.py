
import pytest

from fastapi import FastAPI

from fastapi.testclient import TestClient

from api.main import app

from api.dependencies import (
    get_run_search_service
)

from api.errors import (
    AppError
)

from api.handlers import (
    register_exception_handlers
)

import api.routers.runs as runs_module


client = TestClient(app)


# ==========================================
# 测试使用的假 Run 数据
# ==========================================

SAMPLE_RUN = {
    "run_id": "demo-001",
    "file_name": "demo-001.jsonl",
    "started_at": None,
    "ended_at": None,
    "event_count": 12,
    "event_counts": {
        "tool_result": 3
    }
}


# ==========================================
# 1. 测试依赖注入
# ==========================================

def test_dependency_override():

    captured = {}

    def fake_search_service(
        *,
        limit,
        min_event_count,
        run_id_contains
    ):

        captured["limit"] = limit

        captured["min_event_count"] = (
            min_event_count
        )

        captured["run_id_contains"] = (
            run_id_contains
        )

        return [SAMPLE_RUN]

    # 临时替换 Depends 的依赖提供者
    app.dependency_overrides[
        get_run_search_service
    ] = lambda: fake_search_service

    try:

        response = client.post(
            "/runs/search",
            json={
                "limit": 5,
                "min_event_count": 10,
                "run_id_contains": "demo"
            }
        )

        assert response.status_code == 200

        assert captured == {
            "limit": 5,
            "min_event_count": 10,
            "run_id_contains": "demo"
        }

        assert response.json() == {
            "count": 1,
            "runs": [SAMPLE_RUN]
        }

    finally:

        # 测试结束，恢复默认依赖
        app.dependency_overrides.pop(
            get_run_search_service,
            None
        )


# ==========================================
# 2. 请求校验失败时，业务函数不能执行
# ==========================================

def test_invalid_request_blocks_search():

    calls = {
        "count": 0
    }

    def fake_search_service(
        *,
        limit,
        min_event_count,
        run_id_contains
    ):

        calls["count"] += 1

        return []

    app.dependency_overrides[
        get_run_search_service
    ] = lambda: fake_search_service

    try:

        response = client.post(
            "/runs/search",
            json={
                "limit": 0
            }
        )

        assert response.status_code == 422

        # 无效请求不会执行搜索业务
        assert calls["count"] == 0

    finally:

        app.dependency_overrides.pop(
            get_run_search_service,
            None
        )


# ==========================================
# 3. 响应模型仍然生效
# ==========================================

def test_response_model_filters_fields():

    def fake_search_service(
        *,
        limit,
        min_event_count,
        run_id_contains
    ):

        return [
            {
                **SAMPLE_RUN,
                "internal_secret": "hidden"
            }
        ]

    app.dependency_overrides[
        get_run_search_service
    ] = lambda: fake_search_service

    try:

        response = client.post(
            "/runs/search",
            json={}
        )

        assert response.status_code == 200

        result = response.json()["runs"][0]

        assert result["run_id"] == "demo-001"

        assert "internal_secret" not in result

    finally:

        app.dependency_overrides.pop(
            get_run_search_service,
            None
        )


# ==========================================
# 4. 不存在的 Run 返回原有 404 格式
# ==========================================

def test_run_not_found_contract(monkeypatch):

    monkeypatch.setattr(
        runs_module,
        "get_run_detail",
        lambda run_id, event_limit: None
    )

    response = client.get(
        "/runs/missing-run"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "找不到该Run Trace"
    }


# ==========================================
# 5. 不存在的 Metrics 返回相同 404
# ==========================================

def test_metrics_not_found_contract(
    monkeypatch
):

    monkeypatch.setattr(
        runs_module,
        "build_run_metrics",
        lambda run_id: None
    )

    response = client.get(
        "/runs/missing-run/metrics"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "找不到该Run Trace"
    }


# ==========================================
# 6. 测试统一异常处理器
# ==========================================

def test_unified_app_error_handler():

    # 创建一个只用于测试的小应用
    test_app = FastAPI()

    register_exception_handlers(test_app)

    @test_app.get("/test-error")
    def raise_business_error():

        raise AppError(
            detail="当前操作不允许",
            status_code=409
        )

    test_client = TestClient(test_app)

    response = test_client.get(
        "/test-error"
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "当前操作不允许"
    }


# ==========================================
# 7. 检查依赖提供者没有变成HTTP参数
# ==========================================

def test_dependency_not_exposed_as_parameter():

    response = client.get("/openapi.json")

    assert response.status_code == 200

    operation = response.json()["paths"][
        "/runs/search"
    ]["post"]

    request_body = operation["requestBody"]

    schema_ref = (
        request_body["content"]
        ["application/json"]
        ["schema"]["$ref"]
    )

    assert schema_ref.endswith(
        "/RunSearchRequest"
    )


# ==========================================
# 8. 未处理的程序错误不能被伪装成404
# ==========================================

def test_unexpected_error_not_converted_to_404():

    def broken_service(
        *,
        limit,
        min_event_count,
        run_id_contains
    ):

        raise RuntimeError(
            "模拟内部程序错误"
        )

    app.dependency_overrides[
        get_run_search_service
    ] = lambda: broken_service

    try:

        # 禁止TestClient直接把服务端异常
        # 抛到测试代码中，改为观察HTTP响应
        error_client = TestClient(
            app,
            raise_server_exceptions=False
        )

        response = error_client.post(
            "/runs/search",
            json={}
        )

        assert response.status_code == 500

    finally:

        app.dependency_overrides.pop(
            get_run_search_service,
            None
        )
