import subprocess
import sys
from pathlib import Path

# Auto-redirect to project virtual environment if executed via external Python
# (not applicable to the PyInstaller build, where sys.frozen is set).
_venv_python = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
if (
    not getattr(sys, "frozen", False)
    and _venv_python.exists()
    and Path(sys.executable).resolve() != _venv_python.resolve()
):
    try:
        import sqlalchemy  # noqa: F401
    except ImportError:
        sys.exit(subprocess.run([str(_venv_python), *sys.argv], check=False).returncode)

from controllers.form_controller import FormController
from db.create_db import create_db
from db.params_model import ParamsModel
from views.data_setup_window import ensure_cars_db
from views.main_window import MainWindow


def main() -> None:
    ensure_cars_db()
    create_db()
    params_model = ParamsModel()
    form_controller = FormController(params_model)
    app = MainWindow(form_controller)
    app.run()


if __name__ == "__main__":
    main()
