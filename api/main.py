import logging

from fastapi import (
    FastAPI,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from api.handlers import (
    register_exception_handlers,
)

from api.lifespan import (
    lifespan,
)

from api.middleware import (
    register_http_middleware,
)

from api.routers import (
    control,
    dashboard,
    db_runs,
    runs,
    system,
)

from api.settings import (
    get_api_settings,
)


settings = get_api_settings()


logging.basicConfig(
    level=getattr(
        logging,
        settings.log_level.upper(),
        logging.INFO,
    ),
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.cors_origin_list
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Middleware
# ==========================================

register_http_middleware(
    app
)


# ==========================================
# Exception Handlers
# ==========================================

register_exception_handlers(
    app
)


# ==========================================
# Routers
# ==========================================

app.include_router(
    system.router
)

app.include_router(
    control.router
)

app.include_router(
    runs.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    db_runs.router
)