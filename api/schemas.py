
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)


# ==========================================
# 1. 健康检查响应模型
# ==========================================

class HealthResponse(BaseModel):

    status: Literal["ok"]

    service: str


# ==========================================
# 2. 单条 Run 摘要
# ==========================================

class RunSummary(BaseModel):

    run_id: str

    file_name: str

    started_at: str | None

    ended_at: str | None

    event_count: int = Field(ge=0)

    event_counts: dict[str, int]


# ==========================================
# 3. Run 列表响应
# ==========================================

class RunsResponse(BaseModel):

    count: int = Field(ge=0)

    runs: list[RunSummary]


# ==========================================
# 4. 单条 Run 详情响应
# ==========================================

class RunDetailResponse(BaseModel):

    summary: RunSummary

    events: list[dict[str, Any]]


# ==========================================
# 5. Run 搜索请求模型
# ==========================================

class RunSearchRequest(BaseModel):

    # 不允许请求体出现未定义字段
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

    # 进一步处理字符串内容
    @field_validator("run_id_contains")
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
