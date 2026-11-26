"""The reject button declines the oven's question for subsequent cooking."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.button import HCButton
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeassistant.exceptions import HomeAssistantError
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

QUESTION = "Cooking.Oven.Event.Cavity.001.SubsequentCookingRequest"
FIXTURE = Path(__file__).parent / "fixtures" / "hb774g1b1_oven.json"


async def _button(mock_homeconnect_appliance: MockApplianceType) -> tuple[HCButton, object]:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(data["entry_data"]["description"])
    )
    appliance.info = {"deviceID": "test_device_id", "type": "Oven"}
    available = get_available_entities(appliance)
    description = next(i for i in available["button"] if i.key == "button_reject_event")
    assert description.force_disabled_default
    runtime_data = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=SimpleNamespace(),
    )
    button = HCButton(description, runtime_data)
    button._entity.set_value = AsyncMock()
    return button, appliance


async def test_press_declines_the_pending_question(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Pressing sends the uid of the question for subsequent cooking."""
    button, appliance = await _button(mock_homeconnect_appliance)
    await appliance.entities[QUESTION].update({"value": 1})
    await button.async_press()
    button._entity.set_value.assert_awaited_once_with(6117)


async def test_press_ignores_other_pending_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Without the question nothing is sent, not even with another event waiting."""
    button, appliance = await _button(mock_homeconnect_appliance)
    await appliance.entities[QUESTION].update({"value": 0})
    await appliance.entities["Cooking.Oven.Event.Cavity.001.RegularPreheatFinished"].update(
        {"value": 1}
    )
    with pytest.raises(HomeAssistantError):
        await button.async_press()
    button._entity.set_value.assert_not_awaited()


def _commands() -> list[dict]:
    return [
        EntityDescription(uid=uid, name=name, available=True, access=Access.WRITE_ONLY)
        for uid, name in (
            (6, "BSH.Common.Command.AcknowledgeEvent"),
            (16, "BSH.Common.Command.RejectEvent"),
        )
    ]


def _events(*events: tuple[int, str, str]) -> list[dict]:
    enumeration = {"0": "Off", "1": "Present", "2": "Confirmed"}
    return [
        EntityDescription(uid=uid, name=name, handling=handling, enumeration=enumeration)
        for uid, name, handling in events
    ]


async def _from_description(
    mock_homeconnect_appliance: MockApplianceType, description: dict, appliance_type: str = "Oven"
) -> tuple[list, object]:
    appliance = await mock_homeconnect_appliance(description=DeviceDescription(description))
    appliance.info = {"deviceID": "test_device_id", "type": appliance_type}
    available = get_available_entities(appliance)
    return [i for i in available["button"] if i.key == "button_reject_event"], appliance


@pytest.mark.parametrize("state", [0, 2])
async def test_press_without_open_question_raises(
    mock_homeconnect_appliance: MockApplianceType, state: int
) -> None:
    """Off and Confirmed leave nothing to reject."""
    button, appliance = await _button(mock_homeconnect_appliance)
    await appliance.entities[QUESTION].update({"value": state})
    with pytest.raises(HomeAssistantError):
        await button.async_press()
    button._entity.set_value.assert_not_awaited()


async def test_oven_without_cavity_names(mock_homeconnect_appliance: MockApplianceType) -> None:
    """An oven that names its events without a cavity gets the button as well."""
    question = "Cooking.Oven.Event.SubsequentCookingRequest"
    buttons, appliance = await _from_description(
        mock_homeconnect_appliance,
        {"command": _commands(), "event": _events((100, question, "decision"))},
    )
    assert len(buttons) == 1
    await appliance.entities[question].update({"value": 1})
    runtime_data = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions={},
        coordinator=SimpleNamespace(),
    )
    button = HCButton(buttons[0], runtime_data)
    button._entity.set_value = AsyncMock()
    await button.async_press()
    button._entity.set_value.assert_awaited_once_with(100)


async def test_other_decisions_are_not_rejected(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A waiting descaling question stays untouched."""
    descaling = "Cooking.Oven.Event.Cavity.001.DescalingRequest"
    buttons, appliance = await _from_description(
        mock_homeconnect_appliance,
        {
            "command": _commands(),
            "event": _events((1, descaling, "decision"), (6117, QUESTION, "decision")),
        },
    )
    await appliance.entities[descaling].update({"value": 1})
    await appliance.entities[QUESTION].update({"value": 0})
    runtime_data = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions={},
        coordinator=SimpleNamespace(),
    )
    button = HCButton(buttons[0], runtime_data)
    button._entity.set_value = AsyncMock()
    with pytest.raises(HomeAssistantError):
        await button.async_press()
    button._entity.set_value.assert_not_awaited()


async def test_no_button_without_the_question(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Without the question in the profile there is nothing to reject."""
    preheat = "Cooking.Oven.Event.Cavity.001.RegularPreheatFinished"
    buttons, _ = await _from_description(
        mock_homeconnect_appliance,
        {"command": _commands(), "event": _events((6123, preheat, "acknowledge"))},
    )
    assert buttons == []


@pytest.mark.parametrize(
    ("fixture", "appliance_type"),
    [
        ("lc91klt60_hood", "Hood"),
        ("tq703d07_coffeemaker", "CoffeeMaker"),
        ("sx63hx52be_dishwasher", "Dishwasher"),
        ("ex851lyv5e_hob", "Hob"),
    ],
)
async def test_no_button_on_other_appliances(
    mock_homeconnect_appliance: MockApplianceType, fixture: str, appliance_type: str
) -> None:
    """Only ovens get the button."""
    path = FIXTURE.parent / f"{fixture}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    buttons, _ = await _from_description(
        mock_homeconnect_appliance, data["entry_data"]["description"], appliance_type
    )
    assert buttons == []
