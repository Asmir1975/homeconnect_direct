"""Coffee maker container state sensors built from the events of the profile."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
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


async def _sensors(appliance_factory: MockApplianceType, *names: str) -> dict:
    appliance = await appliance_factory(description=_description(*names))
    return {item.key: item for item in get_available_entities(appliance)["event_sensor"]}


async def test_eq700_profile_gets_water_and_pomace_but_no_second_bean_sensor(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The bean container only has an empty event here, the binary sensor already covers it."""
    sensors = await _sensors(
        mock_homeconnect_appliance,
        "WaterTankEmpty",
        "WaterCriticallyEmpty",
        "WaterTankNearlyEmpty",
        "WaterTankNotInserted",
        "BeanContainerEmpty",
        "PomaceCaveFull",
    )
    assert sensors["sensor_water_tank"].options == [
        "empty",
        "critically_empty",
        "nearly_empty",
        "not_inserted",
        "full",
    ]
    assert sensors["sensor_pomace_container"].options == ["full", "ok"]
    assert "sensor_bean_container" not in sensors


async def test_iq700_profile_gets_all_container_states(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """With the full set of events the bean and grounds containers get every state."""
    sensors = await _sensors(
        mock_homeconnect_appliance,
        "BeanContainerEmpty",
        "BeanContainerNearlyEmpty",
        "BeanContainerIsNotPresent",
        "BeanContainerNotFullyInserted",
        "PomaceCaveFull",
        "PomaceContainerMissing",
    )
    assert sensors["sensor_bean_container"].options == [
        "not_present",
        "not_fully_inserted",
        "empty",
        "nearly_empty",
        "ok",
    ]
    assert tuple(entity.split(".")[-1] for entity in sensors["sensor_bean_container"].entities) == (
        "BeanContainerIsNotPresent",
        "BeanContainerNotFullyInserted",
        "BeanContainerEmpty",
        "BeanContainerNearlyEmpty",
    )
    assert sensors["sensor_pomace_container"].options == ["missing", "full", "ok"]


async def test_water_tank_sensor_survives_a_partial_profile(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A profile without every water event still gets the sensor with the events it has."""
    sensors = await _sensors(mock_homeconnect_appliance, "WaterTankEmpty", "WaterTankNotInserted")
    assert sensors["sensor_water_tank"].options == ["empty", "not_inserted", "full"]


async def test_no_container_sensors_without_coffee_maker_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Other appliances get none of them."""
    appliance = await mock_homeconnect_appliance(description=DeviceDescription())
    keys = {item.key for item in get_available_entities(appliance)["event_sensor"]}
    assert not keys & {"sensor_water_tank", "sensor_bean_container", "sensor_pomace_container"}
