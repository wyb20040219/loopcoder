from fastapi import (
    APIRouter,
    HTTPException
)

from app.schemas.user import (
    UserCreate,
    UserOut
)

from app.services.user_service import (
    create_user
)


router = APIRouter(
    prefix="/users",
    tags=[
        "users"
    ]
)


@router.post(
    "",
    response_model=UserOut,
    status_code=201
)
def create_user_endpoint(
    payload: UserCreate
):

    try:

        return create_user(
            name=
                payload.name,

            email=
                str(
                    payload.email
                )
        )


    except ValueError as e:

        raise HTTPException(

            status_code=
                409,

            detail=
                str(e)
        )