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
        self.window.geometry("900x550")
        
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
        tk.Button(btn_frame, text="Закрыть", command=self.window.destroy, width=15).pack()
    
    def _create_table(self, parent):
        if not self.analogs:
            label = tk.Label(parent, text="Аналоги не найдены", font=("Segoe UI", 12))
            label.pack(expand=True)
            return
        
        columns = ["Название_машины", "Год", "Цена", "Мощность", 
                   "Объем_двигателя", "Тип_двигателя", "Коробка_передач", 
                   "Пробег", "Руль", "Регион"]
        
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
        }
        
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=15)
        tree.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        
        for col in columns:
            display_name = headers.get(col, col)
            tree.heading(col, text=display_name)
            
            if col == "Название_машины":
                width = 180
            elif col == "Цена":
                width = 120
            else:
                width = 100
            
            tree.column(col, width=width, anchor="w" if col != "Цена" else "e")
        
        for analog in self.analogs:
            values = []
            for col in columns:
                value = analog.get(col, "")
                
                if col == "Цена" and value:
                    try:
                        value = f"{int(value):,}".replace(",", " ")
                    except:
                        pass
                
                elif col == "Пробег" and value:
                    try:
                        value = f"{int(value):,}".replace(",", " ")
                    except:
                        pass
                
                values.append(value)
            
            tree.insert("", "end", values=values)