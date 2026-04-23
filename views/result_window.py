import tkinter as tk
from tkinter import messagebox
from kiril import report_generator

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
        self.id = record_id # ID записи в базе
        self.labels = labels
        self.on_back = on_back
        self.on_action_one = on_action_one
        self.on_action_two = on_action_two

        self.window = tk.Toplevel(parent)
        self.window.title("Поиск аналогов и анализ рынка")
        self.window.geometry("620x520")
        self.window.protocol("WM_DELETE_WINDOW", self._go_back)

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

    def _handle_action_one(self):
        report_generator.main()
    def _handle_action_two(self):
        """Поиск аналогов"""
        if not self.controller:
            messagebox.showwarning("Ошибка", "Нет доступа к базе данных")
            return
        
        if not self.id:
            messagebox.showwarning("Ошибка", "ID записи не найден")
            return
        
        try:
            self.window.config(cursor="watch")
            self.window.update()
            
            analogs = self.controller.find_similar_vehicles(self.id)
            
            self.window.config(cursor="")
            
            if not analogs:
                messagebox.showinfo("Поиск аналогов", "Аналоги не найдены")
                return
            
            from views.analogs_window import AnalogsWindow
            AnalogsWindow(self.window, analogs)
            
        except Exception as e:
            self.window.config(cursor="")
            messagebox.showerror("Ошибка", f"Ошибка при поиске аналогов:\n{str(e)}")

    def _go_back(self):
        self.window.destroy()
        self.on_back()
