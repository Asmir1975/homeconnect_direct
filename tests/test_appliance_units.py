"""Unit selectors discover two choices and write the corresponding enum value."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.select import HCSelect
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType


@pytest.mark.parametrize(
    ("feature", "choices"),
    [
        ("TemperatureUnit", ("Celsius", "Fahrenheit")),
        ("LiquidVolumeUnit", ("MilliLiter", "FluidOunces")),
    ],
)
async def test_two_unit_choices_and_write(
    mock_homeconnect_appliance: MockApplianceType, feature: str, choices: tuple[str, str]
) -> None:
    """The appliance's display unit is independent of Home Assistant's display unit."""
    name = "BSH.Common.Setting." + feature
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            setting=[
                EntityDescription(
                    uid=101,
                    name=name,
                    access=Access.READ_WRITE,
                    available=True,
                    protocolType="Integer",
                    enumeration={"0": choices[0], "1": choices[1]},
                )
            ],
        )
    )
    descriptions = get_available_entities(appliance)["select"]
    assert len(descriptions) == 1
    select = HCSelect(
        descriptions[0],
        SimpleNamespace(
            appliance=appliance,
            coordinator=MagicMock(connected=True),
            device_info={},
        ),
    )
    assert select.options == [choice.lower() for choice in choices]
    await appliance.entities[name].update({"value": 0})
    assert select.current_option == choices[0].lower()
    await select.async_select_option(choices[1].lower())
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 101, "value": 1})
    )
    await appliance.entities[name].update({"value": 1})
    assert select.current_option == choices[1].lower()


@pytest.mark.parametrize("feature", ["TemperatureUnit", "LiquidVolumeUnit"])
@pytest.mark.parametrize("choices", [None, {}, {"0": "OnlyChoice"}])
async def test_no_selector_without_a_choice(
    mock_homeconnect_appliance: MockApplianceType, feature: str, choices: dict | None
) -> None:
    """Missing enums and fixed units must not create an unusable selector."""
    setting = EntityDescription(uid=101, name="BSH.Common.Setting." + feature)
    if choices is not None:
        setting["enumeration"] = choices
    appliance = await mock_homeconnect_appliance(description=DeviceDescription(setting=[setting]))
    assert not get_available_entities(appliance)["select"]


async def test_appliance_without_unit_settings(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Do not create selectors on unrelated appliances."""
    appliance = await mock_homeconnect_appliance(description=DeviceDescription())
    assert not get_available_entities(appliance)["select"]
