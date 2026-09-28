"""Constants and normative matrices for forensic vehicle valuation (SEC SK RF / Minyust RF)."""

from enum import StrEnum
from typing import Final

# Mathematical and statistical thresholds
E_BASE: Final[float] = 2.72
VARIATION_THRESHOLD: Final[float] = 0.30


class VehicleWearCategory(StrEnum):
    """Normative categories for physical wear intensity (Omega = a * T + b * L)."""

    DOMESTIC_PASSENGER = "DOMESTIC_PASSENGER"
    ASIAN_EXCEPT_JAPAN = "ASIAN_EXCEPT_JAPAN"
    EUROPEAN_PASSENGER = "EUROPEAN_PASSENGER"
    JAPANESE_PASSENGER = "JAPANESE_PASSENGER"
    AMERICAN_PASSENGER = "AMERICAN_PASSENGER"
    FOREIGN_TRUCK = "FOREIGN_TRUCK"
    DOMESTIC_FLATBED_TRUCK = "DOMESTIC_FLATBED_TRUCK"
    DOMESTIC_TRACTOR = "DOMESTIC_TRACTOR"
    DOMESTIC_DUMP_TRUCK = "DOMESTIC_DUMP_TRUCK"
    DOMESTIC_SPECIAL = "DOMESTIC_SPECIAL"
    DOMESTIC_BUS = "DOMESTIC_BUS"
    FOREIGN_BUS = "FOREIGN_BUS"


# Mapping from VehicleWearCategory to normative coefficients (a, b)
# a = coefficient of age (years), b = coefficient of mileage (thousand km)
WEAR_COEFFICIENTS: Final[dict[str, tuple[float, float]]] = {
    VehicleWearCategory.DOMESTIC_PASSENGER.value: (0.070, 0.0035),
    VehicleWearCategory.ASIAN_EXCEPT_JAPAN.value: (0.065, 0.0032),
    VehicleWearCategory.EUROPEAN_PASSENGER.value: (0.050, 0.0025),
    VehicleWearCategory.JAPANESE_PASSENGER.value: (0.045, 0.0020),
    VehicleWearCategory.AMERICAN_PASSENGER.value: (0.055, 0.0030),
    VehicleWearCategory.FOREIGN_TRUCK.value: (0.090, 0.0020),
    VehicleWearCategory.DOMESTIC_FLATBED_TRUCK.value: (0.100, 0.0030),
    VehicleWearCategory.DOMESTIC_TRACTOR.value: (0.090, 0.0020),
    VehicleWearCategory.DOMESTIC_DUMP_TRUCK.value: (0.150, 0.0025),
    VehicleWearCategory.DOMESTIC_SPECIAL.value: (0.140, 0.0020),
    VehicleWearCategory.DOMESTIC_BUS.value: (0.160, 0.0010),
    VehicleWearCategory.FOREIGN_BUS.value: (0.120, 0.0010),
    # Common Russian names mapping
    "Легковые автомобили отечественные": (0.070, 0.0035),
    "Легковые автомобили азиатские (кроме Японии)": (0.065, 0.0032),
    "Легковые автомобили европейского производства": (0.050, 0.0025),
    "Легковые автомобили производства Японии": (0.045, 0.0020),
    "Легковые автомобили американского производства": (0.055, 0.0030),
    "Грузовые автомобили зарубежного производства": (0.090, 0.0020),
    "Грузовые бортовые автомобили отечественные": (0.100, 0.0030),
    "Тягачи отечественные": (0.090, 0.0020),
    "Самосвалы отечественные": (0.150, 0.0025),
    "Специализированные отечественные": (0.140, 0.0020),
    "Автобусы отечественные": (0.160, 0.0010),
    "Автобусы зарубежного производства": (0.120, 0.0010),
}


class BargainingCategory(StrEnum):
    """Categories for bargaining discounts (Zhivaev M.V., 2024)."""

    DOMESTIC_VEHICLE = "DOMESTIC_VEHICLE"
    IMPORT_VEHICLE = "IMPORT_VEHICLE"
    DOMESTIC_TRUCK = "DOMESTIC_TRUCK"
    IMPORT_TRUCK = "IMPORT_TRUCK"
    SPECIAL_EQUIPMENT = "SPECIAL_EQUIPMENT"


# Average bargaining discount rates
BARGAINING_DISCOUNTS: Final[dict[str, float]] = {
    BargainingCategory.DOMESTIC_VEHICLE.value: 0.06,
    BargainingCategory.IMPORT_VEHICLE.value: 0.05,
    BargainingCategory.DOMESTIC_TRUCK.value: 0.08,
    BargainingCategory.IMPORT_TRUCK.value: 0.05,
    BargainingCategory.SPECIAL_EQUIPMENT.value: 0.06,
    # Direct mappings from wear category names for convenience
    VehicleWearCategory.DOMESTIC_PASSENGER.value: 0.06,
    VehicleWearCategory.ASIAN_EXCEPT_JAPAN.value: 0.05,
    VehicleWearCategory.EUROPEAN_PASSENGER.value: 0.05,
    VehicleWearCategory.JAPANESE_PASSENGER.value: 0.05,
    VehicleWearCategory.AMERICAN_PASSENGER.value: 0.05,
    VehicleWearCategory.FOREIGN_TRUCK.value: 0.05,
    VehicleWearCategory.DOMESTIC_FLATBED_TRUCK.value: 0.08,
    VehicleWearCategory.DOMESTIC_TRACTOR.value: 0.08,
    VehicleWearCategory.DOMESTIC_DUMP_TRUCK.value: 0.08,
    VehicleWearCategory.DOMESTIC_SPECIAL.value: 0.06,
    VehicleWearCategory.DOMESTIC_BUS.value: 0.08,
    VehicleWearCategory.FOREIGN_BUS.value: 0.05,
}

# Monthly Consumer Price Index (CPI) for non-food goods from Rosstat (2024-2025)
# Key: (Year, Month), Value: monthly chain index multiplier
ROSSTAT_CPI_NONFOOD: Final[dict[tuple[int, int], float]] = {
    (2024, 1): 1.0086,
    (2024, 2): 1.0068,
    (2024, 3): 1.0039,
    (2024, 4): 1.0050,
    (2024, 5): 1.0074,
    (2024, 6): 1.0064,
    (2024, 7): 1.0114,
    (2024, 8): 1.0020,
    (2024, 9): 1.0048,
    (2024, 10): 1.0075,
    (2024, 11): 1.0143,
    (2024, 12): 1.0132,
    (2025, 1): 1.0123,
    (2025, 2): 1.0081,
    (2025, 3): 1.0065,
    (2025, 4): 1.0040,
    (2025, 5): 1.0043,
    (2025, 6): 1.0020,
    (2025, 7): 1.0057,
    (2025, 8): 0.9960,
}


def detect_vehicle_category(
    brand: str,
    vin: str | None = None,
    type_ts: str | None = None,
) -> str:
    """Automatically detect normative vehicle wear category by manufacturer brand, VIN prefix, and type.

    Returns:
        Russian category name key for WEAR_COEFFICIENTS.
    """
    clean_brand = brand.strip().lower() if brand else ""
    clean_vin = vin.strip().upper() if vin else ""
    clean_type = type_ts.strip().lower() if type_ts else ""

    # 1. Check vehicle type specialized categories
    if "самосвал" in clean_type:
        return "Самосвалы отечественные"
    if "тягач" in clean_type:
        return "Тягачи отечественные"
    if "автобус" in clean_type:
        if clean_brand in ("паз", "лиаз", "нефаз", "кавз", "газель", "уаз"):
            return "Автобусы отечественные"
        return "Автобусы зарубежного производства"
    if "грузов" in clean_type:
        if clean_brand in ("камаз", "маз", "урал", "зил", "газ", "газель"):
            return "Грузовые бортовые автомобили отечественные"
        return "Грузовые автомобили зарубежного производства"

    # 2. Check brand manufacturer
    domestic_brands = {
        "lada", "лада", "ваз", "vaz", "газ", "gaz", "уаз", "uaz",
        "москвич", "moskvich", "moskvitch", "тагаз", "tagaz", "иж", "izh",
        "луаз", "sollers", "соллерс", "xcite", "volga", "волга", "камаз", "kamaz",
    }
    if clean_brand in domestic_brands:
        return "Легковые автомобили отечественные"

    japanese_brands = {
        "toyota", "тойота", "lexus", "лексус", "nissan", "ниссан", "infiniti", "инфинити",
        "honda", "хонда", "acura", "акура", "mazda", "мазда", "subaru", "субару",
        "mitsubishi", "митсубиси", "митсубиши", "suzuki", "сузуки", "daihatsu", "дайихатсу",
        "isuzu", "исузу", "mitsuoka",
    }
    if clean_brand in japanese_brands:
        return "Легковые автомобили производства Японии"

    asian_brands = {
        "haval", "хавал", "хавейл", "chery", "чери", "geely", "джили", "changan", "чанган",
        "omoda", "омода", "jaecoo", "джейку", "exeed", "эксид", "tank", "танк", "jetour", "джетур",
        "byd", "lixiang", "li auto", "li", "zeekr", "зикры", "voyah", "воя", "hongqi", "хончи",
        "faw", "фав", "dongfeng", "донгфенг", "jac", "джак", "gac", "гак", "baic", "баик",
        "kaiyi", "каи", "forthing", "фортинг", "great wall", "грейт вол", "lifan", "лифан",
        "zotye", "зоти", "belgee", "белджи", "knewstar", "seres", "серес", "aito", "аито",
        "oting", "солярис", "solaris", "evolute", "эволют",
        "hyundai", "хендэ", "хендай", "хюндай", "kia", "киа", "genesis", "генезис",
        "ssangyong", "сангйонг", "kgm", "daewoo", "дэу", "ravon", "равон",
    }
    if clean_brand in asian_brands:
        return "Легковые автомобили азиатские (кроме Японии)"

    european_brands = {
        "mercedes-benz", "mercedes", "мерседес", "bmw", "бмв", "audi", "ауди",
        "volkswagen", "фольксваген", "vw", "porsche", "порше", "opel", "опель",
        "renault", "рено", "peugeot", "пежо", "citroen", "ситроен", "ds",
        "skoda", "шкода", "seat", "сеат", "cupra", "купра", "volvo", "вольво",
        "land rover", "ленд ровер", "range rover", "рейндж ровер", "jaguar", "ягуар",
        "mini", "мини", "fiat", "фиат", "alfa romeo", "альфа ромео", "maserati", "мазерати",
        "dacia", "дачия", "smart", "смарт", "rolls-royce", "bentley", "aston martin",
    }
    if clean_brand in european_brands:
        return "Легковые автомобили европейского производства"

    american_brands = {
        "ford", "форд", "chevrolet", "шевроле", "cadillac", "кадиллак", "gmc", "джиэмси",
        "buick", "бьюик", "dodge", "додж", "chrysler", "крайслер", "jeep", "джип",
        "ram", "рэм", "tesla", "тесла", "lincoln", "линкольн", "pontiac", "понтиак", "hummer", "хаммер",
    }
    if clean_brand in american_brands:
        return "Легковые автомобили американского производства"

    # 3. Check VIN WMI prefix
    if clean_vin:
        c = clean_vin[0]
        if c == "J":
            return "Легковые автомобили производства Японии"
        if c in ("K", "L"):
            return "Легковые автомобили азиатские (кроме Японии)"
        if c in ("W", "V", "S", "T", "Y", "Z"):
            return "Легковые автомобили европейского производства"
        if c in ("1", "4", "5", "2", "3"):
            return "Легковые автомобили американского производства"
        if c == "X":
            return "Легковые автомобили отечественные"

    return "Легковые автомобили отечественные"


def check_vehicle_localization(brand: str, vin: str | None = None) -> tuple[str, bool, str]:
    """Check vehicle manufacturer origin and whether it is a localized assembly in Russia.

    Returns:
        (category, is_localized_in_russia, explanation_note)
    """
    clean_brand = brand.strip().lower() if brand else ""
    clean_vin = vin.strip().upper() if vin else ""

    # Known Russian plants for foreign brands
    russian_foreign_wmi: Final[dict[str, str]] = {
        "X7M": "ТагАЗ (Hyundai Accent, Sonata, Santa Fe Classic)",
        "X4X": "Автотор (BMW, Kia, Hyundai)",
        "Z94": "ХММР (Hyundai Solaris, Creta, Kia Rio)",
        "X7L": "Автофрамос / Рено Россия (Renault Logan, Duster)",
        "X89": "Рено Россия",
        "XW8": "Фольксваген Груп Рус (VW Polo, Tiguan, Skoda Rapid)",
        "X96": "ГАЗ (сборка Skoda Octavia, VW Jetta)",
        "X9F": "Форд Всеволожск (Ford Focus, Mondeo)",
        "XW7": "Тойота Мотор Шушары (Toyota Camry, RAV4)",
        "X6D": "Ниссан Мэнуфэкчуринг Рус (Nissan Qashqai, X-Trail)",
        "XTC": "Хавейл Мотор Мануфактуринг Рус (Haval Jolion, F7)",
    }

    wmi3 = clean_vin[:3] if len(clean_vin) >= 3 else ""
    is_foreign_brand = bool(
        clean_brand
        and clean_brand
        not in (
            "lada", "лада", "ваз", "vaz", "газ", "gaz", "уаз", "uaz",
            "москвич", "moskvich", "тагаз", "tagaz", "иж", "izh", "sollers", "соллерс",
        )
    )

    is_localized = False
    note = ""

    if wmi3 in russian_foreign_wmi and is_foreign_brand:
        is_localized = True
        plant = russian_foreign_wmi[wmi3]
        note = (
            f"Локализованная сборка в РФ: {plant}. "
            "По стандартам Минюста РФ эксперт вправе применить категорию страны бренда "
            "либо категорию отечественного производства."
        )
    elif clean_vin.startswith(("X", "Z94")) and is_foreign_brand:
        is_localized = True
        note = (
            "Иномарка российской сборки (WMI VIN: Россия). "
            "Допустимо применение категории бренда или отечественной."
        )
    elif clean_brand in ("тагаз", "tagaz") or "accent" in clean_brand:
        is_localized = True
        note = "Сборка ТагАЗ (РФ). Для Hyundai Accent допустима категория Азии или РФ."

    category = detect_vehicle_category(brand, vin=vin)
    return category, is_localized, note
