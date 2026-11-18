import tkinter as tk
from tkinter import messagebox, ttk


class DbRecordsWindow:
    COLUMNS = ("mark", "model", "year_ts", "region", "date_deal")
    HEADERS = {
        "mark": "Марка",
        "model": "Модель",
        "year_ts": "Год выпуска",
        "region": "Регион сделки",
        "date_deal": "Дата сделки",
    }

    def __init__(self, parent, records, on_select, on_back=None):
        self.on_select = on_select
        self.on_back = on_back

        self.window = tk.Toplevel(parent)
        self.window.title("Выбор ТС из базы данных")
        self.window.geometry("880x460")
        self.window.protocol("WM_DELETE_WINDOW", self._go_back)

        top_bar = ttk.Frame(self.window, padding=(12, 10, 12, 4))
        top_bar.pack(fill="x")

        ttk.Button(top_bar, text="← Назад", command=self._go_back, width=12).pack(side="left")
        tk.Label(
            top_bar,
            text="Сохранённые транспортные средства",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=14)

        table_frame = ttk.Frame(self.window, padding=(12, 4, 12, 8))
        table_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=self.COLUMNS, show="headings", height=14)
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        for column in self.COLUMNS:
            self.tree.heading(column, text=self.HEADERS[column])
            self.tree.column(column, anchor="w", width=160)

        for record in records:
            record_id = record["id"]
            values = (
                record.get("mark") or "",
                record.get("model") or "",
                record.get("year_ts") or "",
                record.get("region") or "",
                record.get("date_deal") or "",
            )
            self.tree.insert("", "end", iid=str(record_id), values=values)

        self.tree.bind("<Double-1>", self._select_current)

        button_row = ttk.Frame(self.window, padding=(12, 0, 12, 12))
        button_row.pack(fill="x")

        tk.Button(
            button_row,
            text="Выбрать запись",
            width=20,
            command=self._select_current,
            bg="#0066cc",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            pady=4,
        ).pack(side="right")
        ttk.Button(button_row, text="← Назад", width=14, command=self._go_back).pack(
            side="left"
        )

        self._center_window()

    def _center_window(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = max(10, (self.window.winfo_screenwidth() // 2) - (w // 2))
        y = max(10, (self.window.winfo_screenheight() // 2) - (h // 2))
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def _go_back(self):
        self.window.destroy()
        if self.on_back is not None:
            self.on_back()

    def _select_current(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите запись из списка")
            return

        record_id = int(selected[0])
        self.window.destroy()
        self.on_select(record_id)
