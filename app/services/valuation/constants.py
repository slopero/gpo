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
