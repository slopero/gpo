"""Root test wrapper for vehicle valuation tests."""

from app.services.valuation.tests.test_valuation import (
    test_analog_weights_calculation,
    test_benchmark_gac_m8_case,
    test_benchmark_sollers_atlant_03_sep_case,
    test_benchmark_sollers_atlant_29_aug_case,
    test_calculate_deflator_from_cpi,
    test_calculate_physical_wear_formula,
    test_calculate_variation_coefficient,
    test_engine_pure_functions,
    test_real_market_haval_jolion_2022,
    test_real_market_lada_vesta_2023,
    test_real_market_toyota_camry_2021,
    test_validation_minimum_analogs,
)

__all__ = [
    "test_analog_weights_calculation",
    "test_benchmark_gac_m8_case",
    "test_benchmark_sollers_atlant_03_sep_case",
    "test_benchmark_sollers_atlant_29_aug_case",
    "test_calculate_deflator_from_cpi",
    "test_calculate_physical_wear_formula",
    "test_calculate_variation_coefficient",
    "test_engine_pure_functions",
    "test_real_market_haval_jolion_2022",
    "test_real_market_lada_vesta_2023",
    "test_real_market_toyota_camry_2021",
    "test_validation_minimum_analogs",
]
