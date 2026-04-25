import tkinter as tk
from tkinter import messagebox, ttk

from views.db_records_window import DbRecordsWindow
from views.result_window import ResultWindow


class MainWindow:
    # Конфиг полей
    FIELD_CONFIG = [
        ("Марка", "mark", None),
        ("Модель", "model", None),
        ("Тип ТС", "type_ts", ["Автомобили", "Спецтехника"]),
        ("Год выпуска ТС", "year_ts", None),
        ("Регион сделки", "region", None),
        ("Дата сделки", "date_deal", None),
        ("Мощность двигателя", "power", None),
        ("Объем двигателя", "volume", None),
        ("Кол-во владельцев ТС", "count_owners", None),
        ("Тип двигателя", "type_engine", ["Бензин", "Дизель", "Гибрид", "Электро"]),
        ("Расположение руля", "type_wheels", ["Левый", "Правый"]),
        ("Пробег ТС по одометру", "count_kilometers", None),
        ("Тип КПП", "type_kpp", ["Механическая", "Автоматическая", "Роботизированная"]),
        ("Тип кузова", "type_body", None),
        ("Повреждения", "damage", ["Да", "Нет"]),
        ("Особенности комплектации, опции", "quality", None),
    ]

    def __init__(self, controller):
        self.controller = controller
        self.root = tk.Tk()
        self.root.title("Форма для заполнения данных")
        self.root.geometry("560x640")

        self.field_vars = {}
        self.field_labels = {}
        self._build_form()

    # Построение формы на основе FIELD_CONFIG
    def _build_form(self):
        # Получаем данные из FIELD_CONFIG и создаем поля
        for row, (label_text, key, options) in enumerate(self.FIELD_CONFIG):
            self._create_field(row, label_text, key, options)

        button_row = tk.Frame(self.root)
        button_row.grid(row=len(self.FIELD_CONFIG), column=0, columnspan=2, pady=16)

        tk.Button(button_row, text="Сохранить", command=self.submit_form, width=24).pack(side="left", padx=8)
        tk.Button(button_row, text="Выбрать из БД", command=self.open_db_records, width=24).pack(
            side="left", padx=8
        )

    """Создание поля с меткой и виджетом ввода (Entry или Combobox)"""
    def _create_field(self, row, label_text, key, options=None):
        var = tk.StringVar()
        tk.Label(self.root, text=f"{label_text}:").grid(row=row, column=0, padx=10, pady=6, sticky="w")

        # Если есть варианты для выбора
        if options:
            widget = ttk.Combobox(self.root, textvariable=var, values=options, state="readonly", width=37)
            widget.grid(row=row, column=1, padx=10, pady=6)
        # Иначе обычное поле ввода
        else:
            widget = tk.Entry(self.root, textvariable=var, width=40)
            widget.grid(row=row, column=1, padx=10, pady=6)

        self.field_vars[key] = var
        self.field_labels[key] = label_text
    
    """Сохранение данных при нажатии кнопки и отображение результата"""
    def submit_form(self):
        data = {key: var.get().strip() for key, var in self.field_vars.items()}

        success, message = self.controller.save_params(data)
        if not success:
            messagebox.showwarning("Ошибка", message)
            return

        selected_id = self.controller.get_selected_record_id()
        self.root.withdraw()
        ResultWindow(
            self.root, 
            data, 
            self.field_labels, 
            self._restore_form, 
            record_id=selected_id,
            controller=self.controller
        )

    def open_db_records(self):
        records = self.controller.get_saved_records()
        if not records:
            messagebox.showinfo("База данных", "В базе пока нет сохраненных записей")
            return

        DbRecordsWindow(self.root, records, self._open_selected_record)

    def _open_selected_record(self, record_id):
        self.controller.select_record(record_id)
        data = self.controller.get_record_data(record_id)
        if data is None:
            messagebox.showwarning("База данных", "Запись не найдена")
            return

        selected_id = self.controller.get_selected_record_id()
        data_without_id = {key: value for key, value in data.items() if key != "id"}

        self.root.withdraw()
        ResultWindow(
            self.root,
            data_without_id,
            self.field_labels,
            self._restore_form,
            record_id=selected_id,
            controller=self.controller
        )

    def _restore_form(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def run(self):
        self.root.mainloop()
