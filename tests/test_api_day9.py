import pytest

from fastapi.testclient import (
    TestClient,
)

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    sessionmaker,
)

from sqlalchemy.pool import (
    StaticPool,
)

from api.main import (
    app,
)

from db.base import (
    Base,
)

from db.session import (
    get_db,
)


# ==========================================
# 测试专用 SQLite Engine
# ==========================================

test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={
        "check_same_thread":
            False
    },
    poolclass=StaticPool,
)


TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)


# ==========================================
# 每个测试独立数据库
# ==========================================

@pytest.fixture
def client():

    Base.metadata.drop_all(
        bind=test_engine
    )

    Base.metadata.create_all(
        bind=test_engine
    )


    def override_get_db():

        db = TestSessionLocal()

        try:

            yield db

        finally:

            db.close()


    app.dependency_overrides[
        get_db
    ] = override_get_db


    try:

        with TestClient(
            app
        ) as test_client:

            yield test_client

    finally:

        app.dependency_overrides.pop(
            get_db,
            None,
        )


# ==========================================
# 1. Create
# ==========================================

def test_create_db_run(
    client,
):

    response = client.post(
        "/db/runs",
        json={
            "run_id":
                "run-test-001",

            "event_count":
                10,
        },
    )


    assert (
        response.status_code
        ==
        201
    )


    data = response.json()


    assert data[
        "run_id"
    ] == "run-test-001"


    assert data[
        "event_count"
    ] == 10


    assert isinstance(
        data["id"],
        int,
    )


# ==========================================
# 2. List
# ==========================================

def test_list_db_runs(
    client,
):

    client.post(
        "/db/runs",
        json={
            "run_id":
                "run-a",

            "event_count":
                10,
        },
    )


    client.post(
        "/db/runs",
        json={
            "run_id":
                "run-b",

            "event_count":
                20,
        },
    )


    response = client.get(
        "/db/runs"
    )


    assert (
        response.status_code
        ==
        200
    )


    data = response.json()


    assert (
        data["count"]
        ==
        2
    )


    assert (
        len(
            data["records"]
        )
        ==
        2
    )


# ==========================================
# 3. Get One
# ==========================================

def test_get_db_run(
    client,
):

    created = client.post(
        "/db/runs",
        json={
            "run_id":
                "run-get",

            "event_count":
                5,
        },
    ).json()


    record_id = (
        created["id"]
    )


    response = client.get(
        f"/db/runs/{record_id}"
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()["run_id"]
        ==
        "run-get"
    )


# ==========================================
# 4. Update
# ==========================================

def test_update_db_run(
    client,
):

    created = client.post(
        "/db/runs",
        json={
            "run_id":
                "run-update",

            "event_count":
                1,
        },
    ).json()


    record_id = (
        created["id"]
    )


    response = client.patch(
        f"/db/runs/{record_id}",
        json={
            "event_count":
                99
        },
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        response.json()[
            "event_count"
        ]
        ==
        99
    )


# ==========================================
# 5. Delete
# ==========================================

def test_delete_db_run(
    client,
):

    created = client.post(
        "/db/runs",
        json={
            "run_id":
                "run-delete",

            "event_count":
                3,
        },
    ).json()


    record_id = (
        created["id"]
    )


    response = client.delete(
        f"/db/runs/{record_id}"
    )


    assert (
        response.status_code
        ==
        204
    )


    response = client.get(
        f"/db/runs/{record_id}"
    )


    assert (
        response.status_code
        ==
        404
    )


# ==========================================
# 6. Duplicate
# ==========================================

def test_duplicate_run_id(
    client,
):

    payload = {
        "run_id":
            "duplicate-run",

        "event_count":
            1,
    }


    first = client.post(
        "/db/runs",
        json=payload,
    )


    second = client.post(
        "/db/runs",
        json=payload,
    )


    assert (
        first.status_code
        ==
        201
    )


    assert (
        second.status_code
        ==
        409
    )


    assert second.json() == {
        "detail":
            "该run_id已经存在"
    }


# ==========================================
# 7. Validation
# ==========================================

def test_negative_event_count_rejected(
    client,
):

    response = client.post(
        "/db/runs",
        json={
            "run_id":
                "bad-run",

            "event_count":
                -1,
        },
    )


    assert (
        response.status_code
        ==
        422
    )