"""Pure mathematical calculation engine for comparative vehicle valuation."""

import math
from typing import Final, NamedTuple

from app.services.valuation.constants import E_BASE, VARIATION_THRESHOLD, WEAR_COEFFICIENTS


class VariationResult(NamedTuple):
    """Result of statistical variation analysis."""

    variation_coefficient: float
    std_dev: float
    is_homogeneous: bool

    @property
    def v(self) -> float:
        return self.variation_coefficient

    @property
    def s(self) -> float:
        return self.std_dev


class PhysicalWearResult(NamedTuple):
    """Result of physical wear calculation."""

    omega: float
    wear_pct: float


def calculate_sample_mean(prices: list[float]) -> float:
    """Calculate arithmetic mean of prices."""
    if not prices:
        raise ValueError("Prices list cannot be empty")
    return sum(prices) / float(len(prices))


def calculate_variation_coefficient(prices: list[float]) -> VariationResult:
    """Calculate sample mean, unbiased standard deviation, variation coefficient and homogeneity.

    Computes:
        C_cp = sum(prices) / n
        s = sqrt(sum((x - C_cp)^2) / (n - 1))
        v = s / C_cp
        is_homogeneous = (v <= VARIATION_THRESHOLD)

    Returns:
        VariationResult(variation_coefficient=v, std_dev=s, is_homogeneous=(v <= 0.30))
    """
    n: Final[int] = len(prices)
    if n < 2:
        raise ValueError("At least 2 prices are required to compute variation coefficient")

    mean_price: Final[float] = sum(prices) / float(n)
    if mean_price <= 0.0:
        raise ValueError("Mean price must be greater than zero")

    squared_diff_sum: Final[float] = sum((p - mean_price) ** 2 for p in prices)
    unbiased_variance: Final[float] = squared_diff_sum / float(n - 1)
    std_dev: Final[float] = math.sqrt(unbiased_variance)
    v: Final[float] = std_dev / mean_price
    is_homogeneous: Final[bool] = v <= VARIATION_THRESHOLD

    return VariationResult(variation_coefficient=v, std_dev=std_dev, is_homogeneous=is_homogeneous)


def calculate_physical_wear(
    age_years: float,
    mileage_km: float,
    vehicle_category: str,
) -> PhysicalWearResult:
    """Calculate intensity of exploitation (Omega) and normative physical wear percentage (I_ph).

    Formula:
        mileage_thousand = mileage_km / 1000.0
        Omega = a * age_years + b * mileage_thousand
        wear_pct = 100.0 * (1.0 - (2.72 ** (-Omega)))

    Returns:
        PhysicalWearResult(omega, wear_pct)
    """
    if age_years < 0.0:
        raise ValueError("Vehicle age cannot be negative")
    if mileage_km < 0.0:
        raise ValueError("Vehicle mileage cannot be negative")

    coeff_pair = WEAR_COEFFICIENTS.get(vehicle_category)
    if coeff_pair is None:
        normalized_cat = vehicle_category.strip().upper()
        coeff_pair = WEAR_COEFFICIENTS.get(normalized_cat)

    if coeff_pair is None:
        raise ValueError(f"Unknown vehicle category for wear coefficients: '{vehicle_category}'")

    a, b = coeff_pair
    mileage_thousand: Final[float] = mileage_km / 1000.0
    omega: Final[float] = a * age_years + b * mileage_thousand
    wear_pct: Final[float] = 100.0 * (1.0 - (E_BASE ** (-omega)))

    return PhysicalWearResult(omega=omega, wear_pct=wear_pct)


def calculate_wear_adjustment(wear_target_pct: float, wear_analog_pct: float) -> float:
    """Calculate wear adjustment coefficient K_wear reflecting relative residual utility.

    Formula:
        K_wear = (100.0 - wear_target_pct) / (100.0 - wear_analog_pct)
    """
    residual_analog: Final[float] = 100.0 - wear_analog_pct
    if residual_analog <= 0.0:
        raise ValueError("Analog residual utility must be positive (wear must be < 100%)")

    residual_target: Final[float] = 100.0 - wear_target_pct
    return residual_target / residual_analog


def calculate_bargaining_adjustment(price: float, discount_rate: float) -> float:
    """Calculate price after applying bargaining discount.

    Formula:
        price_after_bargaining = price * (1.0 - discount_rate)
    """
    if discount_rate < 0.0 or discount_rate >= 1.0:
        raise ValueError("Bargaining discount rate must be between 0.0 and 1.0")
    return price * (1.0 - discount_rate)


def calculate_deflator(cpi_series: list[float]) -> float:
    """Calculate price deflator K_priv from monthly consumer price indices.

    Formula:
        cumulative_inflation = prod(cpi_series)
        K_deflator = 1.0 / cumulative_inflation
    """
    if not cpi_series:
        return 1.0

    cumulative_inflation: Final[float] = math.prod(cpi_series)
    if cumulative_inflation <= 0.0:
        raise ValueError("Cumulative inflation product must be greater than zero")

    return 1.0 / cumulative_inflation


def calculate_analog_weights(
    deviations: list[float],
    c_original_list: list[float] | None = None,
) -> list[float]:
    """Calculate analog weighting coefficients using the inverse corrections method.

    Can be called either with:
    1) deviations = absolute deltas |1 - r_i|
    2) deviations = c_adjusted_list and c_original_list = original prices

    Formula:
        d_i = Delta_i / sum(Delta)
        K_vi = (1.0 - d_i) / (n - 1)
    """
    target_deviations: list[float] = deviations
    if c_original_list is not None:
        c_adjusted_list = deviations
        if len(c_adjusted_list) != len(c_original_list):
            raise ValueError("Adjusted and original price lists must have the same length")
        target_deviations = [
            abs(1.0 - (c_adj / c_orig))
            for c_adj, c_orig in zip(c_adjusted_list, c_original_list, strict=True)
        ]

    n: Final[int] = len(target_deviations)
    if n == 0:
        return []
    if n == 1:
        return [1.0]

    sum_deltas: Final[float] = sum(target_deviations)
    if sum_deltas == 0.0:
        # All analogs have zero deviation: distribute equally
        equal_weight: Final[float] = 1.0 / float(n)
        return [equal_weight] * n

    relative_shares: Final[list[float]] = [delta / sum_deltas for delta in target_deviations]
    weights: Final[list[float]] = [(1.0 - d) / float(n - 1) for d in relative_shares]
    return weights


def calculate_final_market_value(
    weighted_prices: list[float],
    moral_wear_pct: float = 0.0,
    repair_cost: float = 0.0,
) -> int:
    """Calculate final rounded market value taking into account moral wear and repairs.

    Formula:
        raw_value = sum(weighted_prices) * (1.0 - moral_wear_pct / 100.0) + repair_cost
        market_value = round(raw_value)
    """
    raw_value: Final[float] = (
        sum(weighted_prices) * (1.0 - moral_wear_pct / 100.0) + repair_cost
    )
    return round(raw_value)
