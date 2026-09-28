from fastapi import (
    FastAPI
)

from app.routers.users import (
    router as users_router
)


app = FastAPI(
    title="User API"
)


app.include_router(
    users_router
)


@app.get(
    "/health"
)
def health():

    return {
        "status":
            "ok"
    }