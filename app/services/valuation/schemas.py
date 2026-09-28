"""Pydantic schemas for data validation and valuation reporting."""

from datetime import date
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TargetVehicleInput(BaseModel):
    """Input parameters for the target vehicle being evaluated."""

    model_config = ConfigDict(extra="ignore")

    brand: str = Field(..., description="Brand/Make of vehicle")
    model: str = Field(..., description="Model of vehicle")
    year: int = Field(..., description="Year of manufacture", ge=1900, le=2100)
    age_years: float = Field(..., description="Actual age at valuation date (years)", ge=0.0)
    mileage_km: float = Field(..., description="Actual odometer mileage (km)", ge=0.0)
    vehicle_category: str = Field(
        ...,
        description="Normative category key from VehicleWearCategory, e.g. 'ASIAN_EXCEPT_JAPAN'",
    )
    bargaining_category: str | None = Field(
        default=None,
        description="Category for bargaining discount, e.g. 'DOMESTIC_VEHICLE' or 'IMPORT_VEHICLE'",
    )
    vin: str | None = Field(default=None, description="VIN number if available")
    registration_plate: str | None = Field(
        default=None,
        description="License plate number if available",
    )
    valuation_date: date | str | None = Field(
        default=None,
        description="Legal evaluation date",
    )
    moral_wear_pct: float = Field(
        default=0.0,
        description="Moral wear percentage (default 0.0%)",
        ge=0.0,
        le=100.0,
    )
    repair_cost: float = Field(
        default=0.0,
        description="Repair costs for operational defects (default 0.0 rubles)",
        ge=0.0,
    )


class AnalogVehicleInput(BaseModel):
    """Input parameters for an analog vehicle offer from the open market."""

    model_config = ConfigDict(extra="ignore")

    id: str | None = Field(default=None, description="Identifier of the analog")
    name: str | None = Field(default=None, description="Description or title of the analog")
    price: float = Field(..., description="Initial public asking price (rubles)", gt=0.0)
    age_years: float = Field(..., description="Age at offer date (years)", ge=0.0)
    mileage_km: float = Field(..., description="Mileage at offer date (km)", ge=0.0)
    city: str | None = Field(default=None, description="City / Region of offer")
    offer_date: date | str | None = Field(default=None, description="Date of offer publication")
    bargaining_discount: float | None = Field(
        default=None,
        description="Custom bargaining discount (e.g. 0.05 for 5%). If None, deduced from category",
        ge=0.0,
        le=1.0,
    )
    deflator: float | None = Field(
        default=None,
        description="Price deflator (K_priv). If None, calculated from cpi_series or defaults to 1.0",
        gt=0.0,
    )
    cpi_series: list[float] | None = Field(
        default=None,
        description="Monthly CPI multipliers between evaluation and offer date",
    )


class ValuationRequest(BaseModel):
    """Complete valuation request containing target vehicle and market analogs."""

    model_config = ConfigDict(extra="ignore")

    target: TargetVehicleInput = Field(..., description="Target vehicle specification")
    analogs: Annotated[
        list[AnalogVehicleInput],
        Field(min_length=3, description="List of market analogs (minimum 3 required)"),
    ]


class VariationAnalysis(BaseModel):
    """Statistical homogeneity analysis of analog sample (Stage 2)."""

    model_config = ConfigDict(extra="ignore")

    mean_price: float = Field(..., description="Sample mean price (rubles)")
    std_dev: float = Field(..., description="Unbiased sample standard deviation (rubles)")
    variation_coefficient: float = Field(..., description="Variation coefficient v = s / mean")
    is_homogeneous: bool = Field(
        ...,
        description="Homogeneity flag: True if variation_coefficient <= 0.30",
    )


class AnalogAdjustmentResult(BaseModel):
    """Detailed step-by-step adjustment results for a single analog."""

    model_config = ConfigDict(extra="ignore")

    analog_id: str = Field(..., description="Identifier of the analog")
    original_price: float = Field(..., description="Initial offer price (rubles)")
    age_years: float = Field(..., description="Age of analog (years)")
    mileage_km: float = Field(..., description="Mileage of analog (km)")
    omega: float = Field(..., description="Operating intensity indicator Omega")
    wear_pct: float = Field(..., description="Physical wear percentage (I_ph)")
    k_wear: float = Field(..., description="Wear adjustment factor (K_wear)")
    price_after_wear: float = Field(..., description="Price adjusted for wear (C_1)")
    bargaining_discount: float = Field(..., description="Applied bargaining discount rate")
    price_after_bargaining: float = Field(..., description="Price adjusted for bargaining (C_2)")
    deflator: float = Field(..., description="Time price deflator (K_priv)")
    adjusted_price: float = Field(..., description="Fully adjusted price (C_skorr)")
    scale_ratio: float = Field(..., description="Ratio of adjusted to original price r_i")
    abs_delta: float = Field(..., description="Absolute deviation Delta_i = |1 - r_i|")
    relative_share_d: float = Field(..., description="Relative deviation share d_i = Delta_i / Sigma")
    weight: float = Field(..., description="Weight coefficient K_vi = (1 - d_i) / (n - 1)")
    weighted_price: float = Field(..., description="Weighted analog price C_skorr * K_vi")


class ValuationReport(BaseModel):
    """Final forensic evaluation report and decision justification."""

    model_config = ConfigDict(extra="ignore")

    target_vehicle: TargetVehicleInput = Field(..., description="Target vehicle data")
    target_omega: float = Field(..., description="Target operating intensity Omega")
    target_wear_pct: float = Field(..., description="Target physical wear percentage")
    variation_analysis: VariationAnalysis = Field(..., description="Statistical homogeneity check")
    analog_results: list[AnalogAdjustmentResult] = Field(
        ...,
        description="Step-by-step calculations for each analog",
    )
    sum_weights: float = Field(..., description="Sum of weight coefficients (must equal 1.0)")
    moral_wear_pct: float = Field(..., description="Moral wear percentage")
    repair_cost: float = Field(..., description="Cost of defect repairs")
    market_value: int = Field(..., description="Final rounded market value (rubles)")
    valuation_date: str | None = Field(default=None, description="Evaluation date string")
