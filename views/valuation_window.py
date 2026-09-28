"""Window for judicial vehicle valuation via comparative sales approach (SEC SK RF / Minyust RF)."""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from app.services.valuation.constants import (
    BARGAINING_DISCOUNTS,
    WEAR_COEFFICIENTS,
    BargainingCategory,
    VehicleWearCategory,
)
from app.services.valuation.schemas import (
    AnalogVehicleInput,
    TargetVehicleInput,
    ValuationReport,
    ValuationRequest,
)
from app.services.valuation.service import ValuationService
from views.db_records_window import DbRecordsWindow


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

        # Result summary vars
        self.res_market_value = tk.StringVar(value="—")
        self.res_variation = tk.StringVar(value="—")
        self.res_target_wear = tk.StringVar(value="—")
        self.res_status = tk.StringVar(
            value="Заполните объект и добавьте минимум 3 аналога, затем нажмите 'Рассчитать'."
        )

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
            text=" 3. Экспертный расчет и согласование стоимости (8 этапов СЭЦ СК РФ) ",
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
        calc_btn.pack(fill="x", pady=(10, 0))

    def _build_analogs_manager(self, parent: ttk.LabelFrame) -> None:
        btn_bar = ttk.Frame(parent)
        btn_bar.pack(fill="x", pady=(0, 6))

        ttk.Button(btn_bar, text="➕ Добавить аналог", command=self._add_analog, width=18).pack(
            side="left", padx=4
        )
        ttk.Button(
            btn_bar, text="✏️ Редактировать", command=self._edit_selected_analog, width=18
        ).pack(side="left", padx=4)
        ttk.Button(btn_bar, text="❌ Удалить", command=self._delete_selected_analog, width=14).pack(
            side="left", padx=4
        )

        columns = ("name", "price", "age", "mileage", "discount", "deflator", "city")
        self.analogs_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
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

        scroll_y = ttk.Scrollbar(parent, orient="vertical", command=self.analogs_tree.yview)
        self.analogs_tree.configure(yscrollcommand=scroll_y.set)

        self.analogs_tree.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.analogs_tree.bind("<Double-1>", lambda _e: self._edit_selected_analog())

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

        # 8-step matrix treeview
        columns = (
            "idx",
            "c_orig",
            "wear_an",
            "k_wear",
            "c1",
            "disc",
            "c2",
            "k_priv",
            "c_skorr",
            "r",
            "delta",
            "d",
            "k_v",
            "c_weighted",
        )

        self.matrix_tree = ttk.Treeview(parent, columns=columns, show="headings", height=7)
        headers = {
            "idx": "№",
            "c_orig": "Цена исх (₽)",
            "wear_an": "Износ Иф",
            "k_wear": "К_износ",
            "c1": "Цена C1 (₽)",
            "disc": "Скидка торг",
            "c2": "Цена C2 (₽)",
            "k_priv": "К_прив",
            "c_skorr": "Скорр. Cск (₽)",
            "r": "r_i",
            "delta": "Δ_i",
            "d": "d_i",
            "k_v": "Вес Квi",
            "c_weighted": "Взвеш. цена (₽)",
        }
        for col, title in headers.items():
            self.matrix_tree.heading(col, text=title)
            w = 50 if col == "idx" else 75
            if col in ("c_orig", "c1", "c2", "c_skorr", "c_weighted"):
                w = 95
            self.matrix_tree.column(col, width=w, anchor="e" if "₽" in title or col == "idx" else "center")

        scroll_m_y = ttk.Scrollbar(parent, orient="vertical", command=self.matrix_tree.yview)
        scroll_m_x = ttk.Scrollbar(parent, orient="horizontal", command=self.matrix_tree.xview)
        self.matrix_tree.configure(
            yscrollcommand=scroll_m_y.set, xscrollcommand=scroll_m_x.set
        )

        self.matrix_tree.pack(side="top", fill="both", expand=True)
        scroll_m_y.pack(side="right", fill="y")
        scroll_m_x.pack(side="bottom", fill="x")

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

    def calculate_valuation(self) -> None:
        """Run complete 8-stage valuation pipeline."""
        if len(self.analogs_list) < 3:
            messagebox.showwarning(
                "Недостаточно аналогов",
                f"По методике СЭЦ СК РФ требуется минимум 3 аналога (сейчас: {len(self.analogs_list)}).\n"
                "Добавьте аналоги вручную или загрузите эталон.",
            )
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

        # Clear and fill 8-step matrix
        for item in self.matrix_tree.get_children():
            self.matrix_tree.delete(item)

        for i, res in enumerate(report.analog_results, 1):
            row_vals = (
                str(i),
                f"{int(res.original_price):,}".replace(",", " "),
                f"{res.wear_pct:.2f}%",
                f"{res.k_wear:.4f}",
                f"{int(round(res.price_after_wear)):,}".replace(",", " "),
                f"-{res.bargaining_discount * 100:.1f}%",
                f"{int(round(res.price_after_bargaining)):,}".replace(",", " "),
                f"{res.deflator:.4f}",
                f"{int(round(res.adjusted_price)):,}".replace(",", " "),
                f"{res.scale_ratio:.4f}",
                f"{res.abs_delta:.4f}",
                f"{res.relative_share_d:.4f}",
                f"{res.weight:.4f}",
                f"{int(round(res.weighted_price)):,}".replace(",", " "),
            )
            self.matrix_tree.insert("", "end", values=row_vals)

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
            "2. ФИЗИЧЕСКИЙ ИЗНОС ОБЪЕКТА (Этап 3):",
            f"   Интенсивность эксплуатации Omega = {rep.target_omega:.5f}",
            f"   Физический износ Иф = {rep.target_wear_pct:.2f}%",
            "-" * 78,
            "3. ТАБЛИЦА СКОРРЕКТИРОВАННЫХ ЦЕН И ВЕСОВЫХ КОЭФФИЦИЕНТОВ:",
        ]

        for i, a in enumerate(rep.analog_results, 1):
            text.extend([
                f"   Аналог № {i} ({a.analog_id}):",
                f"     - Исходная цена оферты: {int(a.original_price):,} руб.",
                f"     - Износ аналога: {a.wear_pct:.2f}% | К_износ = {a.k_wear:.4f} -> C1 = {int(round(a.price_after_wear)):,} руб.",
                f"     - Скидка на торг: -{a.bargaining_discount*100:.1f}% -> C2 = {int(round(a.price_after_bargaining)):,} руб.",
                f"     - Дефлятор цен: К_прив = {a.deflator:.4f} -> C_скорр = {int(round(a.adjusted_price)):,} руб.",
                f"     - Отклонение: r_i = {a.scale_ratio:.4f}, Delta_i = {a.abs_delta:.4f}, Доля d_i = {a.relative_share_d:.4f}",
                f"     - Весовой коэффициент: К_в{i} = {a.weight:.4f}",
                f"     - Взвешенная стоимость: {int(round(a.weighted_price)):,} руб.",
            ])

        text.extend([
            "-" * 78,
            f"Сумма весовых коэффициентов: {rep.sum_weights:.4f} (контроль = 1.0000)",
            f"Моральный износ: {rep.moral_wear_pct:.1f}% | Затраты на ремонт: {int(rep.repair_cost):,} руб.",
            "=" * 78,
            f"ИТОГОВАЯ РЫНОЧНАЯ СТОИМОСТЬ: {rep.market_value:,} РУБЛЕЙ.".replace(",", " "),
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
        for item in self.matrix_tree.get_children():
            self.matrix_tree.delete(item)
        self.res_market_value.set("—")
        self.res_variation.set("—")
        self.res_target_wear.set("—")
