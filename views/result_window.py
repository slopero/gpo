import tkinter as tk
from tkinter import messagebox, ttk
from kiril.report_generator import main as report_main


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
        self.window.title("Карточка транспортного средства")
        self.window.geometry("760x540")
        self.window.protocol("WM_DELETE_WINDOW", self._go_back)

        self._center_window()

        top_bar = ttk.Frame(self.window, padding=(14, 12, 14, 6))
        top_bar.pack(fill="x")

        ttk.Button(top_bar, text="← Назад", command=self._go_back, width=12).pack(side="left")
        tk.Label(top_bar, text="Введенные данные ТС", font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=14
        )

        body_frame = ttk.Frame(self.window, padding=(14, 4, 14, 10))
        body_frame.pack(fill="both", expand=True)

        text = tk.Text(body_frame, wrap="word", height=20, font=("Segoe UI", 10), padx=8, pady=8)
        text.pack(fill="both", expand=True)

        lines = []
        for key, value in self.data.items():
            if value is not None and value != "":
                label = self.labels.get(key, key)
                lines.append(f"{label}: {value}")

        text.insert("1.0", "\n".join(lines) if lines else "Нет заполненных данных")
        text.config(state="disabled")

        button_row = ttk.Frame(self.window, padding=(14, 0, 14, 14))
        button_row.pack(fill="x")

        ttk.Button(button_row, text="← Назад", width=12, command=self._go_back).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(
            button_row,
            text="📊 Анализ рынка",
            width=18,
            command=self._handle_action_one,
        ).pack(side="left", padx=6)
        ttk.Button(
            button_row,
            text="🔍 Поиск аналогов",
            width=18,
            command=self._handle_action_two,
        ).pack(side="left", padx=6)
        tk.Button(
            button_row,
            text="⚖️ Судебная оценка (СК РФ)",
            width=24,
            command=self._handle_valuation,
            bg="#0066cc",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            pady=4,
        ).pack(side="right")

    def _center_window(self):
        """Центрирует окно на экране"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def _restore_self(self):
        if self.window.winfo_exists():
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()

    def _handle_action_one(self):
        self.window.withdraw()
        try:
            report_main()
        finally:
            self._restore_self()

    def _handle_valuation(self):
        from views.valuation_window import ValuationWindow

        self.window.withdraw()
        ValuationWindow(
            self.window,
            controller=self.controller,
            initial_data=self.data,
            on_back=self._restore_self,
        )
    
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
            progress_var.set(message)
            progress_bar['value'] = value
            progress_window.update()
        
        def search_thread():
            try:
                analogs = self.controller.find_similar_vehicles(
                    self.id, 
                    progress_callback=update_progress
                )
                
                progress_window.destroy()
                
                if not analogs:
                    messagebox.showinfo("Поиск аналогов", "Аналоги не найдены")
                    return
                
                from views.analogs_window import AnalogsWindow

                self.window.withdraw()
                AnalogsWindow(
                    self.window,
                    analogs,
                    target_data=self.data,
                    on_back=self._restore_self,
                )
                
            except Exception as e:
                progress_window.destroy()
                messagebox.showerror("Ошибка", f"Ошибка при поиске аналогов:\n{str(e)}")
        
        import threading
        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()

    def _go_back(self):
        self.window.destroy()
        self.on_back()
