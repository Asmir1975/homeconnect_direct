"""Join zone sensor follows the option the hob reports."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

OPTION = "Cooking.Hob.Option.JoinZone"
KEY = "binary_sensor_hob_join_zone"


def _description(*names: str) -> DeviceDescription:
    return DeviceDescription(
        option=[
            EntityDescription(uid=5129 + index, name=name, protocolType="Boolean")
            for index, name in enumerate(names)
        ]
    )


def _sensor_description(available: dict) -> object | None:
    return next((item for item in available["binary_sensor"] if item.key == KEY), None)


async def test_sensor_created_with_the_option(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A hob with the option (EX851LYV5E) gets the sensor."""
    appliance = await mock_homeconnect_appliance(description=_description(OPTION))
    description = _sensor_description(get_available_entities(appliance))
    assert description is not None
    assert description.entity == OPTION


async def test_no_sensor_without_the_option(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Appliances without the option get no sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_description("Cooking.Hob.Option.ZoneSelector")
    )
    assert _sensor_description(get_available_entities(appliance)) is None


async def test_sensor_follows_the_option(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The sensor is on while zones are joined, as in the log of the EX851LYV5E."""
    appliance = await mock_homeconnect_appliance(description=_description(OPTION))
    appliance.info = {"deviceID": "test_hob"}
    available = get_available_entities(appliance)
    runtime = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    sensor = HCBinarySensor(_sensor_description(available), runtime)
    await appliance.entities[OPTION].update({"value": False})
    assert not sensor.is_on
    await appliance.entities[OPTION].update({"value": True})
    assert sensor.is_on
