from sqlalchemy.exc import (
    SQLAlchemyError
)

from fastapi.testclient import (
    TestClient
)

from api.main import app

from db.models import (
    RunRecord
)

from db.session import (
    get_db
)


client = TestClient(app)


# ==========================================
# Fake SQL Result
# ==========================================

class FakeResult:

    def scalar_one(self):

        return 1


# ==========================================
# Fake Session
# ==========================================

class FakeSession:

    def __init__(self):

        self.executed = False


    def execute(
        self,
        statement
    ):

        self.executed = True

        return FakeResult()


# ==========================================
# 1. Database Health
# ==========================================

def test_database_health():

    fake_db = FakeSession()


    app.dependency_overrides[
        get_db
    ] = lambda: fake_db


    try:

        response = client.get(
            "/health/db"
        )


        assert (
            response.status_code
            ==
            200
        )


        assert (
            fake_db.executed
            is True
        )


        assert response.json() == {
            "status": "ready",
            "database": "mysql",
            "check": True
        }


    finally:

        app.dependency_overrides.pop(
            get_db,
            None
        )


# ==========================================
# 2. Database Failure → 503
# ==========================================

def test_database_health_failure():

    class BrokenSession:

        def execute(
            self,
            statement
        ):

            raise SQLAlchemyError(
                "database unavailable"
            )


    app.dependency_overrides[
        get_db
    ] = lambda: BrokenSession()


    try:

        response = client.get(
            "/health/db"
        )


        assert (
            response.status_code
            ==
            503
        )


        assert response.json() == {
            "detail":
                (
                    "MySQL数据库"
                    "暂时无法访问"
                )
        }


    finally:

        app.dependency_overrides.pop(
            get_db,
            None
        )


# ==========================================
# 3. ORM Table Name
# ==========================================

def test_run_record_table_name():

    assert (
        RunRecord.__tablename__
        ==
        "run_records"
    )


# ==========================================
# 4. ORM Columns
# ==========================================

def test_run_record_columns():

    column_names = {
        column.name

        for column
        in RunRecord.__table__.columns
    }


    assert column_names == {
        "id",
        "run_id",
        "event_count",
        "created_at"
    }


# ==========================================
# 5. OpenAPI
# ==========================================

def test_openapi_has_database_health():

    response = client.get(
        "/openapi.json"
    )


    assert (
        response.status_code
        ==
        200
    )


    assert (
        "/health/db"
        in response.json()["paths"]
    )