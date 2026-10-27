import threading
import tkinter as tk
from tkinter import messagebox, ttk

from app.bundled_data import cars_db_extraction_needed, extract_cars_db


def ensure_cars_db() -> None:
    """On first launch of the exe, unpack the bundled cars.db showing a progress window."""
    try:
        if not cars_db_extraction_needed():
            return
    except Exception:
        return

    root = tk.Tk()
    root.title("GPO — первый запуск")
    root.resizable(False, False)
    width, height = 460, 150
    x = (root.winfo_screenwidth() - width) // 2
    y = (root.winfo_screenheight() - height) // 2
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    tk.Label(
        root, text="Подготовка базы аналогов (cars.db)", font=("Segoe UI", 11, "bold")
    ).pack(pady=(14, 4))
    status = tk.StringVar(value="Распаковка выполняется один раз, подождите...")
    tk.Label(root, textvariable=status).pack()
    bar = ttk.Progressbar(root, mode="determinate", length=400, maximum=100)
    bar.pack(pady=12)

    state: dict[str, object] = {"done": 0, "total": 1, "error": None, "finished": False}

    def on_progress(done: int, total: int) -> None:
        state["done"] = done
        state["total"] = total

    def worker() -> None:
        try:
            extract_cars_db(on_progress)
        except Exception as exc:
            state["error"] = exc
        state["finished"] = True

    def poll() -> None:
        done = int(state["done"])  # type: ignore[arg-type]
        total = max(int(state["total"]), 1)  # type: ignore[arg-type]
        bar["value"] = done * 100 / total
        status.set(f"Распаковано {done / 1024**3:.2f} из {total / 1024**3:.2f} ГБ")
        if state["finished"]:
            if state["error"] is not None:
                messagebox.showerror(
                    "База аналогов",
                    "Не удалось распаковать cars.db:\n"
                    f"{state['error']}\n\n"
                    "Автоподбор будет работать только по sales.db. "
                    "Можно выбрать базу вручную кнопкой «Сменить БД...».",
                )
            root.destroy()
            return
        root.after(200, poll)

    threading.Thread(target=worker, daemon=True).start()
    root.after(200, poll)
    root.mainloop()
