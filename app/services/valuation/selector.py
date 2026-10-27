"""Analog selector service for judicial vehicle valuation.

Searches sales databases (db/cars.db, db/sales.db) for matching market offers
and transforms them into validated inputs for the 8-stage comparative valuation pipeline.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.paths import cars_db_path, sales_db_path

BRAND_SYNONYMS: dict[str, list[str]] = {
    "lada": ["Лада", "Lada", "ВАЗ"],
    "ваз": ["Лада", "ВАЗ", "Lada"],
    "лада": ["Лада", "ВАЗ", "Lada"],
    "vaz": ["Лада", "ВАЗ", "Lada"],
    "hyundai": ["Hyundai", "Хендай", "Хёндай", "Хундай"],
    "хендай": ["Hyundai", "Хендай", "Хёндай", "Хундай"],
    "хёндай": ["Hyundai", "Хендай", "Хёндай", "Хундай"],
    "хундай": ["Hyundai", "Хендай", "Хёндай", "Хундай"],
    "kia": ["Kia", "Киа"],
    "киа": ["Kia", "Киа"],
    "toyota": ["Toyota", "Тойота"],
    "тойота": ["Toyota", "Тойота"],
    "volkswagen": ["Volkswagen", "Фольксваген", "VW"],
    "фольксваген": ["Volkswagen", "Фольксваген", "VW"],
    "vw": ["Volkswagen", "Фольксваген", "VW"],
    "bmw": ["BMW", "БМВ"],
    "бмв": ["BMW", "БМВ"],
    "mercedes": ["Mercedes-Benz", "Mercedes", "Мерседес"],
    "мерседес": ["Mercedes-Benz", "Mercedes", "Мерседес"],
    "mercedes-benz": ["Mercedes-Benz", "Mercedes", "Мерседес"],
    "nissan": ["Nissan", "Ниссан"],
    "ниссан": ["Nissan", "Ниссан"],
    "renault": ["Renault", "Рено"],
    "рено": ["Renault", "Рено"],
    "skoda": ["Skoda", "Шкода"],
    "шкода": ["Skoda", "Шкода"],
    "uaz": ["УАЗ", "UAZ"],
    "уаз": ["УАЗ", "UAZ"],
    "gaz": ["ГАЗ", "GAZ"],
    "газ": ["ГАЗ", "GAZ"],
    "audi": ["Audi", "Ауди"],
    "ауди": ["Audi", "Ауди"],
    "ford": ["Ford", "Форд"],
    "форд": ["Ford", "Форд"],
    "chevrolet": ["Chevrolet", "Шевроле"],
    "шевроле": ["Chevrolet", "Шевроле"],
    "mazda": ["Mazda", "Мазда"],
    "мазда": ["Mazda", "Мазда"],
    "mitsubishi": ["Mitsubishi", "Митсубиси", "Митсубиши"],
    "митсубиси": ["Mitsubishi", "Митсубиси", "Митсубиши"],
    "митсубиши": ["Mitsubishi", "Митсубиси", "Митсубиши"],
    "honda": ["Honda", "Хонда"],
    "хонда": ["Honda", "Хонда"],
    "subaru": ["Subaru", "Субару"],
    "субару": ["Subaru", "Субару"],
    "suzuki": ["Suzuki", "Сузуки"],
    "сузуки": ["Suzuki", "Сузуки"],
    "chery": ["Chery", "Чери"],
    "чери": ["Chery", "Чери"],
    "geely": ["Geely", "Джили"],
    "джили": ["Geely", "Джили"],
    "haval": ["Haval", "Хавейл", "Хавал"],
    "хавейл": ["Haval", "Хавейл", "Хавал"],
    "хавал": ["Haval", "Хавейл", "Хавал"],
    "lexus": ["Lexus", "Лексус"],
    "лексус": ["Lexus", "Лексус"],
    "infiniti": ["Infiniti", "Инфинити"],
    "инфинити": ["Infiniti", "Инфинити"],
    "volvo": ["Volvo", "Вольво"],
    "вольво": ["Volvo", "Вольво"],
    "peugeot": ["Peugeot", "Пежо"],
    "пежо": ["Peugeot", "Пежо"],
    "citroen": ["Citroen", "Ситроен"],
    "ситроен": ["Citroen", "Ситроен"],
    "aurus": ["Аурус", "Aurus"],
    "аурус": ["Аурус", "Aurus"],
    "aston martin": ["Aston Martin", "Астон Мартин", "Aston"],
    "астон мартин": ["Aston Martin", "Астон Мартин", "Aston"],
    "aston": ["Aston Martin", "Астон Мартин", "Aston"],
    "land rover": ["Land Rover", "Ленд Ровер", "Лэнд Ровер", "Land"],
    "ленд ровер": ["Land Rover", "Ленд Ровер", "Лэнд Ровер", "Land"],
    "лэнд ровер": ["Land Rover", "Ленд Ровер", "Лэнд Ровер", "Land"],
    "rolls-royce": ["Rolls-Royce", "Роллс-Ройс"],
    "роллс-ройс": ["Rolls-Royce", "Роллс-Ройс"],
    "bentley": ["Bentley", "Бентли"],
    "бентли": ["Bentley", "Бентли"],
    "cadillac": ["Cadillac", "Кадиллак"],
    "кадиллак": ["Cadillac", "Кадиллак"],
    "ferrari": ["Ferrari", "Феррари"],
    "феррари": ["Ferrari", "Феррари"],
    "genesis": ["Genesis", "Генезис", "Дженезис"],
    "генезис": ["Genesis", "Генезис", "Дженезис"],
    "hongqi": ["Hongqi", "Хончи", "Хунцы", "Хонгки"],
    "хончи": ["Hongqi", "Хончи", "Хунцы", "Хонгки"],
    "jaguar": ["Jaguar", "Ягуар"],
    "ягуар": ["Jaguar", "Ягуар"],
    "jeep": ["Jeep", "Джип"],
    "джип": ["Jeep", "Джип"],
    "lamborghini": ["Lamborghini", "Ламборгини", "Ламборджини"],
    "ламборгини": ["Lamborghini", "Ламборгини", "Ламборджини"],
    "maserati": ["Maserati", "Мазерати"],
    "мазерати": ["Maserati", "Мазерати"],
    "porsche": ["Porsche", "Порше"],
    "порше": ["Porsche", "Порше"],
    "byd": ["BYD", "Бид", "БИД"],
    "бид": ["BYD", "Бид", "БИД"],
    "li": ["Li", "Li Auto", "Ли", "Лисян"],
    "ли": ["Li", "Li Auto", "Ли", "Лисян"],
    "bugatti": ["Bugatti", "Бугатти"],
    "бугатти": ["Bugatti", "Бугатти"],
    "lotus": ["Lotus", "Лотус"],
    "лотус": ["Lotus", "Лотус"],
}

MODEL_SYNONYMS: dict[str, list[str]] = {
    "vesta": ["Веста", "Vesta"],
    "веста": ["Веста", "Vesta"],
    "granta": ["Гранта", "Granta"],
    "гранта": ["Гранта", "Granta"],
    "kalina": ["Калина", "Kalina"],
    "калина": ["Калина", "Kalina"],
    "priora": ["Приора", "Priora"],
    "приора": ["Приора", "Priora"],
    "largus": ["Ларгус", "Largus"],
    "ларгус": ["Ларгус", "Largus"],
    "niva": ["Нива", "Niva", "4x4"],
    "нива": ["Нива", "Niva", "4x4"],
    "samara": ["Самара", "Samara"],
    "самара": ["Самара", "Samara"],
    "xray": ["Х-рей", "X-Ray", "Xray", "XRAY"],
    "х-рей": ["Х-рей", "X-Ray", "Xray", "XRAY"],
    "хрей": ["Х-рей", "X-Ray", "Xray", "XRAY"],
    "solaris": ["Solaris", "Солярис"],
    "солярис": ["Solaris", "Солярис"],
    "rio": ["Rio", "Рио"],
    "рио": ["Rio", "Рио"],
    "focus": ["Focus", "Фокус"],
    "фокус": ["Focus", "Фокус"],
    "polo": ["Polo", "Поло"],
    "поло": ["Polo", "Поло"],
    "camry": ["Camry", "Камри"],
    "камри": ["Camry", "Камри"],
    "corolla": ["Corolla", "Королла"],
    "королла": ["Corolla", "Королла"],
    "logan": ["Logan", "Логан"],
    "логан": ["Logan", "Логан"],
    "duster": ["Duster", "Дастер"],
    "дастер": ["Duster", "Дастер"],
    "sandero": ["Sandero", "Сандеро"],
    "сандеро": ["Sandero", "Сандеро"],
    "creta": ["Creta", "Крета"],
    "крета": ["Creta", "Крета"],
    "kaptur": ["Kaptur", "Каптюр"],
    "каптюр": ["Kaptur", "Каптюр"],
    "tiguan": ["Tiguan", "Тигуан"],
    "тигуан": ["Tiguan", "Тигуан"],
    "rav4": ["RAV4", "Рав4", "Рав 4", "Rav4"],
    "рав4": ["RAV4", "Рав4", "Рав 4", "Rav4"],
    "outlander": ["Outlander", "Аутлендер"],
    "аутлендер": ["Outlander", "Аутлендер"],
    "sportage": ["Sportage", "Спортейдж", "Спортаж"],
    "спортейдж": ["Sportage", "Спортейдж", "Спортаж"],
    "octavia": ["Octavia", "Октавия"],
    "октавия": ["Octavia", "Октавия"],
    "rapid": ["Rapid", "Рапид"],
    "рапид": ["Rapid", "Рапид"],
    "civic": ["Civic", "Цивик", "Сивик"],
    "цивик": ["Civic", "Цивик", "Сивик"],
    "сивик": ["Civic", "Цивик", "Сивик"],
    "mondeo": ["Mondeo", "Мондео"],
    "мондео": ["Mondeo", "Мондео"],
    "qashqai": ["Qashqai", "Кашкай"],
    "кашкай": ["Qashqai", "Кашкай"],
    "x-trail": ["X-Trail", "Х-Трейл", "Икстрейл"],
    "х-трейл": ["X-Trail", "Х-Трейл", "Икстрейл"],
    "икстрейл": ["X-Trail", "Х-Трейл", "Икстрейл"],
    "lancer": ["Lancer", "Лансер"],
    "лансер": ["Lancer", "Лансер"],
    "jolion": ["Jolion", "Джолион"],
    "джолион": ["Jolion", "Джолион"],
    "coolray": ["Coolray", "Кулрей"],
    "кулрей": ["Coolray", "Кулрей"],
    "tiggo": ["Tiggo", "Тигго"],
    "тигго": ["Tiggo", "Тигго"],
    "senat": ["Senat", "Сенат"],
    "сенат": ["Senat", "Сенат"],
    "tucson": ["Tucson", "Туссан", "Туксон"],
    "туссан": ["Tucson", "Туссан", "Туксон"],
    "santa fe": ["Santa Fe", "Санта Фе"],
    "санта фе": ["Santa Fe", "Санта Фе"],
    "ceed": ["Ceed", "Сид"],
    "сид": ["Ceed", "Сид"],
    "optima": ["Optima", "Оптима"],
    "оптима": ["Optima", "Оптима"],
    "k5": ["K5", "К5"],
    "к5": ["K5", "К5"],
    "sorento": ["Sorento", "Соренто"],
    "соренто": ["Sorento", "Соренто"],
    "golf": ["Golf", "Гольф"],
    "гольф": ["Golf", "Гольф"],
    "passat": ["Passat", "Пассат"],
    "пассат": ["Passat", "Пассат"],
    "touareg": ["Touareg", "Туарег"],
    "туарег": ["Touareg", "Туарег"],
    "kodiaq": ["Kodiaq", "Кодиак"],
    "кодиак": ["Kodiaq", "Кодиак"],
    "superb": ["Superb", "Суперб"],
    "суперб": ["Superb", "Суперб"],
    "arkana": ["Arkana", "Аркана"],
    "аркана": ["Arkana", "Аркана"],
    "pajero": ["Pajero", "Паджеро"],
    "паджеро": ["Pajero", "Паджеро"],
    "forester": ["Forester", "Форестер"],
    "форестер": ["Forester", "Форестер"],
    "accord": ["Accord", "Аккорд"],
    "аккорд": ["Accord", "Аккорд"],
    "cr-v": ["CR-V", "ЦР-В", "СРВ"],
    "цр-в": ["CR-V", "ЦР-В", "СРВ"],
}


def _prefix_range(prefix: str) -> tuple[str, str]:
    """Compute [start, end) range bounds for indexed SQLite B-tree search."""
    if not prefix:
        return "", ""
    start = prefix
    end = prefix[:-1] + chr(ord(prefix[-1]) + 1)
    return start, end


class AnalogSelector:
    """Service for automated retrieval and preparation of market analogs from SQLite databases."""

    DEFAULT_SALES_DB: Path = sales_db_path()
    FULL_CARS_DB: Path = cars_db_path()

    @classmethod
    def get_default_db(cls) -> Path:
        """Preferred primary database for analogs lookup (cars.db when available, else sales.db)."""
        if cls.FULL_CARS_DB.exists():
            return cls.FULL_CARS_DB
        return cls.DEFAULT_SALES_DB

    @classmethod
    def find_analogs(
        cls,
        mark: str,
        model: str,
        year: int | None = None,
        valuation_date: str | None = None,
        target_age: float | None = None,
        target_mileage: float | None = None,
        db_path: Path | None = None,
        limit: int = 10,
        min_required: int = 3,
        allow_fallback: bool = True,
    ) -> list[dict[str, Any]]:
        """Find matching analogs for a given vehicle from database.

        Uses cars.db as primary when available. If fewer than min_required analogs
        are found, and allow_fallback is True, checks the alternative database.
        """
        target_db = db_path or cls.get_default_db()
        analogs: list[dict[str, Any]] = []

        if target_db.exists():
            analogs = cls._query_db(
                db_path=target_db,
                mark=mark,
                model=model,
                year=year,
                valuation_date=valuation_date,
                target_age=target_age,
                target_mileage=target_mileage,
                limit=limit,
                min_required=min_required,
            )

        # Fallback to secondary DB if primary DB yielded fewer than min_required
        if len(analogs) < min_required and allow_fallback:
            fallback_db = (
                cls.FULL_CARS_DB
                if target_db != cls.FULL_CARS_DB and cls.FULL_CARS_DB.exists()
                else (
                    cls.DEFAULT_SALES_DB
                    if target_db != cls.DEFAULT_SALES_DB and cls.DEFAULT_SALES_DB.exists()
                    else None
                )
            )
            if fallback_db is not None:
                fallback_analogs = cls._query_db(
                    db_path=fallback_db,
                    mark=mark,
                    model=model,
                    year=year,
                    valuation_date=valuation_date,
                    target_age=target_age,
                    target_mileage=target_mileage,
                    limit=limit,
                    min_required=min_required,
                )
                if len(fallback_analogs) >= len(analogs):
                    analogs = fallback_analogs

        return analogs

    @classmethod
    def _query_db(
        cls,
        db_path: Path,
        mark: str,
        model: str,
        year: int | None,
        valuation_date: str | None,
        target_age: float | None,
        target_mileage: float | None,
        limit: int,
        min_required: int,
    ) -> list[dict[str, Any]]:
        clean_mark = mark.strip()
        clean_model = model.strip()
        if not clean_mark and not clean_model:
            return []

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        try:
            # 1. Determine table name
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            if not tables:
                return []
            table_name = (
                "cars" if "cars" in tables else ("sales" if "sales" in tables else tables[0])
            )

            # 2. Get columns
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            col_info = cursor.fetchall()
            cols = {col[1].lower(): col[1] for col in col_info}

            col_name = (
                cols.get("название_машины") or cols.get("name") or cols.get("марка_модель")
            )
            col_year = cols.get("год") or cols.get("year")
            col_price = cols.get("цена") or cols.get("price")
            col_mileage = cols.get("пробег") or cols.get("mileage")
            col_city = cols.get("город") or cols.get("city")
            col_region = cols.get("регион") or cols.get("region")

            if not col_name or not col_price:
                return []

            # 3. Build search variants for mark & model
            search_pairs = cls._generate_search_pairs(clean_mark, clean_model)

            # 4. Filter candidate pairs that actually exist in the table (fast range B-tree search)
            valid_pairs: list[tuple[str, str]] = []
            for s_mark, s_model in search_pairs:
                if s_mark:
                    try:
                        start, end = _prefix_range(s_mark)
                        cursor.execute(
                            f'SELECT 1 FROM "{table_name}" WHERE "{col_name}" >= ? AND "{col_name}" < ? LIMIT 1',
                            (start, end),
                        )
                        if cursor.fetchone():
                            valid_pairs.append((s_mark, s_model))
                    except sqlite3.Error:
                        valid_pairs.append((s_mark, s_model))
                elif s_model:
                    valid_pairs.append((s_mark, s_model))

            if not valid_pairs:
                return []

            # 5. Multi-tier indexed search: strict year tolerance -> relaxed year tolerance
            year_tolerances: list[int | None] = [2, 4, None] if year is not None else [None]
            raw_rows: list[dict[str, Any]] = []

            for tol in year_tolerances:
                for s_mark, s_model in valid_pairs:
                    rows = cls._execute_search_fast(
                        cursor=cursor,
                        table=table_name,
                        col_name=col_name,
                        col_year=col_year,
                        mark_term=s_mark,
                        model_term=s_model,
                        year=year,
                        year_tol=tol,
                        limit=limit * 2,
                    )
                    if rows:
                        existing_keys = {
                            (
                                r.get(col_name),
                                r.get(col_year) if col_year else None,
                                r.get(col_price),
                            )
                            for r in raw_rows
                        }
                        for r in rows:
                            key = (
                                r.get(col_name),
                                r.get(col_year) if col_year else None,
                                r.get(col_price),
                            )
                            if key not in existing_keys:
                                raw_rows.append(r)
                                existing_keys.add(key)
                    if len(raw_rows) >= min_required:
                        break
                if len(raw_rows) >= min_required:
                    break

            if year is not None and col_year and raw_rows:
                raw_rows.sort(
                    key=lambda r: abs((int(r[col_year]) if r.get(col_year) is not None else year) - year)
                )

            # 6. Transform raw rows into Analog objects with correct temporal scale
            analogs: list[dict[str, Any]] = []
            now_year = datetime.now(UTC).year
            val_year = now_year
            if valuation_date:
                try:
                    val_year = int(valuation_date[:4])
                except ValueError:
                    pass

            for r in raw_rows[:limit]:
                raw_name = str(r.get(col_name) or f"{mark} {model}")
                raw_price = r.get(col_price)
                if raw_price is None:
                    continue
                try:
                    price = float(str(raw_price).replace(" ", "").replace(",", "."))
                except ValueError:
                    continue
                if price <= 0:
                    continue

                car_year = (
                    int(r[col_year])
                    if col_year and r.get(col_year) is not None
                    else (year or val_year)
                )

                age_years = cls._calculate_age(
                    car_year=car_year,
                    val_year=val_year,
                    target_age=target_age,
                    target_year=year,
                )

                raw_mileage = r.get(col_mileage) if col_mileage else None
                mileage = cls._calculate_mileage(
                    raw_mileage=raw_mileage,
                    age_years=age_years,
                    target_mileage=target_mileage,
                    target_age=target_age,
                )

                city = ""
                if col_city and r.get(col_city):
                    city = str(r[col_city]).strip()
                elif col_region and r.get(col_region):
                    city = str(r[col_region]).strip()

                loc_info = f"{city}" if city else "РФ"
                display_name = f"{raw_name} ({loc_info}, {car_year} г.в.)"

                analogs.append({
                    "name": display_name,
                    "price": price,
                    "age_years": age_years,
                    "mileage_km": mileage,
                    "discount": None,
                    "deflator": 1.0,
                    "city": city,
                    "db_source": db_path.name,
                })

            return analogs

        finally:
            conn.close()

    @classmethod
    def _generate_search_pairs(cls, mark: str, model: str) -> list[tuple[str, str]]:
        """Generate mark/model variants with synonyms and casing normalization."""
        clean_mark = mark.strip()
        clean_model = model.strip()

        # If model repeats mark (e.g. mark="Лада", model="Лада Веста"), strip prefix only if remainder is not empty
        if (
            clean_mark
            and clean_model.lower().startswith(clean_mark.lower())
            and len(clean_model) > len(clean_mark)
        ):
            clean_model = clean_model[len(clean_mark):].strip()

        mark_lower = clean_mark.lower()
        mark_variants: list[str] = []
        for candidate in [clean_mark, clean_mark.title(), clean_mark.capitalize(), clean_mark.upper()]:
            if candidate and candidate not in mark_variants:
                mark_variants.append(candidate)

        for syn in BRAND_SYNONYMS.get(mark_lower, []):
            for candidate in [syn, syn.title(), syn.capitalize(), syn.upper()]:
                if candidate and candidate not in mark_variants:
                    mark_variants.append(candidate)

        model_lower = clean_model.lower()
        model_variants: list[str] = []
        for candidate in [clean_model, clean_model.title(), clean_model.capitalize(), clean_model.upper()]:
            if candidate and candidate not in model_variants:
                model_variants.append(candidate)

        for syn in MODEL_SYNONYMS.get(model_lower, []):
            for candidate in [syn, syn.title(), syn.capitalize(), syn.upper()]:
                if candidate and candidate not in model_variants:
                    model_variants.append(candidate)

        if not mark_variants:
            mark_variants = [""]
        if not model_variants:
            model_variants = [""]

        pairs: list[tuple[str, str]] = []
        for m in mark_variants:
            for md in model_variants:
                if (m, md) not in pairs:
                    pairs.append((m, md))

        return pairs

    @classmethod
    def _execute_search_fast(
        cls,
        cursor: sqlite3.Cursor,
        table: str,
        col_name: str,
        col_year: str | None,
        mark_term: str,
        model_term: str,
        year: int | None,
        year_tol: int | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Execute indexed B-tree search using range prefix matching for maximum SQLite performance."""
        conditions: list[str] = []
        params: list[Any] = []

        if mark_term and model_term:
            prefix = f"{mark_term} {model_term}".strip()
            start, end = _prefix_range(prefix)
            conditions.append(f'"{col_name}" >= ? AND "{col_name}" < ?')
            params.extend([start, end])
        elif mark_term:
            start, end = _prefix_range(mark_term.strip())
            conditions.append(f'"{col_name}" >= ? AND "{col_name}" < ?')
            params.extend([start, end])
        elif model_term:
            conditions.append(f'"{col_name}" LIKE ?')
            params.append(f"%{model_term}%")

        if col_year and year is not None and year_tol is not None:
            conditions.append(f'"{col_year}" BETWEEN ? AND ?')
            params.extend([year - year_tol, year + year_tol])

        where_str = " AND ".join(conditions) if conditions else "1=1"
        query = f'SELECT * FROM "{table}" WHERE {where_str} LIMIT ?'
        params.append(limit)

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows:
                return []
            col_names = [d[0] for d in cursor.description]
            return [dict(zip(col_names, r)) for r in rows]
        except (sqlite3.Error, ValueError):
            return []

    @classmethod
    def _calculate_age(
        cls,
        car_year: int,
        val_year: int,
        target_age: float | None = None,
        target_year: int | None = None,
    ) -> float:
        if target_age is not None and target_year is not None:
            age = float(target_age) + float(target_year - car_year)
            return max(1.0, round(age, 1))

        if val_year and car_year:
            age = float(val_year - car_year)
            return max(1.0, round(age, 1))

        if target_age is not None:
            return max(1.0, round(target_age, 1))

        return 1.0

    @classmethod
    def _calculate_mileage(
        cls,
        raw_mileage: Any,
        age_years: float,
        target_mileage: float | None = None,
        target_age: float | None = None,
    ) -> float:
        if raw_mileage is not None:
            try:
                m = float(str(raw_mileage).replace(" ", "").replace(",", "."))
                if m >= 3000.0 * age_years:
                    return round(m, 1)
            except ValueError:
                pass

        if target_mileage and target_age and target_age > 0:
            annual_rate = target_mileage / target_age
            return round(max(1000.0, age_years * annual_rate), 1)

        return round(max(1000.0, age_years * 15000.0), 1)
