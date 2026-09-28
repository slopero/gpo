"""Service interface for complete forensic vehicle valuation workflow."""

from typing import Final

from app.services.valuation.constants import BARGAINING_DISCOUNTS
from app.services.valuation.engine import (
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


class ValuationService:
    """Service for calculating vehicle market value via the comparative sales approach."""

    def __init__(self, strict_homogeneity: bool = False) -> None:
        """Initialize valuation service.

        Args:
            strict_homogeneity: If True, raises ValueError when variation coefficient exceeds 0.30.
        """
        self.strict_homogeneity: Final[bool] = strict_homogeneity

    def evaluate(self, request: ValuationRequest) -> ValuationReport:
        """Execute full 8-stage valuation pipeline for the provided request.

        Args:
            request: Validated valuation request with target and analogs.

        Returns:
            ValuationReport containing step-by-step metrics and final market value.
        """
        target: TargetVehicleInput = request.target
        analogs: list[AnalogVehicleInput] = request.analogs

        # Stage 1 & 2: Homogeneity verification of initial analog prices
        prices: list[float] = [a.price for a in analogs]
        mean_price = calculate_sample_mean(prices)
        var_result = calculate_variation_coefficient(prices)

        variation_analysis = VariationAnalysis(
            mean_price=mean_price,
            std_dev=var_result.std_dev,
            variation_coefficient=var_result.variation_coefficient,
            is_homogeneous=var_result.is_homogeneous,
        )

        if self.strict_homogeneity and not var_result.is_homogeneous:
            raise ValueError(
                f"Sample is heterogeneous: variation coefficient {var_result.variation_coefficient:.4f} > 0.30"
            )

        # Stage 3: Target vehicle physical wear
        target_wear = calculate_physical_wear(
            age_years=target.age_years,
            mileage_km=target.mileage_km,
            vehicle_category=target.vehicle_category,
        )

        # Stages 3-6: Individual analog adjustments
        raw_adjusted_prices: list[float] = []
        analog_pre_results: list[dict[str, float | str]] = []

        for idx, analog in enumerate(analogs, start=1):
            analog_id = analog.id or f"Analog_{idx}"

            # Stage 3: Analog physical wear
            analog_wear = calculate_physical_wear(
                age_years=analog.age_years,
                mileage_km=analog.mileage_km,
                vehicle_category=target.vehicle_category,
            )

            # Stage 4: Wear adjustment
            k_wear = calculate_wear_adjustment(
                wear_target_pct=target_wear.wear_pct,
                wear_analog_pct=analog_wear.wear_pct,
            )
            price_c1 = analog.price * k_wear

            # Stage 5: Bargaining adjustment
            discount = analog.bargaining_discount
            if discount is None:
                discount = self._resolve_bargaining_discount(target)
            price_c2 = calculate_bargaining_adjustment(price_c1, discount)

            # Stage 6: Price deflator (time adjustment)
            deflator = analog.deflator
            if deflator is None:
                if analog.cpi_series is not None:
                    deflator = calculate_deflator(analog.cpi_series)
                else:
                    deflator = 1.0
            adjusted_price = price_c2 * deflator

            raw_adjusted_prices.append(adjusted_price)
            analog_pre_results.append(
                {
                    "analog_id": analog_id,
                    "original_price": analog.price,
                    "age_years": analog.age_years,
                    "mileage_km": analog.mileage_km,
                    "omega": analog_wear.omega,
                    "wear_pct": analog_wear.wear_pct,
                    "k_wear": k_wear,
                    "price_after_wear": price_c1,
                    "bargaining_discount": discount,
                    "price_after_bargaining": price_c2,
                    "deflator": deflator,
                    "adjusted_price": adjusted_price,
                }
            )

        # Stage 7: Inverse corrections weighting
        scale_ratios = [
            c_adj / c_orig
            for c_adj, c_orig in zip(raw_adjusted_prices, prices, strict=True)
        ]
        abs_deltas = [abs(1.0 - r) for r in scale_ratios]
        sum_deltas = sum(abs_deltas)
        relative_shares = [
            (delta / sum_deltas) if sum_deltas > 0.0 else (1.0 / len(abs_deltas))
            for delta in abs_deltas
        ]
        weights = calculate_analog_weights(abs_deltas)

        analog_results: list[AnalogAdjustmentResult] = []
        weighted_prices: list[float] = []

        for i, pre in enumerate(analog_pre_results):
            weight = weights[i]
            adj_price = float(pre["adjusted_price"])
            weighted_p = adj_price * weight
            weighted_prices.append(weighted_p)

            analog_results.append(
                AnalogAdjustmentResult(
                    analog_id=str(pre["analog_id"]),
                    original_price=float(pre["original_price"]),
                    age_years=float(pre["age_years"]),
                    mileage_km=float(pre["mileage_km"]),
                    omega=float(pre["omega"]),
                    wear_pct=float(pre["wear_pct"]),
                    k_wear=float(pre["k_wear"]),
                    price_after_wear=float(pre["price_after_wear"]),
                    bargaining_discount=float(pre["bargaining_discount"]),
                    price_after_bargaining=float(pre["price_after_bargaining"]),
                    deflator=float(pre["deflator"]),
                    adjusted_price=adj_price,
                    scale_ratio=scale_ratios[i],
                    abs_delta=abs_deltas[i],
                    relative_share_d=relative_shares[i],
                    weight=weight,
                    weighted_price=weighted_p,
                )
            )

        # Stage 8: Final market value
        market_value = calculate_final_market_value(
            weighted_prices=weighted_prices,
            moral_wear_pct=target.moral_wear_pct,
            repair_cost=target.repair_cost,
        )

        val_date_str: str | None = None
        if target.valuation_date is not None:
            val_date_str = str(target.valuation_date)

        return ValuationReport(
            target_vehicle=target,
            target_omega=target_wear.omega,
            target_wear_pct=target_wear.wear_pct,
            variation_analysis=variation_analysis,
            analog_results=analog_results,
            sum_weights=sum(weights),
            moral_wear_pct=target.moral_wear_pct,
            repair_cost=target.repair_cost,
            market_value=market_value,
            valuation_date=val_date_str,
        )

    def evaluate_dict(self, data: dict[str, object]) -> ValuationReport:
        """Validate input dictionary and execute valuation pipeline."""
        request = ValuationRequest.model_validate(data)
        return self.evaluate(request)

    @staticmethod
    def _resolve_bargaining_discount(target: TargetVehicleInput) -> float:
        """Resolve standard bargaining discount from vehicle category."""
        if target.bargaining_category is not None:
            disc = BARGAINING_DISCOUNTS.get(target.bargaining_category)
            if disc is not None:
                return disc

        disc = BARGAINING_DISCOUNTS.get(target.vehicle_category)
        if disc is not None:
            return disc

        return 0.05
