from sqlalchemy import (
    select,
)

from sqlalchemy.exc import (
    IntegrityError,
    SQLAlchemyError,
)

from sqlalchemy.orm import (
    Session,
)

from api.errors import (
    RunRecordConflictError,
    RunRecordNotFoundError,
)

from db.models import (
    RunRecord,
)


# ==========================================
# Create
# ==========================================

def create_run_record(
    db: Session,
    *,
    run_id: str,
    event_count: int,
) -> RunRecord:

    # --------------------------------------
    # 先检查 run_id 是否已经存在
    # --------------------------------------

    existing = db.scalar(
        select(
            RunRecord
        ).where(
            RunRecord.run_id
            ==
            run_id
        )
    )


    if existing is not None:

        raise RunRecordConflictError()


    # --------------------------------------
    # 创建Python ORM对象
    # 此时还没有真正INSERT
    # --------------------------------------

    record = RunRecord(
        run_id=run_id,
        event_count=event_count,
    )


    # --------------------------------------
    # 加入Session
    # --------------------------------------

    db.add(
        record
    )


    try:

        # ----------------------------------
        # 真正提交事务
        # INSERT最终写入MySQL
        # ----------------------------------

        db.commit()


    except IntegrityError as exc:

        db.rollback()

        raise RunRecordConflictError() from exc


    except SQLAlchemyError:

        db.rollback()

        raise


    # --------------------------------------
    # 从数据库重新读取最新状态
    #
    # 比如：
    # id
    # created_at
    # --------------------------------------

    db.refresh(
        record
    )


    return record


# ==========================================
# Read List
# ==========================================

def list_run_records(
    db: Session,
    *,
    limit: int,
) -> list[RunRecord]:

    statement = (
        select(
            RunRecord
        )
        .order_by(
            RunRecord.id.desc()
        )
        .limit(
            limit
        )
    )


    records = (
        db.scalars(
            statement
        )
        .all()
    )


    return list(
        records
    )


# ==========================================
# Read One
# ==========================================

def get_run_record(
    db: Session,
    *,
    record_id: int,
) -> RunRecord:

    record = db.get(
        RunRecord,
        record_id,
    )


    if record is None:

        raise RunRecordNotFoundError()


    return record


# ==========================================
# Update
# ==========================================

def update_run_record(
    db: Session,
    *,
    record_id: int,
    event_count: int,
) -> RunRecord:

    record = get_run_record(
        db,
        record_id=record_id,
    )


    # --------------------------------------
    # 修改Python对象属性
    # SQLAlchemy会追踪这个变化
    # --------------------------------------

    record.event_count = (
        event_count
    )


    try:

        db.commit()


    except SQLAlchemyError:

        db.rollback()

        raise


    db.refresh(
        record
    )


    return record


# ==========================================
# Delete
# ==========================================

def delete_run_record(
    db: Session,
    *,
    record_id: int,
) -> None:

    record = get_run_record(
        db,
        record_id=record_id,
    )


    db.delete(
        record
    )


    try:

        db.commit()


    except SQLAlchemyError:

        db.rollback()

        raise