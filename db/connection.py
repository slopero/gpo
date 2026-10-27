from pathlib import Path
import shutil

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.paths import app_db_path, exe_dir, is_frozen


def _get_db_path() -> Path:
    db_path = app_db_path()

    if is_frozen() and not db_path.exists():
        # Older builds stored app.db next to GPO.exe – migrate it once so records aren't lost.
        legacy_db = exe_dir() / "app.db"
        if legacy_db.exists():
            try:
                shutil.copy2(legacy_db, db_path)
            except OSError:
                pass

    return db_path


DB_PATH = _get_db_path()
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass

