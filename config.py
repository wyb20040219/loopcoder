import os

from dotenv import (
    load_dotenv
)


load_dotenv()


MOONSHOT_API_KEY = (
    os.getenv(
        "MOONSHOT_API_KEY",
        ""
    )
)


MOONSHOT_BASE_URL = (
    os.getenv(
        "MOONSHOT_BASE_URL",
        "https://api.moonshot.cn/v1"
    )
)


MODEL_NAME = (
    os.getenv(
        "MODEL_NAME",
        "kimi-k2.7-code"
    )
)


if not MOONSHOT_API_KEY:

    raise RuntimeError(
        "缺少 MOONSHOT_API_KEY，"
        "请在 .env 中配置。"
    )