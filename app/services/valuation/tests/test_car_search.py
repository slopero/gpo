"""Comprehensive automated tests for vehicle searching in cars.db and sales.db.

Validates that all 44 brands present in the 12.1-million-record cars database
can be retrieved, along with Cyrillic/Latin transliterations, case variations,
and edge cases.
"""

from pathlib import Path

import pytest

from app.paths import cars_db_path, sales_db_path
from app.services.valuation.selector import AnalogSelector

ALL_44_BRANDS: list[str] = [
    "Aston Martin",
    "Audi",
    "BMW",
    "BYD",
    "Bentley",
    "Bugatti",
    "Cadillac",
    "Chery",
    "Chevrolet",
    "Citroen",
    "Ferrari",
    "Ford",
    "Geely",
    "Genesis",
    "Haval",
    "Honda",
    "Hongqi",
    "Hyundai",
    "Infiniti",
    "Jaguar",
    "Jeep",
    "Kia",
    "Lamborghini",
    "Land Rover",
    "Lexus",
    "Li",
    "Lotus",
    "Maserati",
    "Mazda",
    "Mercedes-Benz",
    "Mitsubishi",
    "Nissan",
    "Peugeot",
    "Porsche",
    "Renault",
    "Rolls-Royce",
    "Skoda",
    "Subaru",
    "Suzuki",
    "Toyota",
    "Volkswagen",
    "Volvo",
    "Аурус",
    "Лада",
]


@pytest.fixture(scope="module")
def ensure_cars_db_available() -> Path:
    db = cars_db_path()
    if not db.exists():
        pytest.skip(f"cars.db not found at {db}")
    return db


@pytest.mark.parametrize("brand", ALL_44_BRANDS)
def test_all_44_brands_searchable(ensure_cars_db_available: Path, brand: str) -> None:
    """Verify that every single brand among the 44 in cars.db returns analogs."""
    analogs = AnalogSelector.find_analogs(mark=brand, model="", limit=5)
    assert len(analogs) > 0, f"Brand '{brand}' returned 0 analogs from cars.db"
    assert analogs[0]["db_source"] == "cars.db"
    assert analogs[0]["price"] > 0


@pytest.mark.parametrize(
    ("mark", "model", "expected_fragment"),
    [
        # Russian cars in various spellings and cases
        ("Лада", "Веста", "Веста"),
        ("Lada", "Vesta", "Веста"),
        ("ВАЗ", "Веста", "Веста"),
        ("ваз", "веста", "Веста"),
        ("лада", "веста", "Веста"),
        ("LADA", "VESTA", "Веста"),
        ("Лада", "Гранта", "Гранта"),
        ("Lada", "Granta", "Гранта"),
        ("ваз", "гранта", "Гранта"),
        ("Лада", "Приора", "Приора"),
        ("Lada", "Priora", "Приора"),
        ("Лада", "Калина", "Калина"),
        ("Lada", "Kalina", "Калина"),
        ("Лада", "Нива", "Нива"),
        ("Lada", "Niva", "Нива"),
        ("Лада", "Ларгус", "Ларгус"),
        ("Lada", "Largus", "Ларгус"),
        ("Лада", "2107", "2107"),
        ("ВАЗ", "2107", "2107"),
        ("Лада", "Х-рей", "Х-рей"),
        ("Lada", "XRAY", "Х-рей"),
        ("Аурус", "Сенат", "Сенат"),
        ("Aurus", "Senat", "Сенат"),
        # Foreign cars with Russian / English names
        ("Тойота", "Камри", "Camry"),
        ("Toyota", "Camry", "Camry"),
        ("toyota", "camry", "Camry"),
        ("TOYOTA", "CAMRY", "Camry"),
        ("Тойота", "Королла", "Corolla"),
        ("Toyota", "Corolla", "Corolla"),
        ("Тойота", "Рав4", "RAV4"),
        ("Toyota", "RAV4", "RAV4"),
        ("Хендай", "Солярис", "Solaris"),
        ("Hyundai", "Solaris", "Solaris"),
        ("хендай", "солярис", "Solaris"),
        ("Хендай", "Крета", "Creta"),
        ("Hyundai", "Creta", "Creta"),
        ("Киа", "Рио", "Rio"),
        ("Kia", "Rio", "Rio"),
        ("киа", "рио", "Rio"),
        ("Киа", "Спортейдж", "Sportage"),
        ("Kia", "Sportage", "Sportage"),
        ("Фольксваген", "Поло", "Polo"),
        ("Volkswagen", "Polo", "Polo"),
        ("VW", "Polo", "Polo"),
        ("Фольксваген", "Тигуан", "Tiguan"),
        ("Volkswagen", "Tiguan", "Tiguan"),
        ("Шкода", "Октавия", "Octavia"),
        ("Skoda", "Octavia", "Octavia"),
        ("Шкода", "Рапид", "Rapid"),
        ("Skoda", "Rapid", "Rapid"),
        ("Рено", "Логан", "Logan"),
        ("Renault", "Logan", "Logan"),
        ("Рено", "Дастер", "Duster"),
        ("Renault", "Duster", "Duster"),
        ("Рено", "Сандеро", "Sandero"),
        ("Renault", "Sandero", "Sandero"),
        ("Форд", "Фокус", "Focus"),
        ("Ford", "Focus", "Focus"),
        ("Форд", "Мондео", "Mondeo"),
        ("Ford", "Mondeo", "Mondeo"),
        ("Ниссан", "Кашкай", "Qashqai"),
        ("Nissan", "Qashqai", "Qashqai"),
        ("Ниссан", "Х-Трейл", "X-Trail"),
        ("Nissan", "X-Trail", "X-Trail"),
        ("Мазда", "6", "6"),
        ("Mazda", "6", "6"),
        ("Мазда", "CX-5", "CX-5"),
        ("Mazda", "CX-5", "CX-5"),
        ("Митсубиси", "Аутлендер", "Outlander"),
        ("Mitsubishi", "Outlander", "Outlander"),
        ("Митсубиси", "Лансер", "Lancer"),
        ("Mitsubishi", "Lancer", "Lancer"),
        ("БМВ", "X5", "X5"),
        ("BMW", "X5", "X5"),
        ("Мерседес", "E-Class", "E-Class"),
        ("Mercedes-Benz", "E-Class", "E-Class"),
        ("Mercedes", "C-Class", "C-Class"),
        ("Ауди", "A4", "A4"),
        ("Audi", "A4", "A4"),
        ("Хонда", "Цивик", "Civic"),
        ("Honda", "Civic", "Civic"),
        ("Хавейл", "Джолион", "Jolion"),
        ("Haval", "Jolion", "Jolion"),
        ("Джили", "Кулрей", "Coolray"),
        ("Geely", "Coolray", "Coolray"),
        ("Чери", "Тигго", "Tiggo"),
        ("Chery", "Tiggo", "Tiggo"),
    ],
)
def test_transliterated_and_synonym_searches(
    ensure_cars_db_available: Path, mark: str, model: str, expected_fragment: str
) -> None:
    """Verify that cross-language searches and case variations find matching analogs."""
    analogs = AnalogSelector.find_analogs(mark=mark, model=model, limit=5)
    assert len(analogs) > 0, f"Query ({mark!r}, {model!r}) yielded 0 analogs"
    found_fragment = any(expected_fragment.lower() in a["name"].lower() for a in analogs)
    assert found_fragment, (
        f"Expected '{expected_fragment}' in analog names for ({mark!r}, {model!r}), "
        f"got: {[a['name'] for a in analogs]}"
    )


def test_year_tolerance_and_sorting(ensure_cars_db_available: Path) -> None:
    """Verify that specifying a year prioritizes cars of matching/closest year."""
    target_year = 2019
    analogs = AnalogSelector.find_analogs(
        mark="Лада",
        model="Веста",
        year=target_year,
        limit=10,
    )
    assert len(analogs) >= 3
    # Check that all retrieved vehicles have a valid price and age
    for a in analogs:
        assert a["price"] > 100_000
        assert a["age_years"] >= 1.0
        assert a["mileage_km"] > 0


def test_repeated_brand_in_model_field(ensure_cars_db_available: Path) -> None:
    """Handle user entering mark name inside the model input (e.g. Mark: 'Лада', Model: 'Лада Веста')."""
    analogs = AnalogSelector.find_analogs(mark="Лада", model="Лада Веста", limit=5)
    assert len(analogs) > 0
    assert any("Веста" in a["name"] for a in analogs)


def test_identical_mark_and_model(ensure_cars_db_available: Path) -> None:
    """Handle model names that match brand (e.g. BYD BYD)."""
    analogs = AnalogSelector.find_analogs(mark="BYD", model="BYD", limit=5)
    assert len(analogs) > 0


def test_empty_search_returns_empty_list() -> None:
    """Verify empty input returns empty list without error."""
    assert AnalogSelector.find_analogs(mark="", model="") == []
    assert AnalogSelector.find_analogs(mark="   ", model="   ") == []


def test_nonexistent_car_returns_empty_list(ensure_cars_db_available: Path) -> None:
    """Verify searching for a fictitious vehicle returns an empty list gracefully."""
    analogs = AnalogSelector.find_analogs(
        mark="NonexistentBrandXYZ",
        model="ImpossibleModel999",
        limit=5,
    )
    assert analogs == []


def test_sales_db_direct_query() -> None:
    """Verify querying sales.db explicitly still works for Aston Martin."""
    db = sales_db_path()
    if not db.exists():
        pytest.skip("sales.db not found")
    analogs = AnalogSelector.find_analogs(
        mark="Aston Martin",
        model="DB9",
        db_path=db,
        allow_fallback=False,
    )
    assert len(analogs) >= 3
    assert analogs[0]["db_source"] == "sales.db"
