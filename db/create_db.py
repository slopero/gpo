from sqlalchemy import inspect, text

from db import params_model
from db.connection import Base, engine
from db.country_lookup import ensure_country_db


def create_db() -> None:
    Base.metadata.create_all(bind=engine)
    _add_vin_column_if_missing()
    ensure_country_db()


def _add_vin_column_if_missing() -> None:
    """Добавляет колонку vin в старые app.db без ALTER-скриптов"""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("params")}
    if "vin" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE params ADD COLUMN vin VARCHAR(32)"))
