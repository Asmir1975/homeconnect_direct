"""Remote start allowed sensor follows the status the dishwasher reports."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

STATUS = "BSH.Common.Status.RemoteControlStartAllowed"
KEY = "binary_remote_start_allowed"


def _description(*names: str) -> DeviceDescription:
    return DeviceDescription(
        status=[
            EntityDescription(uid=517 + index, name=name, protocolType="Boolean")
            for index, name in enumerate(names)
        ]
    )


def _sensor_description(available: dict) -> object | None:
    return next((item for item in available["binary_sensor"] if item.key == KEY), None)


async def test_sensor_created_with_the_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A profile with the status (SX63HX52BE) gets the sensor, disabled by default."""
    appliance = await mock_homeconnect_appliance(description=_description(STATUS))
    description = _sensor_description(get_available_entities(appliance))
    assert description is not None
    assert description.entity == STATUS
    assert description.force_disabled_default


async def test_no_sensor_without_the_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Appliances without the status get no sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_description("BSH.Common.Status.RemoteControlActive")
    )
    assert _sensor_description(get_available_entities(appliance)) is None


async def test_sensor_follows_the_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The sensor is on while remote start is allowed, as in the log of the SX63HX52BE."""
    appliance = await mock_homeconnect_appliance(description=_description(STATUS))
    appliance.info = {"deviceID": "test_dishwasher"}
    available = get_available_entities(appliance)
    runtime = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    sensor = HCBinarySensor(_sensor_description(available), runtime)
    await appliance.entities[STATUS].update({"value": False})
    assert not sensor.is_on
    await appliance.entities[STATUS].update({"value": True})
    assert sensor.is_on
