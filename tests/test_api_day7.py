import inspect

from fastapi.testclient import (
    TestClient
)

from api.main import app

import api.routers.system as system_module


import api.routers.runs as runs_module



client = TestClient(app)


# ==========================================
# 1. Health 仍然正常
# ==========================================

def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status":
            "ok",

        "service":
            "loopcoder-control-plane"
    }


# ==========================================
# 2. Readiness 正常
# ==========================================

def test_readiness(
    monkeypatch
):

    monkeypatch.setattr(
        system_module,
        "get_overview",
        lambda: {
            "goal": None
        }
    )


    response = client.get(
        "/health/ready"
    )


    assert response.status_code == 200


    assert response.json() == {
        "status":
            "ready",

        "service":
            "loopcoder-control-plane",

        "control_plane_readable":
            True
    }


# ==========================================
# 3. Control Plane 失败 → 503
# ==========================================

def test_readiness_failure(
    monkeypatch
):

    def broken_overview():

        raise OSError(
            "模拟文件系统异常"
        )


    monkeypatch.setattr(
        system_module,
        "get_overview",
        broken_overview
    )


    response = client.get(
        "/health/ready"
    )


    assert response.status_code == 503


    assert response.json() == {
        "detail":
            (
                "Control Plane数据"
                "暂时无法读取"
            )
    }


# ==========================================
# 4. Health 是 async path operation
# ==========================================

def test_health_is_async():

    assert (
        inspect.iscoroutinefunction(
            system_module.health
        )
        is True
    )


# ==========================================
# 5. Readiness 是 async
# ==========================================

def test_readiness_is_async():

    assert (
        inspect.iscoroutinefunction(
            system_module.readiness
        )
        is True
    )


# ==========================================
# 6. 现有同步文件访问接口仍保持 sync
# ==========================================

def test_runs_route_remains_sync():

    assert (
        inspect.iscoroutinefunction(
            runs_module.runs
        )
        is False
    )


# ==========================================
# 7. OpenAPI 包含 readiness
# ==========================================

def test_openapi_has_readiness():

    response = client.get(
        "/openapi.json"
    )

    assert response.status_code == 200

    paths = response.json()[
        "paths"
    ]

    assert (
        "/health/ready"
        in paths
    )

    assert (
        "get"
        in paths[
            "/health/ready"
        ]
    )