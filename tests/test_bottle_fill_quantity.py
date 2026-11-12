"""Bottle-fill quantities use live bounds and reject unsupported unit modes."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.number import HCNumber
from homeassistant.const import UnitOfVolume
from homeassistant.exceptions import ServiceValidationError
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

QUANTITY = "Refrigeration.Common.Setting.Dispenser.BottleFillQuantity"
UNIT = "BSH.Common.Setting.LiquidVolumeUnit"


async def test_quantity_grid_and_unit_changes(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Send only valid mL values, including when a stale UI races a unit change."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            setting=[
                EntityDescription(
                    uid=101,
                    name=QUANTITY,
                    protocolType="Integer",
                    access=Access.READ_WRITE,
                    available=True,
                    min=200,
                    max=1000,
                    stepSize=50,
                ),
                EntityDescription(
                    uid=102,
                    name=UNIT,
                    protocolType="Integer",
                    access=Access.READ_WRITE,
                    available=True,
                    enumeration={"0": "MilliLiter", "1": "FluidOunces"},
                ),
            ],
        )
    )
    descriptions = get_available_entities(appliance)["number"]
    assert len(descriptions) == 1
    number = HCNumber(
        descriptions[0],
        SimpleNamespace(
            appliance=appliance,
            coordinator=MagicMock(connected=True),
            device_info={},
        ),
    )
    assert not number.entity_registry_enabled_default
    assert not number.available  # The unit is not known until the first live update.
    await appliance.entities[QUANTITY].update({"value": 400})
    await appliance.entities[UNIT].update({"value": 0})
    assert number.available
    assert number.native_value == 400
    assert number.native_unit_of_measurement == UnitOfVolume.MILLILITERS
    assert (number.native_min_value, number.native_max_value) == (200, 1000)
    assert appliance.entities[UNIT] in number._entities

    await number.async_set_native_value(500)
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": 500})
    )
    appliance.session.send_sync.reset_mock()
    with pytest.raises(ServiceValidationError) as error:
        await number.async_set_native_value(525)
    assert error.value.translation_key == "invalid_step"
    appliance.session.send_sync.assert_not_awaited()

    await appliance.entities[UNIT].update({"value": 1})
    assert not number.available
    with pytest.raises(ServiceValidationError) as error:
        await number.async_set_native_value(500)
    assert error.value.translation_key == "bottle_fill_requires_milliliters"
    appliance.session.send_sync.assert_not_awaited()

    await appliance.entities[UNIT].update({"value": 0})
    await appliance.entities[QUANTITY].update({"min": 300, "max": 900, "stepSize": 100})
    assert number.available
    assert (number.native_min_value, number.native_max_value) == (300, 900)
    with pytest.raises(ServiceValidationError):
        await number.async_set_native_value(450)
    appliance.session.send_sync.assert_not_awaited()
    await number.async_set_native_value(600)
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": 600})
    )


@pytest.mark.parametrize("missing", [QUANTITY, UNIT])
async def test_incomplete_profiles_do_not_create_quantity(
    mock_homeconnect_appliance: MockApplianceType, missing: str
) -> None:
    """Do not guess the unit if the appliance does not expose its unit setting."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            setting=[
                EntityDescription(uid=101, name=name)
                for name in (QUANTITY, UNIT)
                if name != missing
            ],
        )
    )
    assert not get_available_entities(appliance)["number"]
