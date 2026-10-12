
import pytest

from fastapi.testclient import TestClient

from api.main import app
from control_api import app as legacy_app

import api.routers.runs as runs_module
import api.routers.control as control_module
import api.routers.dashboard as dashboard_module
import run_search_service


client = TestClient(app)


# 模拟真实的 Run 摘要
SAMPLE_RUNS = [
    {
        "run_id": "alpha-001",
        "file_name": "alpha-001.jsonl",
        "started_at": None,
        "ended_at": None,
        "event_count": 12,
        "event_counts": {
            "tool_result": 3
        }
    },
    {
        "run_id": "beta-002",
        "file_name": "beta-002.jsonl",
        "started_at": None,
        "ended_at": None,
        "event_count": 2,
        "event_counts": {
            "tool_result": 1
        }
    },
    {
        "run_id": "alpha-003",
        "file_name": "alpha-003.jsonl",
        "started_at": None,
        "ended_at": None,
        "event_count": 8,
        "event_counts": {
            "tool_result": 2
        }
    }
]


# ==========================================
# 原有 API 回归测试
# ==========================================

def test_health():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok",
        "service": "loopcoder-control-plane"
    }


def test_legacy_entrypoint():

    assert legacy_app is app


def test_original_get_routes():

    expected_paths = {
        "/health",
        "/control/overview",
        "/goals/active",
        "/goals/active/todos",
        "/quota/current",
        "/evidence/current",
        "/attention/current",
        "/acceptance/current",
        "/runs",
        "/runs/{run_id}",
        "/runs/{run_id}/metrics",
        "/dashboard"
    }

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    for path in expected_paths:

        assert path in paths
        assert "get" in paths[path]

    # 新增的 POST 接口
    assert "post" in paths["/runs/search"]


def test_runs_query_parameter(monkeypatch):

    captured = {}

    def fake_get_run_history(limit):

        captured["limit"] = limit

        return SAMPLE_RUNS[:1]

    monkeypatch.setattr(
        runs_module,
        "get_run_history",
        fake_get_run_history
    )

    response = client.get("/runs?limit=5")

    assert response.status_code == 200

    assert captured["limit"] == 5

    assert response.json() == {
        "count": 1,
        "runs": SAMPLE_RUNS[:1]
    }


@pytest.mark.parametrize(
    "limit",
    ["0", "101", "abc"]
)
def test_runs_invalid_limit(limit):

    response = client.get(
        f"/runs?limit={limit}"
    )

    assert response.status_code == 422


def test_run_detail_parameters(monkeypatch):

    captured = {}

    def fake_get_run_detail(
        run_id,
        event_limit
    ):

        captured["run_id"] = run_id
        captured["event_limit"] = event_limit

        return {
            "summary": SAMPLE_RUNS[0],
            "events": [
                {"event_type": "tool_result"}
            ]
        }

    monkeypatch.setattr(
        runs_module,
        "get_run_detail",
        fake_get_run_detail
    )

    response = client.get(
        "/runs/alpha-001?event_limit=10"
    )

    assert response.status_code == 200

    assert captured == {
        "run_id": "alpha-001",
        "event_limit": 10
    }

    assert (
        response.json()["summary"]["run_id"]
        == "alpha-001"
    )


def test_run_not_found(monkeypatch):

    monkeypatch.setattr(
        runs_module,
        "get_run_detail",
        lambda run_id, event_limit: None
    )

    response = client.get(
        "/runs/missing-run"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "找不到该Run Trace"
    )


def test_metrics_not_found(monkeypatch):

    monkeypatch.setattr(
        runs_module,
        "build_run_metrics",
        lambda run_id: None
    )

    response = client.get(
        "/runs/missing-run/metrics"
    )

    assert response.status_code == 404


def test_dashboard_service(monkeypatch):

    monkeypatch.setattr(
        dashboard_module,
        "build_dashboard",
        lambda: {
            "system_state": "IDLE",
            "goal": None
        }
    )

    response = client.get("/dashboard")

    assert response.status_code == 200

    assert (
        response.json()["system_state"]
        == "IDLE"
    )


def test_goal_not_found(monkeypatch):

    monkeypatch.setattr(
        control_module,
        "get_active_goal",
        lambda: None
    )

    response = client.get(
        "/goals/active"
    )

    assert response.status_code == 404


# ==========================================
# Day 3：请求模型与搜索业务
# ==========================================

def test_search_filters_and_uses_service(
    monkeypatch
):

    called = {}

    def fake_get_run_history(limit):

        called["limit"] = limit

        return SAMPLE_RUNS

    monkeypatch.setattr(
        run_search_service,
        "get_run_history",
        fake_get_run_history
    )

    response = client.post(
        "/runs/search",
        json={
            "limit": 5,
            "min_event_count": 10,
            "run_id_contains": "ALPHA"
        }
    )

    assert response.status_code == 200

    # Service 从 Store 查询最近100条
    assert called["limit"] == 100

    # 只有 alpha-001 同时满足两个筛选条件
    assert response.json() == {
        "count": 1,
        "runs": [
            SAMPLE_RUNS[0]
        ]
    }


def test_search_empty_history(monkeypatch):

    monkeypatch.setattr(
        run_search_service,
        "get_run_history",
        lambda limit: []
    )

    response = client.post(
        "/runs/search",
        json={}
    )

    assert response.status_code == 200

    assert response.json() == {
        "count": 0,
        "runs": []
    }


@pytest.mark.parametrize(
    "payload",
    [
        {"limit": 0},
        {"limit": 101},
        {"limit": "abc"},
        {"min_event_count": -1},
        {"run_id_contains": ""},
        {"run_id_contains": "   "},
        {"unrecognized_field": True}
    ]
)
def test_search_invalid_request(payload):

    response = client.post(
        "/runs/search",
        json=payload
    )

    assert response.status_code == 422


# ==========================================
# Day 3：响应模型验证
# ==========================================

def test_response_model_removes_extra_fields(
    monkeypatch
):

    internal_record = {
        **SAMPLE_RUNS[0],
        "internal_debug_note": "should-not-be-exposed"
    }

    monkeypatch.setattr(
        runs_module,
        "get_run_history",
        lambda limit: [internal_record]
    )

    response = client.get(
        "/runs?limit=1"
    )

    assert response.status_code == 200

    # 没在 RunSummary 里声明的额外字段
    # 不应该出现在最终响应中
    assert (
        "internal_debug_note"
        not in response.json()["runs"][0]
    )


def test_openapi_models_exist():

    response = client.get("/openapi.json")

    schemas = response.json()[
        "components"
    ]["schemas"]

    assert "RunSearchRequest" in schemas

    assert "RunsResponse" in schemas

    assert "HealthResponse" in schemas
