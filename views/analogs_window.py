import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict


class AnalogsWindow:
    """Окно для отображения найденных аналогов"""
    
    def __init__(self, parent, analogs: List[Dict]):
        self.parent = parent
        self.analogs = analogs
        
        self.window = tk.Toplevel(parent)
        self.window.title("Найденные аналоги")
        self.window.geometry("1000x600")
        self._center_window()
        
        title = tk.Label(
            self.window, 
            text=f"Найдено аналогов: {len(analogs)}", 
            font=("Segoe UI", 14, "bold")
        )
        title.pack(pady=(12, 10))
        
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        self._create_table(frame)
        
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=(0, 12))
        tk.Button(
            btn_frame,
            text="⚖️ Передать в судебную оценку",
            command=self._open_valuation,
            width=26,
            bg="#0066cc",
            fg="white",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Закрыть", command=self.window.destroy, width=15).pack(
            side="left", padx=8
        )

    def _open_valuation(self):
        from datetime import datetime
        from views.valuation_window import ValuationWindow
        val_win = ValuationWindow(self.window)
        analogs = []
        for an in self.analogs:
            try:
                price = float(str(an.get("Цена", 0)).replace(" ", "").replace(",", "."))
                mileage = float(str(an.get("Пробег", 0)).replace(" ", "").replace(",", "."))
                year = int(str(an.get("Год", 2023)).strip())
                age = max(1.0, float(datetime.now().year - year))
                analogs.append({
                    "name": str(an.get("Название_машины", "Аналог")),
                    "price": price,
                    "age_years": age,
                    "mileage_km": mileage,
                    "city": str(an.get("Регион", "")),
                })
            except Exception:
                continue
        if analogs:
            val_win.analogs_list = analogs
            val_win._refresh_analogs_table()
    
    def _center_window(self):
        """Центрирует окно на экране"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_table(self, parent):
        if not self.analogs:
            label = tk.Label(parent, text="Аналоги не найдены", font=("Segoe UI", 12))
            label.pack(expand=True)
            return
        
        all_keys = set()
        for analog in self.analogs:
            all_keys.update(analog.keys())
        
        priority_columns = ["Название_машины", "Год", "Цена", "Мощность", 
                           "Объем_двигателя", "Тип_двигателя", "Коробка_передач", 
                           "Пробег", "Руль", "Регион", "Дата_объявления"]
        
        columns = [col for col in priority_columns if col in all_keys]
        
        if not columns:
            columns = list(all_keys)
        
        headers = {
            "Название_машины": "Марка/Модель",
            "Год": "Год",
            "Цена": "Цена (₽)",
            "Мощность": "Мощность (л.с.)",
            "Объем_двигателя": "Объем (л)",
            "Тип_двигателя": "Двигатель",
            "Коробка_передач": "КПП",
            "Пробег": "Пробег (км)",
            "Руль": "Руль",
            "Регион": "Регион",
            "Дата_объявления": "Дата объявления",
        }
        
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True)
        
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        for col in columns:
            display_name = headers.get(col, col)
            tree.heading(col, text=display_name)
            
            if col == "Название_машины":
                width = 200
            elif col == "Цена":
                width = 120
            else:
                width = 100
            
            tree.column(col, width=width, anchor="w" if col not in ["Цена", "Год", "Мощность", "Пробег"] else "e")
        
        for analog in self.analogs:
            values = []
            for col in columns:
                value = analog.get(col, "")
                
                if col == "Цена" and value:
                    try:
                        value = f"{int(float(value)):,}".replace(",", " ")
                    except:
                        pass
                elif col == "Пробег" and value:
                    try:
                        value = f"{int(float(value)):,}".replace(",", " ")
                    except:
                        pass
                elif col == "Мощность" and value:
                    try:
                        value = f"{int(float(value))}".replace(",", " ")
                    except:
                        pass
                
                values.append(value)
            
            tree.insert("", "end", values=values)
