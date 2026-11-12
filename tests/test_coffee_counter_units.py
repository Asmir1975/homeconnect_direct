"""Units of the coffee maker counters, named and counted like the Home Connect app."""

import json
from pathlib import Path

import pytest
from custom_components.homeconnect_ws.entity_descriptions.consumer_products import (
    CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import EntityCategory, UnitOfVolume

TRANSLATIONS = Path(__file__).parents[1] / "custom_components/homeconnect_ws/translations"
COUNTER_UNITS = {
    "sensor_count_coffee": ("cups", "Tassen"),
    "sensor_count_hot_water_cups": ("cups", "Tassen"),
    "sensor_count_coffee_milk": ("cups", "Tassen"),
    "sensor_eq700_beverage_counter_milk": ("cups", "Tassen"),
}

UNTOUCHED = (
    "sensor_count_ristretto_espresso",
    "sensor_count_frothy_milk",
    "sensor_count_hot_milk",
    "sensor_count_powder_coffee",
)


def _sensors() -> dict:
    return {d.key: d for d in CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS["sensor"]}


def test_hot_water_amount_is_a_volume_in_milliliters() -> None:
    """The amount counter is the only one with a native unit."""
    sensor = _sensors()["sensor_count_hot_water"]
    assert sensor.device_class is SensorDeviceClass.VOLUME
    assert sensor.native_unit_of_measurement == UnitOfVolume.MILLILITERS


@pytest.mark.parametrize(("lang", "index"), [("en", 0), ("de", 1)])
def test_counter_units_come_from_translations(lang: str, index: int) -> None:
    """Counters have no native unit, their unit is translated."""
    sensors = _sensors()
    texts = json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8"))
    for key, units in COUNTER_UNITS.items():
        if key in sensors:
            assert sensors[key].native_unit_of_measurement is None
        assert texts["entity"]["sensor"][key]["unit_of_measurement"] == units[index]


def test_counters_are_diagnostic() -> None:
    """The counters are statistics and belong to the diagnostic card."""
    sensors = _sensors()
    for key in [*COUNTER_UNITS, *UNTOUCHED, "sensor_count_hot_water"]:
        assert sensors[key].entity_category is EntityCategory.DIAGNOSTIC
