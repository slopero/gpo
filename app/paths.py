"""Centralised filesystem paths for dev runs and the PyInstaller one-file build.

Two kinds of locations are distinguished:

* **Resources** – read-only files shipped with the app (``db/sales.db``,
  ``kiril/reports``...). In a frozen build they live in the temporary
  ``sys._MEIPASS`` extraction folder, in dev – in the project root.
* **User data** – writable files that must survive restarts and exe updates
  (``app.db``, caches). In a frozen build they go to ``%LOCALAPPDATA%\\GPO``
  so nothing is created next to the executable; in dev – inside the project.
"""

import os
import sys
from pathlib import Path

APP_NAME = "GPO"

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


def is_frozen() -> bool:
    """Return True when running from a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def resource_dir() -> Path:
    """Root folder with bundled read-only resources."""
    bundle_dir: object = getattr(sys, "_MEIPASS", None)
    if is_frozen() and bundle_dir is not None:
        return Path(str(bundle_dir))
    return PROJECT_ROOT


def resource_path(*parts: str) -> Path:
    """Absolute path to a bundled resource, e.g. ``resource_path("db", "sales.db")``."""
    return resource_dir().joinpath(*parts)


def exe_dir() -> Path:
    """Folder containing the executable (frozen) or the project root (dev)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return PROJECT_ROOT


def user_data_dir() -> Path:
    """Writable per-user folder for the app database and caches (created on demand)."""
    if is_frozen():
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        data_dir = (Path(base) if base else Path.home() / "AppData" / "Local") / APP_NAME
    else:
        data_dir = PROJECT_ROOT / "db"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def app_db_path() -> Path:
    """Location of the main application SQLite database (saved form records)."""
    return user_data_dir() / "app.db"


def sales_db_path() -> Path:
    """Bundled small sales database with sample analogs."""
    return resource_path("db", "sales.db")


def cars_db_candidates() -> list[Path]:
    """Places where the large (~3 GB, not bundled) ``cars.db`` is looked up, in priority order."""
    candidates = [
        user_data_dir() / "cars.db",
        exe_dir() / "cars.db",
        exe_dir() / "db" / "cars.db",
        PROJECT_ROOT / "db" / "cars.db",
    ]
    unique: list[Path] = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    return unique


def cars_db_path() -> Path:
    """First existing ``cars.db`` location, or the preferred one if none exists yet."""
    candidates = cars_db_candidates()
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
