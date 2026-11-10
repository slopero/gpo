"""Window for judicial vehicle valuation via comparative sales approach (SEC SK RF / Minyust RF)."""

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from app.services.valuation.constants import (
    BARGAINING_DISCOUNTS,
    WEAR_COEFFICIENTS,
    BargainingCategory,
    VehicleWearCategory,
    check_vehicle_localization,
    detect_vehicle_category,
)
from app.services.valuation.schemas import (
    AnalogVehicleInput,
    TargetVehicleInput,
    ValuationReport,
    ValuationRequest,
)
from app.services.valuation.selector import AnalogSelector
from app.services.valuation.service import ValuationService
from views.db_records_window import DbRecordsWindow


def _fmt_dec(value: float, digits: int = 4) -> str:
    """Format decimal number with Russian decimal comma."""
    return f"{value:.{digits}f}".replace(".", ",")


def _fmt_money(value: float) -> str:
    """Format rouble amount with thin-space thousands separator."""
    return f"{round(value):,}".replace(",", " ")


def _country_formula(report: ValuationReport) -> str:
    """Коротко, откуда взята страна."""
    source = report.target_country_source or ""
    if source == "vin":
        return f"по VIN {(report.target_vehicle.vin or '—')[:3]}"
    if source == "brand":
        return "по марке"
    return "не определена"


def _country_value(report: ValuationReport) -> str:
    return report.target_country or "—"


def _build_target_coefficient_rows(report: ValuationReport) -> list[tuple[str, str, str, str]]:
    """Build per-coefficient breakdown rows for the target vehicle only.

    Each row: (symbol, description, formula with substituted values, value).
    """
    t = report.target_vehicle
    a = report.target_wear_coeff_a
    b = report.target_wear_coeff_b
    t_f = t.age_years
    l_f = t.mileage_km / 1000.0
    omega = report.target_omega
    e = report.e_base
    wear = report.target_wear_pct
    moral = report.moral_wear_pct
    moral_k = 1.0 - moral / 100.0
    c_sr = report.weighted_mean_price
    repair = report.repair_cost

    if report.bargaining_discounts:
        disc_str = " / ".join(f"{d * 100:.1f}%".replace(".", ",") for d in report.bargaining_discounts)
        k_torg_str = " / ".join(_fmt_dec(1.0 - d, 3) for d in report.bargaining_discounts)
    else:
        disc_str = "—"
        k_torg_str = "—"

    return [
        ("Кат.", "Категория ТС (Методика Минюста)", t.vehicle_category, ""),
        (
            "Страна",
            "Страна-производитель",
            _country_formula(report),
            _country_value(report),
        ),
        ("Tф", "Фактический возраст, лет", "по документам", _fmt_dec(t_f, 2)),
        ("Lф", "Фактический пробег, тыс. км", f"{_fmt_money(t.mileage_km)} км / 1000", _fmt_dec(l_f, 3)),
        ("a", "Коэффициент влияния возраста", "норматив категории", _fmt_dec(a, 4)),
        ("b", "Коэффициент влияния пробега", "норматив категории", _fmt_dec(b, 4)),
        (
            "Ω",
            "Интенсивность эксплуатации",
            f"a·Tф + b·Lф = {_fmt_dec(a, 4)}·{_fmt_dec(t_f, 2)} + {_fmt_dec(b, 4)}·{_fmt_dec(l_f, 3)}",
            _fmt_dec(omega, 5),
        ),
        ("e", "Основание натурального логарифма", "по Методике", _fmt_dec(e, 2)),
        (
            "Иф",
            "Физический износ, %",
            f"100·(1 − e^−Ω) = 100·(1 − {_fmt_dec(e, 2)}^−{_fmt_dec(omega, 5)})",
            _fmt_dec(wear, 2),
        ),
        ("Сторг", "Скидка на торг, %", "Живаев М.В., 2024", disc_str),
        ("Кторг", "Коэффициент торга", "1 − Сторг", k_torg_str),
        (
            "Сср",
            "Средневзвешенная стоимость, руб.",
            "Σ (Cск_i · Кв_i) по аналогам",
            _fmt_money(c_sr),
        ),
        ("Им", "Моральный износ, %", "Им1 + Им2 + Им3 + Им4", _fmt_dec(moral, 2)),
        ("Км", "Коэффициент морального износа", "1 − Им / 100", _fmt_dec(moral_k, 4)),
        ("Сэд", "Устранение дефектов, руб.", "Ср + Сзч + См", _fmt_money(repair)),
        (
            "Ств",
            "РЫНОЧНАЯ СТОИМОСТЬ, руб.",
            f"Сср·Км − Сэд = {_fmt_money(c_sr)}·{_fmt_dec(moral_k, 4)} − {_fmt_money(repair)}",
            _fmt_money(report.market_value),
        ),
    ]


class AnalogEditDialog:
    """Dialog for adding or editing an analog vehicle."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        analog_data: dict[str, Any] | None = None,
        on_save: Any = None,
    ) -> None:
        self.on_save = on_save
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Параметры объекта-аналога")
        self.dialog.geometry("460x360")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        from views.clipboard_fix import install_paste_fix

        install_paste_fix(self.dialog)

        self.fields: dict[str, tk.StringVar] = {
            "name": tk.StringVar(value=str(analog_data.get("name", "")) if analog_data else ""),
            "price": tk.StringVar(
                value=str(analog_data.get("price", "")) if analog_data else "3000000"
            ),
            "age_years": tk.StringVar(
                value=str(analog_data.get("age_years", "")) if analog_data else "2"
            ),
            "mileage_km": tk.StringVar(
                value=str(analog_data.get("mileage_km", "")) if analog_data else "30000"
            ),
            "discount": tk.StringVar(
                value=str(analog_data.get("discount", "")) if analog_data else ""
            ),
            "deflator": tk.StringVar(
                value=str(analog_data.get("deflator", "")) if analog_data else "1.0"
            ),
            "city": tk.StringVar(value=str(analog_data.get("city", "")) if analog_data else ""),
        }

        self._build_ui()
        self._center_window()

    def _center_window(self) -> None:
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (h // 2)
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.dialog, padding=14)
        frame.pack(fill="both", expand=True)

        rows = [
            ("Наименование / Описание:", "name", "Аналог (например, Drom Казань)"),
            ("Цена предложения (руб.):", "price", "4350000"),
            ("Фактический возраст (лет):", "age_years", "2"),
            ("Пробег (км):", "mileage_km", "14000"),
            ("Скидка на торг (0.05 = 5%):", "discount", "Оставить пустым для авто-расчета"),
            ("Дефлятор цен К_прив:", "deflator", "1.0 (или расчетный)"),
            ("Город / Регион оферты:", "city", "Казань"),
        ]

        for idx, (label, key, hint) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, textvariable=self.fields[key], width=26)
            entry.grid(row=idx, column=1, sticky="ew", pady=4, padx=(8, 0))

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=len(rows), column=0, columnspan=2, pady=(16, 0))
        ttk.Button(btn_row, text="Сохранить", command=self._save, width=15).pack(
            side="left", padx=6
        )
        ttk.Button(btn_row, text="Отмена", command=self.dialog.destroy, width=15).pack(
            side="left", padx=6
        )

    def _save(self) -> None:
        try:
            price = float(self.fields["price"].get().replace(" ", "").replace(",", "."))
            age = float(self.fields["age_years"].get().replace(",", "."))
            mileage = float(self.fields["mileage_km"].get().replace(" ", "").replace(",", "."))

            discount_str = self.fields["discount"].get().strip().replace(",", ".")
            discount = float(discount_str) if discount_str else None

            deflator_str = self.fields["deflator"].get().strip().replace(",", ".")
            deflator = float(deflator_str) if deflator_str else 1.0

            result = {
                "name": self.fields["name"].get().strip() or "Аналог",
                "price": price,
                "age_years": age,
                "mileage_km": mileage,
                "discount": discount,
                "deflator": deflator,
                "city": self.fields["city"].get().strip(),
            }
            if self.on_save:
                self.on_save(result)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Проверьте числовые поля: Цена, Возраст, Пробег, Дефлятор."
            )


class ValuationWindow:
    """Dedicated interactive window for judicial vehicle valuation (comparative approach)."""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        controller: Any = None,
        initial_data: dict[str, Any] | None = None,
    ) -> None:
        self.parent = parent
        self.controller = controller
        self.service = ValuationService()

        self.window = tk.Toplevel(parent)
        self.window.title(
            "Судебная оценка стоимости ТС — Сравнительный подход (СЭЦ СК РФ / Минюст РФ)"
        )
        self.window.geometry("1180x820")
        self.window.minsize(1050, 700)

        self.analogs_list: list[dict[str, Any]] = []
        self.last_report: ValuationReport | None = None

        self._init_target_vars(initial_data)
        self._build_ui()
        from views.clipboard_fix import install_paste_fix

        install_paste_fix(self.window)
        self._center_window()

        # If initial data has values, pre-populate
        if initial_data:
            self._fill_from_dict(initial_data)

    def _center_window(self) -> None:
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = max(10, (self.window.winfo_screenwidth() // 2) - (w // 2))
        y = max(10, (self.window.winfo_screenheight() // 2) - (h // 2))
        self.window.geometry(f"{w}x{h}+{x}+{y}")

    def _init_target_vars(self, initial_data: dict[str, Any] | None) -> None:
        self.var_brand = tk.StringVar(value="GAC")
        self.var_model = tk.StringVar(value="M8")
        self.var_year = tk.StringVar(value="2023")
        self.var_age = tk.StringVar(value="1")
        self.var_mileage = tk.StringVar(value="92088")
        self.var_category = tk.StringVar(value="Легковые автомобили азиатские (кроме Японии)")
        self.var_vin = tk.StringVar(value="")
        self.var_plate = tk.StringVar(value="")
        self.var_date = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.var_bargaining = tk.StringVar(value="5%")
        self.var_moral_wear = tk.StringVar(value="0")
        self.var_repair_cost = tk.StringVar(value="0")

        # Database selection for market analogs: cars.db is default
        default_db = AnalogSelector.get_default_db()
        self.var_db_path = tk.StringVar(value=str(default_db))
        self.var_auto_fallback = tk.BooleanVar(value=True)
        status_name = (
            "cars.db (12.1 млн записей)" if default_db.name == "cars.db" else default_db.name
        )
        self.var_analogs_db_status = tk.StringVar(
            value=f"База аналогов: {status_name}"
        )

        # Result summary vars
        self.res_market_value = tk.StringVar(value="—")
        self.res_variation = tk.StringVar(value="—")
        self.res_target_wear = tk.StringVar(value="—")
        self.res_status = tk.StringVar(
            value="Нажмите 'Рассчитать' — аналоги будут подобраны из базы автоматически."
        )
        self.var_localization_hint = tk.StringVar(value="")

        self.var_brand.trace_add("write", self._on_brand_or_vin_change)
        self.var_vin.trace_add("write", self._on_brand_or_vin_change)

    def _on_brand_or_vin_change(self, *args: Any) -> None:
        brand = self.var_brand.get().strip()
        vin = self.var_vin.get().strip()
        if brand or vin:
            cat, is_localized, note = check_vehicle_localization(brand, vin=vin)
            if brand:
                self.var_category.set(cat)
            if is_localized:
                self.var_localization_hint.set(f"💡 {note}")
            else:
                self.var_localization_hint.set("")
        else:
            self.var_localization_hint.set("")

    def _build_ui(self) -> None:
        # Top toolbar
        toolbar = ttk.Frame(self.window, padding=(12, 10, 12, 6))
        toolbar.pack(fill="x")

        ttk.Button(
            toolbar,
            text="📂 Выбрать ТС из базы",
            command=self._open_db_selector,
            width=22,
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar,
            text="⭐ Эталон: GAC M8",
            command=self._load_benchmark_gac,
            width=20,
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar,
            text="⭐ Эталон: Sollers Atlant",
            command=self._load_benchmark_sollers,
            width=24,
        ).pack(side="left", padx=4)

        ttk.Button(
            toolbar,
            text="🔄 Очистить",
            command=self._clear_all,
            width=14,
        ).pack(side="left", padx=4)

        # PanedWindow: Left (Target + Actions) / Right (Analogs + Full 8-step Table)
        main_paned = ttk.PanedWindow(self.window, orient="vertical")
        main_paned.pack(fill="both", expand=True, padx=12, pady=6)

        # Upper frame: Target vehicle (Left) + Analogs list (Right)
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=3)

        top_paned = ttk.PanedWindow(top_frame, orient="horizontal")
        top_paned.pack(fill="both", expand=True)

        target_group = ttk.LabelFrame(
            top_paned,
            text=" 1. Объект исследования (оцениваемый автомобиль) ",
            padding=10,
        )
        top_paned.add(target_group, weight=2)
        self._build_target_form(target_group)

        analogs_group = ttk.LabelFrame(
            top_paned,
            text=" 2. Объекты-аналоги вторичного рынка (минимум 3) ",
            padding=10,
        )
        top_paned.add(analogs_group, weight=3)
        self._build_analogs_manager(analogs_group)

        # Lower frame: Calculation Results & 8-stage matrix
        bottom_group = ttk.LabelFrame(
            main_paned,
            text=" 3. Расчет стоимости объекта исследования (Методика Минюста РФ) ",
            padding=10,
        )
        main_paned.add(bottom_group, weight=4)
        self._build_results_view(bottom_group)

    def _build_target_form(self, parent: ttk.LabelFrame) -> None:
        grid = ttk.Frame(parent)
        grid.pack(fill="both", expand=True)

        categories = list(WEAR_COEFFICIENTS.keys())
        # Filter for cleaner Russian presentation
        ru_categories = [
            cat for cat in categories if not cat.isupper()
        ] or categories

        fields = [
            ("Марка:", self.var_brand, None),
            ("Модель:", self.var_model, None),
            ("Год выпуска:", self.var_year, None),
            ("Фактический возраст Tф (лет):", self.var_age, None),
            ("Фактический пробег Lф (км):", self.var_mileage, None),
            ("Категория интенсивности (Минюст):", self.var_category, ru_categories),
            ("Дата оценки (ГГГГ-ММ-ДД):", self.var_date, None),
            ("VIN номер:", self.var_vin, None),
            ("Гос. рег. знак:", self.var_plate, None),
            ("Моральный износ Им (%):", self.var_moral_wear, None),
            ("Ремонт дефектов Сэд (руб.):", self.var_repair_cost, None),
        ]

        for row, (lbl, var, opts) in enumerate(fields):
            ttk.Label(grid, text=lbl, font=("Segoe UI", 9)).grid(
                row=row, column=0, sticky="w", pady=2, padx=(0, 4)
            )
            if opts:
                combo = ttk.Combobox(grid, textvariable=var, values=opts, state="readonly", width=30)
                combo.grid(row=row, column=1, sticky="ew", pady=2)
            else:
                entry = ttk.Entry(grid, textvariable=var, width=32)
                entry.grid(row=row, column=1, sticky="ew", pady=2)

        # Localization hint label (ниже кнопки расчёта — кнопка не должна уезжать за экран;
        # показывается только при наличии текста; живёт в labelframe, а не в grid-фрейме)
        self._hint_label = ttk.Label(
            parent,
            textvariable=self.var_localization_hint,
            font=("Segoe UI", 8, "italic"),
            foreground="#b35900",
            wraplength=340,
        )

        grid.columnconfigure(1, weight=1)

        # Big primary calculate button
        calc_btn = tk.Button(
            parent,
            text="⚖️ РАССЧИТАТЬ СТОИМОСТЬ ПО МЕТОДИКЕ",
            command=self.calculate_valuation,
            font=("Segoe UI", 10, "bold"),
            bg="#0066cc",
            fg="white",
            relief="raised",
            cursor="hand2",
            pady=6,
        )
        calc_btn.pack(fill="x", pady=(8, 0))
        self._calc_btn = calc_btn
        self._hint_label.pack(fill="x", pady=(2, 0))

        # Пустая подсказка не должна съедать высоту панели
        self.var_localization_hint.trace_add("write", self._toggle_hint_visibility)
        self._toggle_hint_visibility()

    def _toggle_hint_visibility(self, *args: Any) -> None:
        if self.var_localization_hint.get():
            self._hint_label.pack(fill="x", pady=(2, 0), after=self._calc_btn)
        else:
            self._hint_label.pack_forget()

    def _build_analogs_manager(self, parent: ttk.LabelFrame) -> None:
        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill="x", pady=(0, 6))

        ttk.Button(
            btn_bar,
            text="🔍 Подобрать из БД",
            command=self._manual_pick_analogs,
            width=20,
        ).pack(side="left", padx=3)
        ttk.Button(btn_bar, text="➕ Добавить", command=self._add_analog, width=12).pack(
            side="left", padx=3
        )
        ttk.Button(
            btn_bar, text="✏️ Изменить", command=self._edit_selected_analog, width=12
        ).pack(side="left", padx=3)
        ttk.Button(btn_bar, text="❌ Удалить", command=self._delete_selected_analog, width=11).pack(
            side="left", padx=3
        )
        ttk.Button(
            btn_bar, text="📁 Сменить БД...", command=self._select_db_file, width=14
        ).pack(side="right", padx=3)

        table_frame = ttk.Frame(parent)
        table_frame.pack(fill="both", expand=True)

        columns = ("name", "price", "age", "mileage", "discount", "deflator", "city")
        self.analogs_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=6)
        self.analogs_tree.heading("name", text="Описание")
        self.analogs_tree.heading("price", text="Цена оферты (₽)")
        self.analogs_tree.heading("age", text="Tф (лет)")
        self.analogs_tree.heading("mileage", text="Пробег (км)")
        self.analogs_tree.heading("discount", text="Торг")
        self.analogs_tree.heading("deflator", text="К_прив")
        self.analogs_tree.heading("city", text="Город")

        self.analogs_tree.column("name", width=140)
        self.analogs_tree.column("price", width=105, anchor="e")
        self.analogs_tree.column("age", width=65, anchor="center")
        self.analogs_tree.column("mileage", width=90, anchor="e")
        self.analogs_tree.column("discount", width=65, anchor="center")
        self.analogs_tree.column("deflator", width=70, anchor="center")
        self.analogs_tree.column("city", width=100)

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.analogs_tree.yview)
        self.analogs_tree.configure(yscrollcommand=scroll_y.set)

        self.analogs_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.analogs_tree.bind("<Double-1>", lambda _e: self._edit_selected_analog())

        # Status row at bottom of analogs frame
        status_row = ttk.Frame(parent)
        status_row.pack(fill="x", pady=(4, 0))
        ttk.Label(
            status_row,
            textvariable=self.var_analogs_db_status,
            font=("Segoe UI", 8),
            foreground="#555",
        ).pack(side="left")

    def _build_results_view(self, parent: ttk.LabelFrame) -> None:
        top_summary = ttk.Frame(parent)
        top_summary.pack(fill="x", pady=(0, 6))

        # Value highlight box
        val_box = tk.LabelFrame(
            top_summary,
            text=" ИТОГОВАЯ РЫНОЧНАЯ СТОИМОСТЬ ",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4,
            bg="#f0f7ff",
        )
        val_box.pack(side="left", fill="y", padx=(0, 10))

        val_label = tk.Label(
            val_box,
            textvariable=self.res_market_value,
            font=("Segoe UI", 16, "bold"),
            fg="#004085",
            bg="#f0f7ff",
        )
        val_label.pack()

        # Stats box
        stats_frame = ttk.Frame(top_summary)
        stats_frame.pack(side="left", fill="both", expand=True)

        row1 = ttk.Frame(stats_frame)
        row1.pack(fill="x", pady=1)
        ttk.Label(row1, text="Однородность выборки (Этап 2):", font=("Segoe UI", 9, "bold")).pack(
            side="left"
        )
        ttk.Label(row1, textvariable=self.res_variation).pack(side="left", padx=6)

        row2 = ttk.Frame(stats_frame)
        row2.pack(fill="x", pady=1)
        ttk.Label(row2, text="Физический износ объекта (Этап 3):", font=("Segoe UI", 9, "bold")).pack(
            side="left"
        )
        ttk.Label(row2, textvariable=self.res_target_wear).pack(side="left", padx=6)

        # Report button
        ttk.Button(
            top_summary,
            text="📄 Полный отчет (текст экспертизы)",
            command=self._show_text_report,
            width=30,
        ).pack(side="right", padx=6, pady=4)

        # Target vehicle coefficient breakdown (analogs are not itemized here)
        coeff_group = ttk.LabelFrame(
            parent,
            text=" Коэффициенты объекта исследования ",
            padding=6,
        )
        coeff_group.pack(side="top", fill="both", expand=True)

        columns = ("symbol", "name", "formula", "value")
        self.coeff_tree = ttk.Treeview(coeff_group, columns=columns, show="headings", height=10)
        headers = {
            "symbol": ("Обозн.", 70, "center"),
            "name": ("Показатель", 260, "w"),
            "formula": ("Формула / подстановка", 460, "w"),
            "value": ("Значение", 150, "e"),
        }
        for col, (title, width, anchor) in headers.items():
            self.coeff_tree.heading(col, text=title)
            self.coeff_tree.column(col, width=width, anchor=anchor, stretch=col == "formula")

        self.coeff_tree.tag_configure("odd", background="#f7f9fc")
        self.coeff_tree.tag_configure("key", background="#e8f1ff", font=("Segoe UI", 9, "bold"))
        self.coeff_tree.tag_configure(
            "total", background="#d4edda", foreground="#155724", font=("Segoe UI", 10, "bold")
        )

        scroll_c_y = ttk.Scrollbar(coeff_group, orient="vertical", command=self.coeff_tree.yview)
        self.coeff_tree.configure(yscrollcommand=scroll_c_y.set)
        self.coeff_tree.pack(side="left", fill="both", expand=True)
        scroll_c_y.pack(side="right", fill="y")

    def _add_analog(self) -> None:
        def on_save(data: dict[str, Any]) -> None:
            self.analogs_list.append(data)
            self._refresh_analogs_table()

        AnalogEditDialog(self.window, on_save=on_save)

    def _edit_selected_analog(self) -> None:
        selected = self.analogs_tree.selection()
        if not selected:
            messagebox.showinfo("Редактирование", "Выберите аналог для редактирования")
            return
        idx = int(selected[0])
        analog_data = self.analogs_list[idx]

        def on_save(data: dict[str, Any]) -> None:
            self.analogs_list[idx] = data
            self._refresh_analogs_table()

        AnalogEditDialog(self.window, analog_data=analog_data, on_save=on_save)

    def _delete_selected_analog(self) -> None:
        selected = self.analogs_tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите аналог для удаления")
            return
        idx = int(selected[0])
        del self.analogs_list[idx]
        self._refresh_analogs_table()

    def _refresh_analogs_table(self) -> None:
        for item in self.analogs_tree.get_children():
            self.analogs_tree.delete(item)

        for i, an in enumerate(self.analogs_list):
            disc_str = f"{an['discount'] * 100:.1f}%" if an.get("discount") is not None else "Авто"
            vals = (
                an.get("name", f"Аналог {i+1}"),
                f"{int(an['price']):,}".replace(",", " "),
                f"{an['age_years']:.1f}",
                f"{int(an['mileage_km']):,}".replace(",", " "),
                disc_str,
                f"{an.get('deflator', 1.0):.4f}",
                an.get("city", ""),
            )
            self.analogs_tree.insert("", "end", iid=str(i), values=vals)

    def _manual_pick_analogs(self) -> None:
        """Trigger analog picking manually from button."""
        self._auto_pick_analogs(silent=False)

    def _select_db_file(self) -> None:
        """Select database file for analogs lookup."""
        path = filedialog.askopenfilename(
            title="Выберите файл базы аналогов",
            filetypes=[
                ("Базы SQLite", "*.db *.sqlite *.sqlite3"),
                ("Все файлы", "*.*"),
            ],
        )
        if path:
            self.var_db_path.set(path)
            self.var_analogs_db_status.set(f"База данных: {Path(path).name}")
            self._auto_pick_analogs(silent=False)

    def _auto_pick_analogs(self, silent: bool = False) -> bool:
        """Automatically find analogs from active database (sales.db/cars.db)."""
        brand = self.var_brand.get().strip()
        model = self.var_model.get().strip()
        if not brand and not model:
            if not silent:
                messagebox.showwarning(
                    "Поиск аналогов", "Укажите марку или модель автомобиля для подбора."
                )
            return False

        year_val: int | None = None
        try:
            year_val = int(self.var_year.get().strip())
        except ValueError:
            pass

        target_age_val: float | None = None
        try:
            target_age_val = float(self.var_age.get().strip().replace(",", "."))
        except ValueError:
            pass

        target_mileage_val: float | None = None
        try:
            target_mileage_val = float(
                self.var_mileage.get().strip().replace(" ", "").replace(",", ".")
            )
        except ValueError:
            pass

        val_date = self.var_date.get().strip() or None
        db_path = Path(self.var_db_path.get().strip())
        if not db_path.exists():
            db_path = AnalogSelector.get_default_db()

        analogs = AnalogSelector.find_analogs(
            mark=brand,
            model=model,
            year=year_val,
            valuation_date=val_date,
            target_age=target_age_val,
            target_mileage=target_mileage_val,
            db_path=db_path,
            limit=10,
            min_required=3,
            allow_fallback=self.var_auto_fallback.get(),
        )

        if analogs:
            self.analogs_list = analogs
            self._refresh_analogs_table()
            source_name = analogs[0].get("db_source", db_path.name)
            self.var_analogs_db_status.set(
                f"База: {source_name} (загружено аналогов: {len(analogs)})"
            )
            if not silent:
                messagebox.showinfo(
                    "Подбор аналогов",
                    f"Найдено и загружено {len(analogs)} аналогов из базы '{source_name}'.",
                )
            return True
        else:
            self.var_analogs_db_status.set(
                f"База: {db_path.name} (аналоги для '{brand} {model}' не найдены)"
            )
            if not silent:
                self._show_no_analogs_dialog(brand, model)
            return False

    def _show_no_analogs_dialog(self, brand: str, model: str) -> None:
        """Display helpful guidance when fewer than 3 analogs are found in DB."""
        db_name = Path(self.var_db_path.get()).name
        cars_db_available = AnalogSelector.FULL_CARS_DB.exists()
        current_count = len(self.analogs_list)

        msg = (
            f"В базе данных '{db_name}' найдено {current_count} аналогов для '{brand} {model}'.\n"
            "По методике СЭЦ СК РФ и Минюста РФ требуется минимум 3 аналога.\n\n"
        )
        if db_name == "sales.db":
            msg += (
                "ℹ️ Файл 'sales.db' содержит 6 тестовых записей (Aston Martin DB9/DBS).\n\n"
            )

        if cars_db_available and db_name != "cars.db":
            msg += (
                "Найдена полная база 'cars.db' (12.1 млн записей).\n"
                "Переключить поиск на полную базу cars.db?"
            )
            ans = messagebox.askyesno("Подбор аналогов", msg)
            if ans:
                self.var_db_path.set(str(AnalogSelector.FULL_CARS_DB))
                self.var_analogs_db_status.set("База данных: cars.db (12.1 млн записей)")
                if self._auto_pick_analogs(silent=False):
                    self.calculate_valuation()
        else:
            msg += (
                "Что можно сделать:\n"
                "1. Нажмите '📁 Сменить БД...', чтобы выбрать другой файл базы данных.\n"
                "2. Нажмите '⭐ Эталон' для загрузки эталонных данных судебной практики.\n"
                "3. Добавьте аналоги вручную кнопкой '➕ Добавить'."
            )
            messagebox.showwarning("Недостаточно аналогов", msg)

    def calculate_valuation(self) -> None:
        """Run complete 8-stage valuation pipeline."""
        brand = self.var_brand.get().strip()
        model = self.var_model.get().strip()

        # Check if loaded analogs mismatch the current vehicle
        mismatch = False
        if self.analogs_list and brand:
            mismatch = not any(
                brand.lower() in str(an.get("name", "")).lower() for an in self.analogs_list
            )

        if len(self.analogs_list) < 3 or mismatch:
            # Auto-attempt retrieval from database
            self._auto_pick_analogs(silent=True)
            if len(self.analogs_list) < 3:
                self._show_no_analogs_dialog(brand, model)
                return

        try:
            year = int(self.var_year.get().strip())
            age = float(self.var_age.get().strip().replace(",", "."))
            mileage = float(self.var_mileage.get().strip().replace(" ", "").replace(",", "."))
            moral_wear = float(self.var_moral_wear.get().strip().replace(",", "."))
            repair = float(self.var_repair_cost.get().strip().replace(" ", "").replace(",", "."))

            target = TargetVehicleInput(
                brand=self.var_brand.get().strip() or "ТС",
                model=self.var_model.get().strip() or "Модель",
                year=year,
                age_years=age,
                mileage_km=mileage,
                vehicle_category=self.var_category.get().strip(),
                vin=self.var_vin.get().strip() or None,
                registration_plate=self.var_plate.get().strip() or None,
                valuation_date=self.var_date.get().strip() or None,
                moral_wear_pct=moral_wear,
                repair_cost=repair,
            )

            analogs: list[AnalogVehicleInput] = []
            for i, an in enumerate(self.analogs_list):
                analogs.append(
                    AnalogVehicleInput(
                        id=f"A{i+1}",
                        name=an.get("name", f"Аналог {i+1}"),
                        price=float(an["price"]),
                        age_years=float(an["age_years"]),
                        mileage_km=float(an["mileage_km"]),
                        bargaining_discount=an.get("discount"),
                        deflator=an.get("deflator"),
                        city=an.get("city"),
                    )
                )

            request = ValuationRequest(target=target, analogs=analogs)
            report = self.service.evaluate(request)
            self.last_report = report

            self._display_report(report)

        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Не удалось выполнить расчет:\n{e!s}")

    def _display_report(self, report: ValuationReport) -> None:
        self.res_market_value.set(f"{report.market_value:,} руб.".replace(",", " "))

        var = report.variation_analysis
        homo_str = "Однородна (v ≤ 30%)" if var.is_homogeneous else "НЕОДНОРОДНА (v > 30%)"
        self.res_variation.set(
            f"v = {var.variation_coefficient * 100:.2f}% (C_ср = {int(var.mean_price):,}, σ = {int(var.std_dev):,}) — {homo_str}".replace(
                ",", " "
            )
        )

        self.res_target_wear.set(
            f"Иф = {report.target_wear_pct:.2f}% (Ω = {report.target_omega:.5f})"
        )

        # Clear and fill target coefficient breakdown
        for item in self.coeff_tree.get_children():
            self.coeff_tree.delete(item)

        key_symbols = {"Ω", "Иф", "Сср"}
        for i, (symbol, name, formula, value) in enumerate(
            _build_target_coefficient_rows(report)
        ):
            if symbol == "Ств":
                tag = "total"
            elif symbol in key_symbols:
                tag = "key"
            else:
                tag = "odd" if i % 2 else ""
            self.coeff_tree.insert("", "end", values=(symbol, name, formula, value), tags=(tag,))

    def _show_text_report(self) -> None:
        if not self.last_report:
            messagebox.showinfo("Отчет", "Сначала выполните расчет кнопкой 'Рассчитать'.")
            return

        rep = self.last_report
        t = rep.target_vehicle

        text = [
            "=" * 78,
            "ЗАКЛЮЧЕНИЕ ЭКСПЕРТА (РАСЧЕТНАЯ ЧАСТЬ СРАВНИТЕЛЬНОГО ПОДХОДА)",
            "в соответствии со стандартами СЭЦ СК России и Минюста РФ",
            "=" * 78,
            f"Объект исследования: {t.brand} {t.model} ({t.year} г.в.)",
            f"VIN: {t.vin or 'не указан'} | Гос. знак: {t.registration_plate or 'не указан'}",
            f"Страна-производитель: {rep.target_country or 'не определена'}",
            f"Фактический пробег: {int(t.mileage_km):,} км | Фактический возраст: {t.age_years} лет",
            f"Категория ТС: {t.vehicle_category}",
            f"Дата фиксации оценки: {rep.valuation_date or 'на дату расчета'}",
            "-" * 78,
            "1. ПРОВЕРКА ВЫБОРКИ НА ОДНОРОДНОСТЬ (Этап 2):",
            f"   Средняя цена выборки C_ср = {int(rep.variation_analysis.mean_price):,} руб.",
            f"   Выборочное стандартное отклонение s = {int(rep.variation_analysis.std_dev):,} руб.",
            f"   Коэффициент вариации v = {rep.variation_analysis.variation_coefficient:.4f} ({rep.variation_analysis.variation_coefficient*100:.2f}%)",
            f"   Критерий: v <= 0.30 -> {'Совокупность ОДНОРОДНА, выборка валидна' if rep.variation_analysis.is_homogeneous else 'Выборка неоднородна'}",
            "-" * 78,
            "2. КОЭФФИЦИЕНТЫ ОБЪЕКТА ИССЛЕДОВАНИЯ:",
        ]

        for symbol, name, formula, value in _build_target_coefficient_rows(rep):
            if symbol == "Ств":
                continue
            line = f"   {symbol:<6} {name}"
            if formula:
                line += f": {formula}"
            if value:
                line += f" = {value}"
            text.append(line)

        text.extend([
            "=" * 78,
            f"ИТОГОВАЯ РЫНОЧНАЯ СТОИМОСТЬ: {_fmt_money(rep.market_value)} РУБЛЕЙ.",
            "=" * 78,
        ])

        report_str = "\n".join(text)

        report_win = tk.Toplevel(self.window)
        report_win.title("Экспертное заключение — Сравнительный подход")
        report_win.geometry("780x600")

        txt_box = tk.Text(report_win, wrap="word", font=("Consolas", 10), padx=8, pady=8)
        txt_box.pack(fill="both", expand=True)
        txt_box.insert("1.0", report_str)
        txt_box.config(state="disabled")

        btn_row = ttk.Frame(report_win, padding=6)
        btn_row.pack(fill="x")

        def copy_to_clipboard() -> None:
            report_win.clipboard_clear()
            report_win.clipboard_append(report_str)
            messagebox.showinfo("Буфер обмена", "Текст заключения скопирован в буфер обмена.")

        ttk.Button(btn_row, text="📋 Скопировать текст", command=copy_to_clipboard).pack(
            side="left", padx=6
        )
        ttk.Button(btn_row, text="Закрыть", command=report_win.destroy).pack(side="right", padx=6)

    def _open_db_selector(self) -> None:
        """Open selector for vehicles stored in local DB."""
        if not self.controller:
            messagebox.showwarning("БД", "Контроллер базы данных недоступен.")
            return

        records = self.controller.get_saved_records()
        if not records:
            messagebox.showinfo("БД", "В базе данных пока нет сохраненных записей.")
            return

        def on_select(record_id: int) -> None:
            data = self.controller.get_record_data(record_id)
            if data:
                self._fill_from_dict(data)

        DbRecordsWindow(self.window, records, on_select)

    def _fill_from_dict(self, data: dict[str, Any]) -> None:
        if data.get("mark"):
            self.var_brand.set(str(data["mark"]))
        if data.get("model"):
            self.var_model.set(str(data["model"]))
        if data.get("year_ts"):
            self.var_year.set(str(data["year_ts"]))
            try:
                y = int(data["year_ts"])
                now_y = datetime.now().year
                self.var_age.set(str(max(1, now_y - y)))
            except ValueError:
                pass
        if data.get("count_kilometers"):
            self.var_mileage.set(str(data["count_kilometers"]))
        if data.get("date_deal"):
            self.var_date.set(str(data["date_deal"]))
        if data.get("vin"):
            self.var_vin.set(str(data["vin"]))
        brand = str(data.get("mark", ""))
        if brand:
            type_ts = str(data.get("type_ts", ""))
            self.var_category.set(detect_vehicle_category(brand, vin=str(data.get("vin", "")), type_ts=type_ts))

    def _load_benchmark_gac(self) -> None:
        """Load benchmark GAC M8 parameters from case 4440/25e."""
        self.var_brand.set("GAC")
        self.var_model.set("M8")
        self.var_year.set("2023")
        self.var_age.set("1")
        self.var_mileage.set("92088")
        self.var_category.set("Легковые автомобили азиатские (кроме Японии)")
        self.var_vin.set("LMGMU1G81P1168719")
        self.var_plate.set("С 555 ВР 777")
        self.var_date.set("2024-09-02")
        self.var_moral_wear.set("0")
        self.var_repair_cost.set("0")

        self.analogs_list = [
            {
                "name": "Аналог № 1 (Казань)",
                "price": 4350000.0,
                "age_years": 2.0,
                "mileage_km": 14000.0,
                "discount": 0.05,
                "deflator": 0.9325,
                "city": "Казань",
            },
            {
                "name": "Аналог № 2 (Омск)",
                "price": 4390000.0,
                "age_years": 2.0,
                "mileage_km": 22000.0,
                "discount": 0.05,
                "deflator": 0.9254,
                "city": "Омск",
            },
            {
                "name": "Аналог № 3 (Краснодар)",
                "price": 4790000.0,
                "age_years": 2.0,
                "mileage_km": 17800.0,
                "discount": 0.05,
                "deflator": 0.9254,
                "city": "Краснодар",
            },
        ]
        self._refresh_analogs_table()
        self.calculate_valuation()

    def _load_benchmark_sollers(self) -> None:
        """Load benchmark Sollers Atlant parameters from case 4440/25e."""
        self.var_brand.set("Sollers")
        self.var_model.set("Atlant")
        self.var_year.set("2023")
        self.var_age.set("1")
        self.var_mileage.set("25618")
        self.var_category.set("Легковые автомобили отечественные")
        self.var_vin.set("ЕВЕ66S209P0005012")
        self.var_plate.set("Т 592 АХ 550")
        self.var_date.set("2024-08-29")
        self.var_moral_wear.set("0")
        self.var_repair_cost.set("0")

        self.analogs_list = [
            {
                "name": "Аналог № 1 (Москва)",
                "price": 1908000.0,
                "age_years": 2.0,
                "mileage_km": 62271.0,
                "discount": 0.06,
                "deflator": 0.932080,
                "city": "Москва",
            },
            {
                "name": "Аналог № 2 (Раменское)",
                "price": 2050099.0,
                "age_years": 2.0,
                "mileage_km": 39000.0,
                "discount": 0.06,
                "deflator": 0.924686,
                "city": "Раменское",
            },
            {
                "name": "Аналог № 3 (Новосибирск)",
                "price": 2200000.0,
                "age_years": 2.0,
                "mileage_km": 20000.0,
                "discount": 0.06,
                "deflator": 0.924686,
                "city": "Новосибирск",
            },
        ]
        self._refresh_analogs_table()
        self.calculate_valuation()

    def _clear_all(self) -> None:
        self.var_brand.set("")
        self.var_model.set("")
        self.var_year.set("")
        self.var_age.set("1")
        self.var_mileage.set("")
        self.var_vin.set("")
        self.var_plate.set("")
        self.var_moral_wear.set("0")
        self.var_repair_cost.set("0")
        self.analogs_list.clear()
        self._refresh_analogs_table()
        for item in self.coeff_tree.get_children():
            self.coeff_tree.delete(item)
        self.res_market_value.set("—")
        self.res_variation.set("—")
        self.res_target_wear.set("—")
