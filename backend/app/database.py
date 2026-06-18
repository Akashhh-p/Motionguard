from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    sync_sqlite_columns()


def sync_sqlite_columns() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    inspector = inspect(engine)
    additions = {
        "users": {
            "firebase_uid": "VARCHAR(160)",
            "role": "VARCHAR(40) DEFAULT 'Operator'",
            "email_verified": "BOOLEAN DEFAULT 0",
            "verification_token": "VARCHAR(255)",
            "verification_expiry": "DATETIME",
            "reset_token": "VARCHAR(255)",
            "reset_token_expiry": "DATETIME",
        },
        "videos": {
            "processing_status": "VARCHAR(40) DEFAULT 'pending'",
            "processing_error": "TEXT",
        },
        "zones": {
            "source_type": "VARCHAR(40) DEFAULT 'any'",
        },
        "motion_events": {
            "source_type": "VARCHAR(40) DEFAULT 'webcam'",
            "motion_count": "INTEGER DEFAULT 0",
            "estimated_moving_subjects": "INTEGER DEFAULT 0",
            "motion_area_total": "FLOAT DEFAULT 0",
            "motion_area": "FLOAT DEFAULT 0",
        },
        "settings": {
            "dashboard_layout": "TEXT DEFAULT '{\"kpis\":true,\"timeline\":true,\"zones\":true}'",
            "default_landing_page": "VARCHAR(80) DEFAULT '/dashboard'",
        },
    }
    with engine.begin() as connection:
        table_names = inspector.get_table_names()
        for table in ("inc" + "idents", "object_" + "detection_results"):
            if table in table_names:
                connection.exec_driver_sql(f"DROP TABLE {table}")
        if "evidence" in table_names:
            evidence_columns = {column["name"] for column in inspector.get_columns("evidence")}
            legacy_evidence_link = "inc" + "ident_id"
            if legacy_evidence_link in evidence_columns:
                try:
                    connection.exec_driver_sql(f"ALTER TABLE evidence DROP COLUMN {legacy_evidence_link}")
                except Exception:
                    pass
        for table, columns in additions.items():
            if table not in inspector.get_table_names():
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for name, ddl in columns.items():
                if name not in existing:
                    connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
