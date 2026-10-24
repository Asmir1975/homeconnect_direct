"""CoffeeMaker messages ordered by relevance and the Problem binary sensor."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.sensor import HCEventSensor
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

PREFIX = "ConsumerProducts.CoffeeMaker.Event."
EVENT_ENUM = {"0": "Off", "1": "Present", "2": "Confirmed"}


def _description(*names: str) -> DeviceDescription:
    return DeviceDescription(
        event=[
            EntityDescription(uid=4600 + index, name=PREFIX + name, enumeration=EVENT_ENUM)
            for index, name in enumerate(names)
        ]
    )


async def _runtime(appliance_factory: MockApplianceType, *names: str) -> HCData:
    appliance = await appliance_factory(description=_description(*names))
    appliance.info = {"deviceID": "test_coffeemaker"}
    return HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=get_available_entities(appliance),
        coordinator=MagicMock(),
    )


async def test_messages_put_everyday_problems_first(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An everyday problem wins over a hint and over a rare fault."""
    runtime = await _runtime(
        mock_homeconnect_appliance,
        "DripTrayFull",
        "WaterCriticallyEmpty",
        "WaterTankEmpty",
        "HeaterError",
    )
    description = next(
        item
        for item in runtime.available_entity_descriptions["event_sensor"]
        if item.key == "sensor_eq700_messages"
    )
    assert description.options == [
        "water_tank_empty",
        "water_critically_empty",
        "heater_error",
        "drip_tray_full",
        "none",
    ]
    sensor = HCEventSensor(description, runtime)
    for name in ("DripTrayFull", "HeaterError", "WaterTankEmpty"):
        await runtime.appliance.entities[PREFIX + name].update({"value": 1})
    assert sensor.native_value == "water_tank_empty"


async def test_problem_sensor_reacts_to_serious_events_only(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Hints and the rinse prompt do not switch Problem on, the empty drip tray does."""
    runtime = await _runtime(
        mock_homeconnect_appliance,
        "DripTrayFull",
        "SpecialRinsing",
        "EmptyDripTrayRemoveContainer",
        "HeaterError",
    )
    description = next(
        item
        for item in runtime.available_entity_descriptions["binary_sensor"]
        if item.key == "binary_sensor_eq700_problem"
    )
    assert tuple(description.entities) == (
        PREFIX + "EmptyDripTrayRemoveContainer",
        PREFIX + "HeaterError",
    )
    assert not description.force_disabled_default
    sensor = HCBinarySensor(description, runtime)
    assert not sensor.is_on
    for name in ("DripTrayFull", "SpecialRinsing"):
        await runtime.appliance.entities[PREFIX + name].update({"value": 1})
    assert not sensor.is_on
    await runtime.appliance.entities[PREFIX + "EmptyDripTrayRemoveContainer"].update({"value": 1})
    assert sensor.is_on
    await runtime.appliance.entities[PREFIX + "EmptyDripTrayRemoveContainer"].update({"value": 0})
    assert not sensor.is_on


async def test_no_problem_sensor_without_serious_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A profile with only hints gets no Problem sensor."""
    appliance = await mock_homeconnect_appliance(description=_description("DripTrayFull"))
    available = get_available_entities(appliance)
    assert not any(item.key == "binary_sensor_eq700_problem" for item in available["binary_sensor"])
