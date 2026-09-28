"""Forensic vehicle valuation package (comparative approach)."""

from app.services.valuation.constants import (
    BARGAINING_DISCOUNTS,
    E_BASE,
    ROSSTAT_CPI_NONFOOD,
    VARIATION_THRESHOLD,
    WEAR_COEFFICIENTS,
    BargainingCategory,
    VehicleWearCategory,
)
from app.services.valuation.engine import (
    PhysicalWearResult,
    VariationResult,
    calculate_analog_weights,
    calculate_bargaining_adjustment,
    calculate_deflator,
    calculate_final_market_value,
    calculate_physical_wear,
    calculate_sample_mean,
    calculate_variation_coefficient,
    calculate_wear_adjustment,
)
from app.services.valuation.schemas import (
    AnalogAdjustmentResult,
    AnalogVehicleInput,
    TargetVehicleInput,
    ValuationReport,
    ValuationRequest,
    VariationAnalysis,
)
from app.services.valuation.service import ValuationService

__all__ = [
    "BARGAINING_DISCOUNTS",
    "E_BASE",
    "ROSSTAT_CPI_NONFOOD",
    "VARIATION_THRESHOLD",
    "WEAR_COEFFICIENTS",
    "AnalogAdjustmentResult",
    "AnalogVehicleInput",
    "BargainingCategory",
    "PhysicalWearResult",
    "TargetVehicleInput",
    "ValuationReport",
    "ValuationRequest",
    "ValuationService",
    "VariationAnalysis",
    "VariationResult",
    "VehicleWearCategory",
    "calculate_analog_weights",
    "calculate_bargaining_adjustment",
    "calculate_deflator",
    "calculate_final_market_value",
    "calculate_physical_wear",
    "calculate_sample_mean",
    "calculate_variation_coefficient",
    "calculate_wear_adjustment",
]
