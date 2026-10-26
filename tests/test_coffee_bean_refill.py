"""Bean container sensor follows the empty event and the refill request."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

PREFIX = "ConsumerProducts.CoffeeMaker.Event."
EVENT_ENUM = {"0": "Off", "1": "Present", "2": "Confirmed"}
KEY = "binary_sensor_bean_container_empty"


def _description(*names: str) -> DeviceDescription:
    return DeviceDescription(
        event=[
            EntityDescription(uid=4600 + index, name=PREFIX + name, enumeration=EVENT_ENUM)
            for index, name in enumerate(names)
        ]
    )


def _sensor_description(available: dict) -> object | None:
    return next((item for item in available["binary_sensor"] if item.key == KEY), None)


async def test_both_events_are_watched(mock_homeconnect_appliance: MockApplianceType) -> None:
    """The empty event and the refill request share one sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_description("BeanContainerEmpty", "RefillEmptyBeanContainer")
    )
    description = _sensor_description(get_available_entities(appliance))
    assert tuple(description.entities) == (
        PREFIX + "BeanContainerEmpty",
        PREFIX + "RefillEmptyBeanContainer",
    )


async def test_only_the_refill_request_is_enough(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A profile with the refill request alone still gets the sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_description("RefillEmptyBeanContainer")
    )
    description = _sensor_description(get_available_entities(appliance))
    assert tuple(description.entities) == (PREFIX + "RefillEmptyBeanContainer",)


async def test_no_sensor_without_bean_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Appliances without either event get no bean container sensor."""
    appliance = await mock_homeconnect_appliance(description=_description("DripTrayFull"))
    assert _sensor_description(get_available_entities(appliance)) is None


async def test_refill_request_turns_the_sensor_on(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The sensor reads empty while the appliance asks for beans and full afterwards."""
    appliance = await mock_homeconnect_appliance(
        description=_description("BeanContainerEmpty", "RefillEmptyBeanContainer")
    )
    appliance.info = {"deviceID": "test_coffeemaker"}
    available = get_available_entities(appliance)
    runtime = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    sensor = HCBinarySensor(_sensor_description(available), runtime)
    assert not sensor.is_on
    await appliance.entities[PREFIX + "RefillEmptyBeanContainer"].update({"value": 1})
    assert sensor.is_on
    await appliance.entities[PREFIX + "RefillEmptyBeanContainer"].update({"value": 0})
    assert not sensor.is_on
