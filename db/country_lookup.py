"""Страна-производитель авто: таблицы + запросы.

Договорённость по задаче 4440/25э:
1. Если известен VIN — страна всегда определяется по VIN (страна сборки:
   таблица vin_country, приоритет у WMI-кода из первых 3 символов).
2. Если VIN нет — по марке (страна компании-производителя, таблица brand_country).
3. Найденная страна переводится в категорию интенсивности износа
   по Методике Минюста (см. CATEGORY_BY_COUNTRY ниже).

Данные: db/country_data.py (единственный источник, правится вручную).
"""

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column

from db.connection import Base, SessionLocal
from db.country_data import BRAND_COUNTRY, VIN_RANGES, WMI

# Порядок символов VIN: A..Z без I, O, Q, затем 1..9, затем 0 (ISO 3780).
_VIN_ALPHABET = "ABCDEFGHJKLMNPRSTUVWXYZ1234567890"

# Живые кириллические двойники в VIN из документов (ПТС/СТС пишут от руки).
_CYRILLIC_TO_LATIN = {
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K",
    "М": "M", "О": "O", "Р": "P", "Т": "T", "У": "Y", "Х": "X",
}


def normalize_vin(raw: str) -> str:
    """Uppercase + замена кириллических двойников на латиницу."""
    vin = (raw or "").strip().upper().replace(" ", "").replace("-", "")
    return "".join(_CYRILLIC_TO_LATIN.get(ch, ch) for ch in vin)


class VinCountry(Base):
    """Определение страны по VIN.

    kind="wmi" — первые 3 символа (код WMI, страна завода);
    kind="range" — диапазон первых 2 символов (ISO 3780).
    """

    __tablename__ = "vin_country"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    code_from: Mapped[str] = mapped_column(String(3), nullable=False)
    code_to: Mapped[str] = mapped_column(String(3), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    iso: Mapped[str | None] = mapped_column(String(2), nullable=True)


class BrandCountry(Base):
    """Страна компании-производителя по марке (алиас)."""

    __tablename__ = "brand_country"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alias: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)


# Страна -> категория ТС по «Методике Минюста» (ключ в WEAR_COEFFICIENTS).
# Категории: отечественные 0,070/0,0035; Япония 0,045/0,0020;
# азиатские кроме Японии 0,065/0,0032; европейские 0,050/0,0025;
# американские 0,055/0,0030 (см. расчёты 4440.25э: GAC M8 и Sollers Atlant).
CATEGORY_BY_COUNTRY: dict[str, str] = {
    **dict.fromkeys(
        ("Россия", "Беларусь", "Казахстан", "Узбекистан"),
        "Легковые автомобили отечественные",
    ),
    **dict.fromkeys(
        ("Япония",),
        "Легковые автомобили производства Японии",
    ),
    **dict.fromkeys(
        (
            "Южная Корея", "Китай", "Индия", "Индонезия", "Таиланд", "Мьянма",
            "Иран", "Пакистан", "Турция", "Филиппины", "Сингапур", "Малайзия",
            "ОАЭ", "Тайвань", "Вьетнам", "Саудовская Аравия", "Шри-Ланка",
            "Израиль",
        ),
        "Легковые автомобили азиатские (кроме Японии)",
    ),
    **dict.fromkeys(
        (
            "Великобритания", "Германия", "Польша", "Латвия", "Швейцария",
            "Чехия", "Венгрия", "Португалия", "Дания", "Ирландия", "Румыния",
            "Словакия", "Австрия", "Франция", "Испания", "Сербия", "Хорватия",
            "Эстония", "Болгария", "Греция", "Нидерланды", "Люксембург",
            "Бельгия", "Финляндия", "Мальта", "Швеция", "Норвегия", "Италия",
            "Словения", "Литва",
        ),
        "Легковые автомобили европейского производства",
    ),
    **dict.fromkeys(
        (
            "США", "Канада", "Мексика", "Коста-Рика", "Каймановы острова",
            "Бразилия", "Аргентина", "Чили", "Эквадор", "Перу", "Венесуэла",
            "Колумбия", "Парагвай", "Уругвай", "Тринидад и Тобаго",
        ),
        "Легковые автомобили американского производства",
    ),
}


def _seed_country_tables() -> None:
    """Resync vin_country and brand_country from country_data.

    Пересобираем всегда: правки country_data.py подхватываются без удаления app.db
    (таблицы справочные, случайных данных в них нет).
    """
    with SessionLocal() as session:
        session.query(VinCountry).delete()
        session.query(BrandCountry).delete()
        rows: list[VinCountry] = []
        for wmi_code, brand, country in WMI:
            rows.append(
                VinCountry(kind="wmi", code_from=wmi_code[:2], code_to=wmi_code[2:],
                           country=country, brand=brand, iso=None)
            )
        for _first, _last, country, iso in VIN_RANGES:
            rows.append(
                VinCountry(kind="range", code_from=_first, code_to=_last,
                           country=country, brand=None, iso=iso)
            )
        session.add_all(rows)
        session.add_all(
            BrandCountry(alias=alias, brand=brand, country=country)
            for alias, brand, country in BRAND_COUNTRY
        )
        session.commit()


def ensure_country_db() -> None:
    """Called from create_db(): create tables if absent and resync справочник."""
    Base.metadata.create_all(bind=_engine())
    _seed_country_tables()


def _engine():  # noqa: ANN202 - tiny local helper
    from db.connection import engine

    return engine


def _element(prefix: str) -> int:
    """Первые 2 символа как число по алфавиту ISO 3780."""
    (c1, c2) = (prefix[0], prefix[1])
    return _VIN_ALPHABET.index(c1) * len(_VIN_ALPHABET) + _VIN_ALPHABET.index(c2)


def country_by_vin(vin: str) -> tuple[str | None, str | None]:
    """Страна сборки по VIN. Возвращает (страна, найденная марка или None)."""
    vin = normalize_vin(vin)
    if len(vin) < 2:
        return None, None
    with SessionLocal() as session:
        # 1. Точное совпадение WMI (3 символа) имеет приоритет.
        if len(vin) >= 3:
            wmi3 = vin[:3]
            row = session.execute(
                select(VinCountry).where(
                    VinCountry.kind == "wmi",
                    VinCountry.code_from == wmi3[:2],
                    VinCountry.code_to == wmi3[2:],
                )
            ).scalars().first()
            if row is not None:
                return row.country, row.brand
        # 2. Диапазон первых двух символов.
        v = _element(vin)
        rows = session.execute(
            select(VinCountry).where(VinCountry.kind == "range")
        ).scalars().all()
        for row in rows:
            if _element(row.code_from) <= v <= _element(row.code_to):
                return row.country, row.brand
    return None, None


def country_by_brand(brand: str) -> tuple[str | None, str | None]:
    """Страна компании по марке. Возвращает (страна, каноничное имя бренда)."""
    alias = (brand or "").strip().lower()
    if not alias:
        return None, None
    with SessionLocal() as session:
        row = session.execute(
            select(BrandCountry).where(BrandCountry.alias == alias)
        ).scalars().first()
        if row is None:
            return None, None
        return row.country, row.brand


def car_origin(
    vin: str | None = None, brand: str | None = None
) -> tuple[str | None, str | None, str | None]:
    """Страна производства по задаче: VIN в приоритете, иначе марка.

    Returns:
        (country, matched_brand_or_canonical, source) — source = "vin" | "brand" | None
    """
    vin_country, vin_brand = country_by_vin(vin or "")
    if vin_country:
        return vin_country, vin_brand, "vin"
    brand_country, canonical = country_by_brand(brand or "")
    if brand_country:
        return brand_country, canonical, "brand"
    return None, None, None


def category_from_country(country: str | None) -> str | None:
    """Категория Минюста по стране, None если страна не в таблице."""
    if country is None:
        return None
    return CATEGORY_BY_COUNTRY.get(country)
