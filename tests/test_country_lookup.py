"""Страна-производитель -> категория Минюста (эталоны из дела 4440/25э)."""

import pytest

from app.services.valuation.constants import detect_vehicle_category
from db.country_lookup import car_origin, category_from_country, normalize_vin

GAC_M8_VIN = "LMGMU1G81P1168719"  # эталон GAC M8 из 4440.25э
SOLLERS_VIN = "ЕВЕ66S209P0005012"  # эталон Sollers Atlant, VIN в кириллице
ASIAN = "Легковые автомобили азиатские (кроме Японии)"


def test_vin_beats_brand():
    country, _matched, source = car_origin(vin=GAC_M8_VIN, brand="vw")
    assert source == "vin"
    assert country == "Китай"


def test_brand_fallback_when_no_vin():
    country, _catalog, source = car_origin(vin="", brand="GAC")
    assert source == "brand"
    assert country == "Китай"


def test_gac_m8_is_asian_by_vin():
    assert detect_vehicle_category("", vin=GAC_M8_VIN) == ASIAN


def test_gac_m8_is_asian_by_brand():
    assert detect_vehicle_category("GAC") == ASIAN


def test_sollers_atlant_is_domestic_by_vin_cyrillic():
    assert detect_vehicle_category("", vin=SOLLERS_VIN) == "Легковые автомобили отечественные"


def test_sollers_atlant_vin_resolves_russia_via_wmi():
    country, matched, source = car_origin(vin=SOLLERS_VIN, brand="sollers")
    assert source == "vin"
    assert country == "Россия"
    assert matched is not None and "Соллерс-Елабуга" in matched


def test_sollers_atlant_is_domestic_by_brand():
    assert detect_vehicle_category("Sollers") == "Легковые автомобили отечественные"


@pytest.mark.parametrize(
    ("vin", "expected"),
    [
        ("WBA5A5C55FD520435", "Легковые автомобили европейского производства"),  # BMW, DE
        ("JTNKT32E90J123456", "Легковые автомобили производства Японии"),  # Toyota, JP
        ("1FA6P8K1GL5522044", "Легковые автомобили американского производства"),  # Ford, US
    ],
)
def test_categories_by_vin_prefixes(vin: str, expected: str) -> None:
    assert detect_vehicle_category("", vin=vin) == expected


@pytest.mark.parametrize(
    ("brand", "expected"),
    [
        ("Лада", "Легковые автомобили отечественные"),
        ("Haval", ASIAN),
        ("Ford", "Легковые автомобили американского производства"),
        ("Volvo", "Легковые автомобили европейского производства"),
    ],
)
def test_categories_by_brand(brand: str, expected: str) -> None:
    assert detect_vehicle_category(brand) == expected


def test_normalize_vin_replaces_cyrillic_lookalikes():
    assert normalize_vin("ЕВЕ66S209Р0005012") == "EBE66S209P0005012"


def test_unknown_country_keeps_legacy_fallback():
    # Марки нет в БД -> срабатывают старые списки/первые символы VIN.
    assert detect_vehicle_category("zzzunknown") == "Легковые автомобили отечественные"


def test_category_mapping_covers_generated_countries():
    for country in ("Россия", "Япония", "Китай", "Германия", "США"):
        assert category_from_country(country)
