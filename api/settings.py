from functools import lru_cache

from pydantic import Field

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class ApiSettings(BaseSettings):

    # ======================================
    # Pydantic Settings 配置
    # ======================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # ======================================
    # API 基础配置
    # ======================================

    app_name: str = (
        "LoopCoder Control Plane API"
    )

    app_version: str = (
        "0.1.0"
    )

    environment: str = (
        "development"
    )

    log_level: str = (
        "INFO"
    )

    # ======================================
    # CORS
    # ======================================

    cors_origins: str = Field(
        default=(
            "http://localhost:5173,"
            "http://127.0.0.1:5173"
        )
    )

    # ======================================
    # 将字符串转换成列表
    # ======================================

    @property
    def cors_origin_list(
        self
    ) -> list[str]:

        return [
            origin.strip()

            for origin
            in self.cors_origins.split(",")

            if origin.strip()
        ]


@lru_cache
def get_api_settings() -> ApiSettings:

    return ApiSettings()