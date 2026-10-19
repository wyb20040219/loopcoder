
"""
LoopCoder Control Plane API.

保留原来的 Uvicorn 启动入口。
实际 FastAPI 应用位于 api/main.py。
"""

from api.main import app
