"""Provisioning of large data files shipped inside the one-file build.

``cars.db`` (~3 GB) is bundled as ``cars.zip`` (~440 MB) and extracted once into the
user data folder (``%LOCALAPPDATA%\\GPO``) on first launch. Subsequent launches reuse it.
"""

import shutil
import zipfile
from collections.abc import Callable
from pathlib import Path

from app.paths import cars_db_candidates, resource_path, user_data_dir

CARS_DB_NAME = "cars.db"
CHUNK_SIZE = 8 * 1024 * 1024

ProgressCallback = Callable[[int, int], None]


def bundled_cars_zip() -> Path:
    """Path of the bundled compressed cars database."""
    return resource_path("cars.zip")


def _zip_member(archive: zipfile.ZipFile) -> zipfile.ZipInfo | None:
    for info in archive.infolist():
        if Path(info.filename).name == CARS_DB_NAME:
            return info
    return None


def cars_db_extraction_needed() -> bool:
    """True if no usable cars.db exists yet but a bundled archive is available to extract."""
    zip_path = bundled_cars_zip()
    if not zip_path.exists():
        return False

    with zipfile.ZipFile(zip_path) as archive:
        member = _zip_member(archive)
        if member is None:
            return False
        expected_size = member.file_size

    target = user_data_dir() / CARS_DB_NAME
    if target.exists():
        # Re-extract if a previous extraction was interrupted or the bundled DB changed.
        return target.stat().st_size != expected_size

    # A manually placed cars.db (e.g. next to the exe) is good enough.
    return not any(path.exists() for path in cars_db_candidates() if path != target)


def extract_cars_db(progress: ProgressCallback | None = None) -> Path:
    """Extract bundled cars.db into the user data folder atomically and return its path."""
    zip_path = bundled_cars_zip()
    target = user_data_dir() / CARS_DB_NAME
    partial = target.with_suffix(".db.part")

    with zipfile.ZipFile(zip_path) as archive:
        member = _zip_member(archive)
        if member is None:
            raise FileNotFoundError(f"{CARS_DB_NAME} не найден внутри {zip_path.name}")

        total = member.file_size
        free = shutil.disk_usage(target.parent).free
        if free < total:
            raise OSError(
                f"Недостаточно места на диске для базы аналогов: нужно "
                f"{total / 1024**3:.1f} ГБ, свободно {free / 1024**3:.1f} ГБ "
                f"({target.parent})"
            )

        done = 0
        with archive.open(member) as src, partial.open("wb") as dst:
            while chunk := src.read(CHUNK_SIZE):
                dst.write(chunk)
                done += len(chunk)
                if progress is not None:
                    progress(done, total)

    partial.replace(target)
    return target
