from typing import (
    Annotated,
)

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    Response,
    status,
)

from sqlalchemy.orm import (
    Session,
)

from api.schemas import (
    DbRunCreateRequest,
    DbRunListResponse,
    DbRunResponse,
    DbRunUpdateRequest,
)

from db.repositories.run_records import (
    create_run_record,
    delete_run_record,
    get_run_record,
    list_run_records,
    update_run_record,
)

from db.session import (
    get_db,
)


router = APIRouter(
    prefix="/db/runs",
    tags=[
        "Database Runs"
    ],
)


# ==========================================
# Create
# ==========================================

@router.post(
    "",
    response_model=DbRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_db_run(
    payload: DbRunCreateRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    return create_run_record(
        db,
        run_id=payload.run_id,
        event_count=payload.event_count,
    )


# ==========================================
# List
# ==========================================

@router.get(
    "",
    response_model=DbRunListResponse,
)
def list_db_runs(
    db: Annotated[
        Session,
        Depends(get_db),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 20,
):

    records = list_run_records(
        db,
        limit=limit,
    )


    return {
        "count":
            len(records),

        "records":
            records,
    }


# ==========================================
# Get One
# ==========================================

@router.get(
    "/{record_id}",
    response_model=DbRunResponse,
)
def get_db_run(
    record_id: Annotated[
        int,
        Path(
            ge=1
        ),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    return get_run_record(
        db,
        record_id=record_id,
    )


# ==========================================
# Update
# ==========================================

@router.patch(
    "/{record_id}",
    response_model=DbRunResponse,
)
def update_db_run(
    record_id: Annotated[
        int,
        Path(
            ge=1
        ),
    ],
    payload: DbRunUpdateRequest,
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    return update_run_record(
        db,
        record_id=record_id,
        event_count=payload.event_count,
    )


# ==========================================
# Delete
# ==========================================

@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_db_run(
    record_id: Annotated[
        int,
        Path(
            ge=1
        ),
    ],
    db: Annotated[
        Session,
        Depends(get_db),
    ],
):

    delete_run_record(
        db,
        record_id=record_id,
    )


    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )