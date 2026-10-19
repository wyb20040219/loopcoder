from collections.abc import (
    Generator,
)

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from api.settings import (
    get_api_settings,
)


settings = get_api_settings()


# ==========================================
# Engine
# ==========================================

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=settings.sql_echo,
)


# ==========================================
# Session Factory
# ==========================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# ==========================================
# FastAPI Dependency
# ==========================================

def get_db() -> Generator[
    Session,
    None,
    None,
]:

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()