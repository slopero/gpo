import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

class ExternalDB:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def __init__(self, db_path: Optional[Path] = None, progress_callback=None):
        self.db_path = db_path
        self.data = None
        self.db_type = None
        self.table_name = None
        self.column_mapping = {}
        self.conn = None
        self.cursor = None
        self.all_columns = []
        self.progress_callback = progress_callback
        
        if db_path and db_path.exists():
            self.load_database(db_path)

    def select_database_interactive(self) -> bool:
        """Интерактивный выбор файла базы данных"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл базы данных",
            filetypes=[
                ("Базы данных", "*.db *.sqlite *.sqlite3"),
                ("CSV файлы", "*.csv"),
                ("Excel файлы", "*.xlsx *.xls"),
                ("Все файлы", "*.*")
            ]
        )
        
        if not file_path:
            return False
            
        return self.load_database(Path(file_path))

    def load_database(self, file_path: Path) -> bool:
        self.db_path = file_path
        ext = file_path.suffix.lower()
        try:
            if ext in ['.db', '.sqlite', '.sqlite3']:
                return self._load_sqlite()
            elif ext == '.csv':
                return self._load_csv()
            elif ext in ['.xlsx', '.xls']:
                return self._load_excel()
            else:
                messagebox.showerror("Ошибка", f"Неподдерживаемый формат файла: {ext}")
                return False
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить БД:\n{str(e)}")
            return False

    def _load_sqlite(self) -> bool:
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in self.cursor.fetchall()]
        if not tables:
            messagebox.showerror("Ошибка", "В базе данных нет таблиц")
            return False
    
        self.table_name = "cars" if "cars" in tables else tables[0]
        self.cursor.execute(f"PRAGMA table_info('{self.table_name}')")
        columns_info = self.cursor.fetchall()
        self.all_columns = [col[1] for col in columns_info]
    
        # Загружаем пример для маппинга
        self.cursor.execute(f"SELECT * FROM '{self.table_name}' LIMIT 5")
        sample = self.cursor.fetchall()
        
        self.data = pd.DataFrame(sample, columns=self.all_columns)
        self._auto_map_columns()
        self.data = None
        self.db_type = 'sqlite'
        
        if self.progress_callback:
            self.progress_callback(f"Загружена таблица: {self.table_name}", 50)
        
        return True

    def _load_csv(self) -> bool:
        """Загрузка CSV файла"""
        self.data = pd.read_csv(self.db_path)
        self.all_columns = list(self.data.columns)
        self._auto_map_columns()
        self.db_type = 'csv'
        self.table_name = self.db_path.stem
        return True

    def _load_excel(self) -> bool:
        """Загрузка Excel файла"""
        self.data = pd.read_excel(self.db_path)
        self.all_columns = list(self.data.columns)
        self._auto_map_columns()
        self.db_type = 'excel'
        self.table_name = self.db_path.stem
        return True

    def _auto_map_columns(self):
        mapping_rules = {
            'mark': ['марка', 'mark', 'brand', 'make', 'производитель'],
            'model': ['модель', 'model', 'модель_авто'],
            'mark_model': ['название_машины', 'name', 'марка_модель', 'full_name', 'автомобиль'],
            'year': ['год', 'year', 'год_выпуска', 'year_of_manufacture'],
            'ad_date': ['дата_размещения_объявления', 'date', 'дата', 'ad_date', 'publication_date'],
            'region': ['регион', 'region', 'город', 'city', 'location'],
            'power': ['мощность', 'power', 'лс', 'horsepower', 'hp'],
            'volume': ['объем_двигателя', 'volume', 'объем', 'engine_volume', 'displacement'],
            'engine': ['тип_двигателя', 'engine_type', 'топливо', 'fuel', 'engine'],
            'transmission': ['коробка_передач', 'transmission', 'кпп', 'gear', 'gearbox', 'transmission_type'],
            'body_type': ['тип_кузова', 'body_type', 'кузов', 'body'],
            'type_ts': ['тип_техники', 'категория_тс', 'type_ts', 'vehicle_type', 'category'],
            'price': ['цена', 'price', 'стоимость', 'cost', 'price_rub']
        }
        
        col_lower = {col.lower(): col for col in self.all_columns}
        for target, possible_names in mapping_rules.items():
            for name in possible_names:
                if name in col_lower:
                    self.column_mapping[target] = col_lower[name]
                    break

    def find_similar(self, source_data: dict[str, Any]) -> list[dict]:
        """Основной метод поиска аналогов"""
        if self.db_type == 'sqlite' and self.conn:
            return self._find_similar_sqlite(source_data)
        elif self.db_type in ['csv', 'excel'] and self.data is not None:
            return self._find_similar_dataframe(source_data)
        return []

    def _find_similar_sqlite(self, source_data: dict[str, Any]) -> list[dict]:
        """Поиск аналогов в SQLite"""
        if not self.table_name: 
            return []
        
        conditions = []
        params = []

        # 1. Марка и Модель - Гибкий поиск
        mark = self._safe_strip(source_data.get("mark"))
        model = self._safe_strip(source_data.get("model"))
        
        has_mark_model_field = 'mark_model' in self.column_mapping
        
        if mark or model:
            if has_mark_model_field:
                col = self.column_mapping['mark_model']
                
                if mark and model:
                    full_name = f"{mark} {model}"
                    conditions.append(f"LOWER(\"{col}\") = LOWER(?) OR (LOWER(\"{col}\") LIKE ? AND LOWER(\"{col}\") LIKE ?)")
                    params.extend([full_name, f"%{mark.lower()}%", f"%{model.lower()}%"])
                elif mark:
                    conditions.append(f"LOWER(\"{col}\") LIKE ?")
                    params.append(f"%{mark.lower()}%")
                elif model:
                    conditions.append(f"LOWER(\"{col}\") LIKE ?")
                    params.append(f"%{model.lower()}%")
        
        # 2. Год выпуска
        year = self._to_int(source_data.get("year_ts"))
        if year and 'year' in self.column_mapping:
            conditions.append(f"ABS(\"{self.column_mapping['year']}\" - ?) <= 2")
            params.append(year)
        
        # 3. Регион
        region = self._safe_strip(source_data.get("region"))
        if region and 'region' in self.column_mapping:
            conditions.append(f"LOWER(\"{self.column_mapping['region']}\") LIKE LOWER(?)")
            params.append(f"%{region}%")
        
        # 4. Мощность
        power = self._to_int(source_data.get("power"))
        if power and 'power' in self.column_mapping:
            conditions.append(f"ABS(\"{self.column_mapping['power']}\" - ?) <= 30")
            params.append(power)
        
        # 5. Объем двигателя
        volume = self._to_float(source_data.get("volume"))
        if volume and 'volume' in self.column_mapping:
            conditions.append(f"ABS(\"{self.column_mapping['volume']}\" - ?) <= 1.0")
            params.append(volume)
        
        # 6. Тип двигателя
        engine = self._safe_strip(source_data.get("type_engine"))
        if engine and 'engine' in self.column_mapping:
            conditions.append(f"LOWER(\"{self.column_mapping['engine']}\") LIKE LOWER(?)")
            params.append(f"{engine[:4].lower()}%")
        
        # 7. Тип КПП
        kpp = self._safe_strip(source_data.get("type_kpp"))
        if kpp and 'transmission' in self.column_mapping:
            col = self.column_mapping['transmission']
            if "мех" in kpp.lower():
                keyword = "%мех%"
            elif "авт" in kpp.lower():
                keyword = "%авт%"
            else:
                keyword = f"%{kpp.lower()}%"
            conditions.append(f"LOWER(\"{col}\") LIKE ?")
            params.append(keyword)
        
        # 8. Тип кузова
        body = self._safe_strip(source_data.get("type_body"))
        if body and 'body_type' in self.column_mapping:
            conditions.append(f"LOWER(\"{self.column_mapping['body_type']}\") LIKE LOWER(?)")
            params.append(f"%{body.lower()}%")
        
        # 9. Тип ТС
        type_ts = self._safe_strip(source_data.get("type_ts"))
        if type_ts and 'type_ts' in self.column_mapping:
            conditions.append(f"LOWER(\"{self.column_mapping['type_ts']}\") LIKE LOWER(?)")
            params.append(f"%{type_ts.lower()}%")
        
        target_date = source_data.get("date_deal") or datetime.now().strftime("%Y-%m-%d")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        date_col = self.column_mapping.get('ad_date')
        if date_col and date_col in self.all_columns:
            order_by = f"ABS(JULIANDAY(\"{date_col}\") - JULIANDAY(?)) ASC"
            params.append(target_date)
        else:
            order_by = "1"
        
        query = f"""
            SELECT * FROM "{self.table_name}"
            WHERE {where_clause}
            ORDER BY {order_by}
            LIMIT 150
        """

        try:
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            
            if rows:
                col_names = [desc[0] for desc in self.cursor.description]
                return [dict(zip(col_names, row)) for row in rows]
            return []
        except Exception:
            logger.exception("SQL query failed in _find_similar_sqlite")
            return []

    def _find_similar_dataframe(self, source_data: dict[str, Any]) -> list[dict]:
        """Поиск аналогов в DataFrame (CSV/Excel)"""
        if self.data is None or self.data.empty:
            return []
        
        df = self.data.copy()
        mask = pd.Series([True] * len(df))
        
        # Применяем фильтры
        mark = self._safe_strip(source_data.get("mark"))
        model = self._safe_strip(source_data.get("model"))
        
        if mark and 'mark_model' in self.column_mapping:
            col = self.column_mapping['mark_model']
            if model:
                mask &= df[col].astype(str).str.contains(mark, case=False, na=False)
                mask &= df[col].astype(str).str.contains(model, case=False, na=False)
            else:
                mask &= df[col].astype(str).str.contains(mark, case=False, na=False)
        
        year = self._to_int(source_data.get("year_ts"))
        if year and 'year' in self.column_mapping:
            col = self.column_mapping['year']
            mask &= (df[col].astype(float) - year).abs() <= 2
        
        region = self._safe_strip(source_data.get("region"))
        if region and 'region' in self.column_mapping:
            col = self.column_mapping['region']
            mask &= df[col].astype(str).str.contains(region, case=False, na=False)
        
        filtered_df = df[mask]
        
        return filtered_df.head(150).to_dict('records')

    def _safe_strip(self, val) -> str:
        return str(val).strip() if val else ""

    def _to_int(self, val) -> Optional[int]:
        try:
            return int(float(str(val).replace(',', '.')))
        except (ValueError, TypeError):
            return None

    def _to_float(self, val) -> Optional[float]:
        try:
            return float(str(val).replace(',', '.'))
        except (ValueError, TypeError):
            return None

    def close(self):
        if self.conn:
            self.conn.close()