from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)


# ==========================================
# 1. 健康检查响应
# ==========================================

class HealthResponse(BaseModel):

    status: Literal["ok"]

    service: str


# ==========================================
# 2. Readiness 响应
# ==========================================

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
# 3. Run 摘要
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


# ==========================================
# 4. Run 列表
# ==========================================

class RunsResponse(BaseModel):

    count: int = Field(
        ge=0
    )

    runs: list[RunSummary]


# ==========================================
# 5. Run Detail
# ==========================================

class RunDetailResponse(BaseModel):

    summary: RunSummary

    events: list[
        dict[str, Any]
    ]


# ==========================================
# 6. Run Search Request
# ==========================================

class RunSearchRequest(BaseModel):

    model_config = ConfigDict(
        extra="forbid"
    )

    limit: int = Field(
        default=20,
        ge=1,
        le=100
    )

    min_event_count: int = Field(
        default=0,
        ge=0
    )

    run_id_contains: str | None = Field(
        default=None,
        min_length=1,
        max_length=80
    )


    @field_validator(
        "run_id_contains"
    )
    @classmethod
    def normalize_run_id_contains(
        cls,
        value: str | None
    ) -> str | None:

        if value is None:

            return None


        value = value.strip()


        if not value:

            raise ValueError(
                "run_id_contains 不能只包含空格"
            )


        return value