"""
Laundry, dishwasher and coffee values checked against real appliance fixtures.

Each fixture in tests/fixtures is the diagnostics download of one appliance,
trimmed to the saved device description and the values it reported, without
serial numbers, network or account data.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.select import HCSelect
from custom_components.homeconnect_ws.sensor import HCSensor
from custom_components.homeconnect_ws.switch import HCSwitch

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance
    from homeconnect_websocket.testutils import MockApplianceType

FIXTURES = Path(__file__).parent / "fixtures"
WASHER = "wgb244a7nl_washer"
DRYER = "wqb246c7nl_dryer"
DISHWASHER = "sn87y801be_dishwasher"
COFFEE = "ct836leb6_coffeemaker"

PLATFORMS = {
    "binary_sensor": HCBinarySensor,
    "select": HCSelect,
    "sensor": HCSensor,
    "switch": HCSwitch,
}

# fixture, platform, key, (enabled by default, value the appliance reported)
NEW_ENTITIES = [
    (WASHER, "sensor", "sensor_washer_laundry_load", (True, 1101)),
    (WASHER, "sensor", "sensor_washer_textile_type", (True, "mixed")),
    (DRYER, "binary_sensor", "binary_sensor_dryer_cooldown_running", (True, False)),
    (DRYER, "binary_sensor", "binary_sensor_dryer_clean_self_cleaning_module", (True, False)),
    (DRYER, "binary_sensor", "binary_sensor_dryer_evaporator_frozen", (True, None)),
    (DISHWASHER, "switch", "switch_dishwasher_eco_prognosis", (True, True)),
    (DISHWASHER, "switch", "switch_dishwasher_error_light", (False, True)),
    (DISHWASHER, "switch", "switch_dishwasher_time_light", (False, True)),
    (
        DISHWASHER,
        "select",
        "select_dishwasher_door_opening_handling",
        (True, "doublepushtoopenanddryingassistant"),
    ),
    (COFFEE, "select", "select_coffee_illumination", (False, "wheninuse")),
]


async def load_fixture(mock_homeconnect_appliance: MockApplianceType, name: str) -> HomeAppliance:
    """Create the appliance from a fixture and apply the values it reported."""
    fixture = json.loads((FIXTURES / f"{name}.json").read_text())
    appliance = await mock_homeconnect_appliance(description=fixture["entry_data"]["description"])
    for state in fixture["appliance_state"]["entities"]:
        if state["name"] in appliance.entities:
            await appliance.entities[state["name"]].update({"value": state["value_raw"]})
    return appliance


def make_entity(appliance: HomeAppliance, platform: str, key: str) -> Any:
    """Build the Home Assistant entity for a description key."""
    description = next(d for d in get_available_entities(appliance)[platform] if d.key == key)
    runtime_data = SimpleNamespace(
        appliance=appliance,
        coordinator=MagicMock(connected=True),
        device_info={},
    )
    return PLATFORMS[platform](description, runtime_data)


def state_of(entity: Any) -> Any:
    """Return the value Home Assistant would show."""
    if isinstance(entity, HCSensor):
        return entity.native_value
    if isinstance(entity, HCSelect):
        return entity.current_option
    return entity.is_on


@pytest.mark.parametrize(("fixture", "platform", "key", "expected"), NEW_ENTITIES)
async def test_entity_matches_fixture(
    mock_homeconnect_appliance: MockApplianceType,
    fixture: str,
    platform: str,
    key: str,
    expected: tuple[bool, Any],
) -> None:
    """Each appliance gets the entity, with the value it reported."""
    enabled, value = expected
    appliance = await load_fixture(mock_homeconnect_appliance, fixture)
    entity = make_entity(appliance, platform, key)
    assert entity.entity_description.entity_registry_enabled_default is enabled
    assert state_of(entity) == value


@pytest.mark.parametrize(
    ("fixture", "platform", "key"),
    [
        (fixture, platform, key)
        for fixture in (WASHER, DRYER, DISHWASHER, COFFEE)
        for owner, platform, key, _expected in NEW_ENTITIES
        if fixture != owner
    ],
)
async def test_entity_only_on_appliances_that_report_it(
    mock_homeconnect_appliance: MockApplianceType,
    fixture: str,
    platform: str,
    key: str,
) -> None:
    """Appliances without the value get no entity."""
    appliance = await load_fixture(mock_homeconnect_appliance, fixture)
    keys = [description.key for description in get_available_entities(appliance)[platform]]
    assert key not in keys


@pytest.mark.parametrize(("raw", "expected"), [(1101, 1101), (0, 0), (65535, None)])
async def test_laundry_load_without_value_is_unknown(
    mock_homeconnect_appliance: MockApplianceType,
    raw: int,
    expected: int | None,
) -> None:
    """Some washers send 65535 when they have no load value, which is not 65.5 kg."""
    appliance = await load_fixture(mock_homeconnect_appliance, WASHER)
    sensor = make_entity(appliance, "sensor", "sensor_washer_laundry_load")
    await appliance.entities["LaundryCare.Washer.Status.ProcessingData.LaundryLoad"].update(
        {"value": raw}
    )
    assert sensor.native_value == expected
