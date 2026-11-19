"""Local and remote control status sensors follow the status the appliance reports."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

CASES = [
    ("binary_local_control_active", "BSH.Common.Status.LocalControlActive"),
    ("binary_remote_control_active", "BSH.Common.Status.RemoteControlActive"),
]


def _description(*names: str) -> DeviceDescription:
    return DeviceDescription(
        status=[
            EntityDescription(uid=517 + index, name=name, protocolType="Boolean")
            for index, name in enumerate(names)
        ]
    )


def _sensor_description(available: dict, key: str) -> object | None:
    return next((item for item in available["binary_sensor"] if item.key == key), None)


@pytest.mark.parametrize(("key", "status"), CASES)
async def test_sensor_created_with_the_status(
    mock_homeconnect_appliance: MockApplianceType, key: str, status: str
) -> None:
    """A profile with the status gets the sensor, disabled by default."""
    appliance = await mock_homeconnect_appliance(description=_description(status))
    description = _sensor_description(get_available_entities(appliance), key)
    assert description is not None
    assert description.entity == status
    assert description.force_disabled_default


@pytest.mark.parametrize(("key", "status"), CASES)
async def test_no_sensor_without_the_status(
    mock_homeconnect_appliance: MockApplianceType,
    key: str,
    status: str,  # noqa: ARG001
) -> None:
    """Appliances without the status get no sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_description("BSH.Common.Status.OperationState")
    )
    assert _sensor_description(get_available_entities(appliance), key) is None


@pytest.mark.parametrize(("key", "status"), CASES)
async def test_sensor_follows_the_status(
    mock_homeconnect_appliance: MockApplianceType, key: str, status: str
) -> None:
    """The sensor is on while the appliance reports the status as true."""
    appliance = await mock_homeconnect_appliance(description=_description(status))
    appliance.info = {"deviceID": "test_oven"}
    available = get_available_entities(appliance)
    runtime = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    sensor = HCBinarySensor(_sensor_description(available, key), runtime)
    await appliance.entities[status].update({"value": False})
    assert not sensor.is_on
    await appliance.entities[status].update({"value": True})
    assert sensor.is_on
