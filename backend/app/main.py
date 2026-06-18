import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import init_db
from .middleware import RateLimitMiddleware
from .routes import analytics_routes, assistant_routes, auth_routes, dashboard_routes, detection_routes, evidence_routes, file_routes, motion_routes, report_routes, settings_routes, system_routes, zone_routes
from .services.yolo_service import get_yolo_model


settings = get_settings()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
file_handler = RotatingFileHandler(settings.logs_dir / "backend.log", maxBytes=2_000_000, backupCount=5)
file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.getLogger().addHandler(file_handler)
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()
    try:
        get_yolo_model()
    except Exception as exc:
        logging.getLogger(__name__).error("YOLO model failed during startup: %s", exc)


@app.get("/health")
def health():
    return {"status": "ok", "name": settings.app_name}


@app.get("/")
def root():
    return {"status": "ok", "name": settings.app_name, "api": settings.api_prefix, "health": "/health"}


for route in (
    auth_routes.router,
    dashboard_routes.router,
    motion_routes.router,
    detection_routes.router,
    zone_routes.router,
    analytics_routes.router,
    assistant_routes.router,
    evidence_routes.router,
    report_routes.router,
    settings_routes.router,
    system_routes.router,
    file_routes.router,
):
    app.include_router(route, prefix=settings.api_prefix)
