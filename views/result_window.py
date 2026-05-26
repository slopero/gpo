import logging
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from kiril.report_generator import main as report_main

logger = logging.getLogger(__name__)


class ResultWindow:
    def __init__(
        self,
        parent,
        data,
        labels,
        on_back,
        on_action_one=None,
        on_action_two=None,
        record_id=None,
        controller=None,
    ):
        self.controller = controller
        self.parent = parent
        self.data = data
        self.id = record_id
        self.labels = labels
        self.on_back = on_back

        self.window = tk.Toplevel(parent)
        self.window.title("Поиск аналогов и анализ рынка")
        self.window.geometry("620x520")
        self.window.protocol("WM_DELETE_WINDOW", self._go_back)

        self._center_window()

        title = tk.Label(self.window, text="Введенные данные", font=("Segoe UI", 14, "bold"))
        title.pack(pady=(12, 10))

        body_frame = tk.Frame(self.window)
        body_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        text = tk.Text(body_frame, wrap="word", height=20)
        text.pack(fill="both", expand=True)

        lines = []
        for key, value in self.data.items():
            if value is not None and value != "":
                label = self.labels.get(key, key)
                lines.append(f"{label}: {value}")

        text.insert("1.0", "\n".join(lines) if lines else "Нет заполненных данных")
        text.config(state="disabled")

        button_row = tk.Frame(self.window)
        button_row.pack(pady=(0, 14))

        tk.Button(button_row, text="Провести анализ рынка", width=20, command=self._handle_action_one).pack(side="left", padx=6)
        tk.Button(button_row, text="Поиск аналогов", width=20, command=self._handle_action_two).pack(side="left", padx=6)
        tk.Button(button_row, text="Назад к форме", width=20, command=self._go_back).pack(side="left", padx=6)

    def _center_window(self):
        """Центрирует окно на экране"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _handle_action_one(self):
        report_main()
    
    def _handle_action_two(self):
        """Поиск аналогов с выбором БД и прогресс-баром"""
        if not self.controller:
            messagebox.showwarning("Ошибка", "Нет доступа к базе данных")
            return
        
        if not self.id:
            messagebox.showwarning("Ошибка", "ID записи не найден")
            return
        
        progress_window = tk.Toplevel(self.window)
        progress_window.title("Поиск аналогов")
        progress_window.geometry("400x150")
        progress_window.transient(self.window)
        progress_window.grab_set()
        
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (progress_window.winfo_screenheight() // 2) - (150 // 2)
        progress_window.geometry(f'400x150+{x}+{y}')
        
        tk.Label(progress_window, text="Поиск аналогов...", font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        progress_var = tk.StringVar(value="Подготовка...")
        tk.Label(progress_window, textvariable=progress_var).pack(pady=5)
        
        progress_bar = ttk.Progressbar(progress_window, mode='determinate', length=350)
        progress_bar.pack(pady=10)
        
        def update_progress(message, value):
            self.window.after(0, lambda m=message, v=value: _apply_progress(m, v))

        def _apply_progress(message, value):
            progress_var.set(message)
            progress_bar['value'] = value

        def _on_search_complete(analogs):
            progress_window.destroy()
            if not analogs:
                messagebox.showinfo("Поиск аналогов", "Аналоги не найдены")
                return
            from views.analogs_window import AnalogsWindow
            AnalogsWindow(self.window, analogs)

        def _on_search_error(error_msg):
            progress_window.destroy()
            messagebox.showerror("Ошибка", f"Ошибка при поиске аналогов:\n{error_msg}")

        def search_thread():
            try:
                analogs = self.controller.find_similar_vehicles(
                    self.id,
                    progress_callback=update_progress
                )
                self.window.after(0, lambda: _on_search_complete(analogs))
            except Exception as e:
                logger.exception("Error searching for analogs")
                self.window.after(0, lambda: _on_search_error(str(e)))

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _go_back(self):
        self.window.destroy()
        self.on_back()
