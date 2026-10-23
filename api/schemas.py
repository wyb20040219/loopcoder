from datetime import datetime

from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ==========================================
# Health
# ==========================================

class HealthResponse(BaseModel):

    status: Literal["ok"]

    service: str


class ReadinessResponse(BaseModel):

    status: Literal["ready"]

    service: str

    control_plane_readable: bool


class DatabaseHealthResponse(
    BaseModel
):

    status: Literal["ready"]

    database: Literal["mysql"]

    check: bool


# ==========================================
# 原文件系统 Run Schema
# ==========================================

class RunSummary(BaseModel):

    run_id: str

    file_name: str

    started_at: str | None

    ended_at: str | None

    event_count: int = Field(
        ge=0
    )

    event_counts: dict[str, int]


class RunsResponse(BaseModel):

    count: int = Field(
        ge=0
    )

    runs: list[RunSummary]


class RunDetailResponse(BaseModel):

    summary: RunSummary

    events: list[
        dict[str, Any]
    ]


class RunSearchRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    min_event_count: int = Field(
        default=0,
        ge=0,
    )

    run_id_contains: str | None = Field(
        default=None,
        min_length=1,
        max_length=80,
    )


    @field_validator(
        "run_id_contains"
    )
    @classmethod
    def normalize_run_id_contains(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:

            return None


        value = value.strip()


        if not value:

            raise ValueError(
                "run_id_contains 不能只包含空格"
            )


        return value


# ==========================================
# Day 9：数据库 Run CRUD
# ==========================================

class DbRunCreateRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    run_id: str = Field(
        min_length=1,
        max_length=128,
    )

    event_count: int = Field(
        default=0,
        ge=0,
    )


class DbRunUpdateRequest(
    BaseModel
):

    model_config = ConfigDict(
        extra="forbid"
    )

    event_count: int = Field(
        ge=0
    )


class DbRunResponse(
    BaseModel
):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    run_id: str

    event_count: int

    created_at: datetime


class DbRunListResponse(
    BaseModel
):

    count: int = Field(
        ge=0
    )

    records: list[
        DbRunResponse
    ]