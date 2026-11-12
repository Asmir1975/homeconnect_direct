"""Energy saving writes and sanitized completion states use existing entity behavior."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.binary_sensor import HCBinarySensor
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.switch import HCSwitch
from homeassistant.exceptions import ServiceValidationError
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

ENERGY = "Dishcare.Dishwasher.Option.EnergySafe"
SANITIZED = "Dishcare.Dishwasher.Event.ProgramFinishedSanitized"


async def test_energy_option_write_and_read_only_state(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An energy option locked during a program stays readable but rejects writes."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            option=[
                EntityDescription(
                    uid=101,
                    name=ENERGY,
                    protocolType="Boolean",
                    available=True,
                    access=Access.READ_WRITE,
                )
            ],
        )
    )
    descriptions = get_available_entities(appliance)["switch"]
    assert len(descriptions) == 1
    switch = HCSwitch(
        descriptions[0],
        SimpleNamespace(
            appliance=appliance,
            coordinator=MagicMock(connected=True),
            device_info={},
        ),
    )
    await appliance.entities[ENERGY].update({"value": False})
    assert not switch.is_on
    await switch.async_turn_on()
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": True})
    )
    appliance.session.send_sync.reset_mock()
    await appliance.entities[ENERGY].update({"value": True, "access": "read"})
    assert switch.available
    assert switch.is_on
    assert switch.extra_state_attributes["readonly"]
    with pytest.raises(ServiceValidationError):
        await switch.async_turn_off()
    appliance.session.send_sync.assert_not_awaited()
    await appliance.entities[ENERGY].update({"access": "readwrite"})
    await switch.async_turn_off()
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": False})
    )
    await appliance.entities[ENERGY].update({"available": False})
    assert not switch.available


async def test_sanitized_completion_event_lifecycle(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Present/Confirmed mean sanitized completion; Off clears the indication."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            event=[
                EntityDescription(
                    uid=102,
                    name=SANITIZED,
                    protocolType="Integer",
                    enumeration={"0": "Off", "1": "Present", "2": "Confirmed"},
                )
            ],
        )
    )
    descriptions = get_available_entities(appliance)["binary_sensor"]
    assert len(descriptions) == 1
    sensor = HCBinarySensor(
        descriptions[0],
        SimpleNamespace(
            appliance=appliance,
            coordinator=MagicMock(connected=True),
            device_info={},
        ),
    )
    assert sensor.is_on is None
    for raw, expected in ((0, False), (1, True), (2, True), (0, False)):
        await appliance.entities[SANITIZED].update({"value": raw})
        assert sensor.available
        assert sensor.is_on is expected
    appliance.session.send_sync.assert_not_awaited()


async def test_missing_features_create_no_entities(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Other dishwashers retain their existing entities."""
    appliance = await mock_homeconnect_appliance(description=DeviceDescription())
    descriptions = get_available_entities(appliance)
    assert not descriptions["switch"]
    assert not descriptions["binary_sensor"]
