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

    def __init__(self, parent, records, on_select):
        self.on_select = on_select

        self.window = tk.Toplevel(parent)
        self.window.title("Выбор данных из базы")
        self.window.geometry("860x420")

        title = tk.Label(self.window, text="Выбери запись", font=("Segoe UI", 12, "bold"))
        title.pack(pady=(10, 8))

        table_frame = tk.Frame(self.window)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

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

        button_row = tk.Frame(self.window)
        button_row.pack(pady=(0, 12))

        tk.Button(button_row, text="Выбрать", width=18, command=self._select_current).pack(side="left", padx=8)
        tk.Button(button_row, text="Отмена", width=18, command=self.window.destroy).pack(side="left", padx=8)

    def _select_current(self, _event=None):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выбери запись из списка")
            return

        record_id = int(selected[0])
        self.window.destroy()
        self.on_select(record_id)
