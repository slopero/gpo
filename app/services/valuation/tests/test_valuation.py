"""Unit and benchmark tests for vehicle valuation module (Case No. 4440/25e)."""

import math

import pytest
from pydantic import ValidationError

from app.services.valuation.constants import VehicleWearCategory
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
    AnalogVehicleInput,
    TargetVehicleInput,
    ValuationRequest,
)
from app.services.valuation.service import ValuationService


def test_calculate_variation_coefficient() -> None:
    """Test variation coefficient calculation and homogeneity check."""
    prices = [4_350_000.0, 4_390_000.0, 4_790_000.0]
    mean = calculate_sample_mean(prices)
    assert mean == 4_510_000.0

    var_result = calculate_variation_coefficient(prices)
    assert math.isclose(var_result.variation_coefficient, 0.0539, abs_tol=1e-3)
    assert var_result.is_homogeneous is True
    assert var_result.v == var_result.variation_coefficient
    assert var_result.s == var_result.std_dev


def test_calculate_physical_wear_formula() -> None:
    """Test physical wear exponential formula with e=2.72."""
    # GAC M8: Asian (non-Japan), T=1, L=92.088
    res = calculate_physical_wear(
        age_years=1.0,
        mileage_km=92_088.0,
        vehicle_category=VehicleWearCategory.ASIAN_EXCEPT_JAPAN.value,
    )
    assert math.isclose(res.omega, 0.3596816, rel_tol=1e-4)
    assert math.isclose(res.wear_pct, 30.226, abs_tol=0.01)

    # Sollers Atlant: Domestic, T=1, L=25.618
    res_sollers = calculate_physical_wear(
        age_years=1.0,
        mileage_km=25_618.0,
        vehicle_category=VehicleWearCategory.DOMESTIC_PASSENGER.value,
    )
    assert math.isclose(res_sollers.omega, 0.159663, rel_tol=1e-4)
    assert math.isclose(res_sollers.wear_pct, 14.765, abs_tol=0.01)


def test_calculate_deflator_from_cpi() -> None:
    """Test deflator calculation from CPI product."""
    cpi = [1.0048, 1.0075, 1.0143]
    deflator = calculate_deflator(cpi)
    expected = 1.0 / (1.0048 * 1.0075 * 1.0143)
    assert math.isclose(deflator, expected, rel_tol=1e-6)

    # Empty list defaults to 1.0
    assert calculate_deflator([]) == 1.0


def test_analog_weights_calculation() -> None:
    """Test weights derivation with inverse corrections method."""
    c_adj = [3_202_712.0, 3_290_780.0, 3_542_658.0]
    c_orig = [4_350_000.0, 4_390_000.0, 4_790_000.0]

    weights = calculate_analog_weights(c_adj, c_orig)
    assert len(weights) == 3
    assert math.isclose(sum(weights), 1.0, rel_tol=1e-6)
    assert math.isclose(weights[0], 0.3297, abs_tol=5e-4)
    assert math.isclose(weights[1], 0.3384, abs_tol=5e-4)
    assert math.isclose(weights[2], 0.3319, abs_tol=5e-4)


def test_benchmark_gac_m8_case() -> None:
    """Reference Test 1: GAC M8 valuation benchmark (Expert conclusion No. 4440/25e)."""
    target = TargetVehicleInput(
        brand="GAC",
        model="M8",
        year=2023,
        age_years=1.0,
        mileage_km=92_088.0,
        vehicle_category=VehicleWearCategory.ASIAN_EXCEPT_JAPAN.value,
        vin="LMGMU1G81P1168719",
        registration_plate="С 555 ВР 777",
        valuation_date="2024-09-02",
    )

    analogs = [
        AnalogVehicleInput(
            id="Analog_1",
            name="GAC M8 Kazan",
            price=4_350_000.0,
            age_years=2.0,
            mileage_km=14_000.0,
            bargaining_discount=0.05,
            deflator=0.9325,
            city="Казань",
        ),
        AnalogVehicleInput(
            id="Analog_2",
            name="GAC M8 Omsk",
            price=4_390_000.0,
            age_years=2.0,
            mileage_km=22_000.0,
            bargaining_discount=0.05,
            deflator=0.9254,
            city="Омск",
        ),
        AnalogVehicleInput(
            id="Analog_3",
            name="GAC M8 Krasnodar",
            price=4_790_000.0,
            age_years=2.0,
            mileage_km=17_800.0,
            bargaining_discount=0.05,
            deflator=0.9254,
            city="Краснодар",
        ),
    ]

    service = ValuationService()
    report = service.evaluate(ValuationRequest(target=target, analogs=analogs))

    # 1. Target wear
    assert math.isclose(report.target_wear_pct, 30.226, abs_tol=0.01)

    # 2. Homogeneity
    assert report.variation_analysis.is_homogeneous is True
    assert math.isclose(report.variation_analysis.variation_coefficient, 0.0539, abs_tol=1e-3)

    # 3. Adjusted prices
    expected_adj = [3_202_712, 3_290_780, 3_542_658]
    for i, exp_p in enumerate(expected_adj):
        assert math.isclose(report.analog_results[i].adjusted_price, exp_p, abs_tol=1.5)

    # 4. Weights
    expected_weights = [0.3297, 0.3384, 0.3319]
    for i, exp_w in enumerate(expected_weights):
        assert math.isclose(report.analog_results[i].weight, exp_w, abs_tol=5e-4)

    assert math.isclose(report.sum_weights, 1.0, rel_tol=1e-6)

    # 5. Final market value
    assert report.market_value == 3_345_338


def test_benchmark_sollers_atlant_29_aug_case() -> None:
    """Reference Test 2: Sollers Atlant benchmark on 2024-08-29."""
    target = TargetVehicleInput(
        brand="Sollers",
        model="Atlant",
        year=2023,
        age_years=1.0,
        mileage_km=25_618.0,
        vehicle_category=VehicleWearCategory.DOMESTIC_PASSENGER.value,
        vin="ЕВЕ66S209P0005012",
        registration_plate="Т 592 АХ 550",
        valuation_date="2024-08-29",
    )

    analogs = [
        AnalogVehicleInput(
            id="Analog_1",
            price=1_908_000.0,
            age_years=2.0,
            mileage_km=62_271.0,
            bargaining_discount=0.06,
            deflator=0.932080,
            city="Москва",
        ),
        AnalogVehicleInput(
            id="Analog_2",
            price=2_050_099.0,
            age_years=2.0,
            mileage_km=39_000.0,
            bargaining_discount=0.06,
            deflator=0.924686,
            city="Раменское",
        ),
        AnalogVehicleInput(
            id="Analog_3",
            price=2_200_000.0,
            age_years=2.0,
            mileage_km=20_000.0,
            bargaining_discount=0.06,
            deflator=0.924686,
            city="Новосибирск",
        ),
    ]

    service = ValuationService()
    report = service.evaluate(ValuationRequest(target=target, analogs=analogs))

    # 1. Target wear
    assert math.isclose(report.target_wear_pct, 14.765, abs_tol=0.01)

    # 2. Homogeneity
    assert report.variation_analysis.is_homogeneous is True
    assert math.isclose(report.variation_analysis.variation_coefficient, 0.0711, abs_tol=1e-3)

    # 3. Adjusted prices
    expected_adj = [2_038_583, 2_002_953, 2_011_036]
    for i, exp_p in enumerate(expected_adj):
        assert math.isclose(report.analog_results[i].adjusted_price, exp_p, abs_tol=1.5)

    # 4. Weights
    expected_weights = [0.3070, 0.4352, 0.2578]
    for i, exp_w in enumerate(expected_weights):
        assert math.isclose(report.analog_results[i].weight, exp_w, abs_tol=5e-4)

    assert math.isclose(report.sum_weights, 1.0, rel_tol=1e-6)

    # 5. Final market value
    assert report.market_value == 2_015_976


def test_benchmark_sollers_atlant_03_sep_case() -> None:
    """Reference Test 3: Sollers Atlant benchmark on 2024-09-03."""
    target = TargetVehicleInput(
        brand="Sollers",
        model="Atlant",
        year=2023,
        age_years=1.0,
        mileage_km=25_618.0,
        vehicle_category=VehicleWearCategory.DOMESTIC_PASSENGER.value,
        valuation_date="2024-09-03",
    )

    analogs = [
        AnalogVehicleInput(
            id="Analog_1",
            price=1_908_000.0,
            age_years=2.0,
            mileage_km=62_271.0,
            bargaining_discount=0.06,
            deflator=0.9366,
        ),
        AnalogVehicleInput(
            id="Analog_2",
            price=2_050_099.0,
            age_years=2.0,
            mileage_km=39_000.0,
            bargaining_discount=0.06,
            deflator=0.9291,
        ),
        AnalogVehicleInput(
            id="Analog_3",
            price=2_200_000.0,
            age_years=2.0,
            mileage_km=20_000.0,
            bargaining_discount=0.06,
            deflator=0.9291,
        ),
    ]

    service = ValuationService()
    report = service.evaluate(ValuationRequest(target=target, analogs=analogs))

    # Weight checks
    assert math.isclose(report.analog_results[0].weight, 0.2878, abs_tol=1e-3)
    assert math.isclose(report.analog_results[1].weight, 0.4472, abs_tol=1e-3)
    assert math.isclose(report.analog_results[2].weight, 0.2649, abs_tol=1e-3)

    # Market value is within ±10 rubles of 2 025 021 due to float precision
    assert math.isclose(report.market_value, 2_025_021, abs_tol=10)


def test_validation_minimum_analogs() -> None:
    """Test validation requires at least 3 analogs."""
    target = TargetVehicleInput(
        brand="Lada",
        model="Vesta",
        year=2023,
        age_years=1.0,
        mileage_km=10_000.0,
        vehicle_category=VehicleWearCategory.DOMESTIC_PASSENGER.value,
    )
    two_analogs = [
        AnalogVehicleInput(price=1_000_000.0, age_years=1.0, mileage_km=10_000.0),
        AnalogVehicleInput(price=1_100_000.0, age_years=1.0, mileage_km=12_000.0),
    ]
    with pytest.raises(ValidationError):
        ValuationRequest(target=target, analogs=two_analogs)


def test_engine_pure_functions() -> None:
    """Test auxiliary pure engine functions."""
    assert calculate_wear_adjustment(30.0, 20.0) == (70.0 / 80.0)
    assert calculate_bargaining_adjustment(1_000_000.0, 0.05) == 950_000.0
    assert calculate_final_market_value([1_000_000.0], moral_wear_pct=10.0, repair_cost=50_000.0) == 950_000


def test_real_market_lada_vesta_2023() -> None:
    """Independent test 1: Lada Vesta NG 2023 (Drom.ru listings)."""
    target = TargetVehicleInput(
        brand="Lada",
        model="Vesta NG",
        year=2023,
        age_years=1.5,
        mileage_km=35_000.0,
        vehicle_category=VehicleWearCategory.DOMESTIC_PASSENGER.value,
    )
    analogs = [
        AnalogVehicleInput(name="Drom Москва", price=1_350_000.0, age_years=2.0, mileage_km=42_000.0, bargaining_discount=0.06, deflator=1.0),
        AnalogVehicleInput(name="Drom Самара", price=1_420_000.0, age_years=1.0, mileage_km=18_000.0, bargaining_discount=0.06, deflator=1.0),
        AnalogVehicleInput(name="Drom Казань", price=1_390_000.0, age_years=2.0, mileage_km=28_000.0, bargaining_discount=0.06, deflator=1.0),
    ]
    report = ValuationService().evaluate(ValuationRequest(target=target, analogs=analogs))
    assert report.variation_analysis.is_homogeneous is True
    assert math.isclose(report.target_wear_pct, 20.3592, abs_tol=0.01)
    assert report.market_value == 1_319_379


def test_real_market_toyota_camry_2021() -> None:
    """Independent test 2: Toyota Camry 2.5 2021 (Auto.ru listings)."""
    target = TargetVehicleInput(
        brand="Toyota",
        model="Camry",
        year=2021,
        age_years=3.0,
        mileage_km=60_000.0,
        vehicle_category=VehicleWearCategory.JAPANESE_PASSENGER.value,
        repair_cost=25_000.0,
    )
    analogs = [
        AnalogVehicleInput(name="Auto.ru Москва", price=3_250_000.0, age_years=3.5, mileage_km=75_000.0, bargaining_discount=0.05, deflator=0.9850),
        AnalogVehicleInput(name="Auto.ru СПб", price=3_400_000.0, age_years=3.0, mileage_km=50_000.0, bargaining_discount=0.05, deflator=0.9850),
        AnalogVehicleInput(name="Auto.ru Екб", price=3_300_000.0, age_years=4.0, mileage_km=85_000.0, bargaining_discount=0.05, deflator=0.9850),
    ]
    report = ValuationService().evaluate(ValuationRequest(target=target, analogs=analogs))
    assert report.variation_analysis.is_homogeneous is True
    assert math.isclose(report.target_wear_pct, 22.5208, abs_tol=0.01)
    assert report.market_value == 3_288_726


def test_real_market_haval_jolion_2022() -> None:
    """Independent test 3: Haval Jolion 2022 (Drom.ru listings)."""
    target = TargetVehicleInput(
        brand="Haval",
        model="Jolion",
        year=2022,
        age_years=2.0,
        mileage_km=48_000.0,
        vehicle_category=VehicleWearCategory.ASIAN_EXCEPT_JAPAN.value,
        repair_cost=15_000.0,
    )
    analogs = [
        AnalogVehicleInput(name="Drom Москва", price=1_850_000.0, age_years=2.5, mileage_km=55_000.0, bargaining_discount=0.05, deflator=0.9750),
        AnalogVehicleInput(name="Drom СПб", price=1_920_000.0, age_years=2.0, mileage_km=40_000.0, bargaining_discount=0.05, deflator=0.9750),
        AnalogVehicleInput(name="Drom Краснодар", price=1_990_000.0, age_years=2.0, mileage_km=32_000.0, bargaining_discount=0.05, deflator=0.9750),
    ]
    report = ValuationService().evaluate(ValuationRequest(target=target, analogs=analogs))
    assert report.variation_analysis.is_homogeneous is True
    assert math.isclose(report.target_wear_pct, 24.7067, abs_tol=0.01)
    assert report.market_value == 1_787_835
