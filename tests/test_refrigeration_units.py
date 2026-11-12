"""Temperature controls survive profile/live unit mismatches and later changes."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.number import HCNumber
from homeassistant.const import UnitOfTemperature
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType


@pytest.mark.parametrize("compartment", ["Freezer", "Refrigerator", "ChillerCommon"])
async def test_live_unit_changes_keep_both_controls(
    mock_homeconnect_appliance: MockApplianceType, compartment: str
) -> None:
    """Profile Celsius must not prevent Fahrenheit reads/writes after connecting."""
    base = f"Refrigeration.Common.Setting.{compartment}.SetpointTemperature"
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            setting=[
                EntityDescription(
                    uid=101,
                    name=base,
                    protocolType="Integer",
                    available=True,
                    access=Access.READ_WRITE,
                    min=1,
                    max=8,
                    stepSize=1,
                ),
                EntityDescription(
                    uid=102,
                    name=base + "Fahrenheit",
                    protocolType="Integer",
                    available=False,
                    access=Access.READ_WRITE,
                    min=34,
                    max=46,
                    stepSize=1,
                ),
            ],
        )
    )
    descriptions = get_available_entities(appliance)
    runtime = SimpleNamespace(
        appliance=appliance,
        coordinator=MagicMock(connected=True),
        device_info={},
    )
    controls = {
        item.native_unit_of_measurement: HCNumber(item, runtime) for item in descriptions["number"]
    }
    assert set(controls) == {UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT}
    celsius = controls[UnitOfTemperature.CELSIUS]
    fahrenheit = controls[UnitOfTemperature.FAHRENHEIT]
    unique_ids = (celsius.unique_id, fahrenheit.unique_id)

    await appliance.entities[base].update({"available": False, "value": 4})
    await appliance.entities[base + "Fahrenheit"].update({"available": True, "value": 39})
    assert not celsius.available
    assert fahrenheit.available
    assert fahrenheit.native_value == 39
    assert (fahrenheit.native_min_value, fahrenheit.native_max_value) == (34, 46)
    await fahrenheit.async_set_native_value(40)
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 102, "value": 40})
    )

    appliance.session.send_sync.reset_mock()
    await appliance.entities[base].update({"available": True, "value": 5})
    await appliance.entities[base + "Fahrenheit"].update({"available": False})
    assert celsius.available
    assert not fahrenheit.available
    assert celsius.native_value == 5
    await celsius.async_set_native_value(6)
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": 6})
    )
    assert (celsius.unique_id, fahrenheit.unique_id) == unique_ids
