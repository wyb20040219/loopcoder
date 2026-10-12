
from fastapi import APIRouter

from api.schemas import HealthResponse


router = APIRouter(
    tags=["System"]
)


@router.get(
    "/health",
    response_model=HealthResponse
)
def health():

    return {
        "status": "ok",
        "service": "loopcoder-control-plane"
    }
