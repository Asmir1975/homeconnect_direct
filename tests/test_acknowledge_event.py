"""AcknowledgeEvent button sends the uid of the event that is waiting."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from custom_components.homeconnect_ws.button import HCButton
from custom_components.homeconnect_ws.entity_descriptions.descriptions_definitions import (
    HCButtonEntityDescription,
)
from custom_components.homeconnect_ws.helpers import pending_acknowledge_event_uid
from homeassistant.const import CONF_DESCRIPTION
from homeassistant.exceptions import HomeAssistantError

PREFIX = "ConsumerProducts.CoffeeMaker.Event."

HANDLING = {
    "CleanBrewingUnitStep1": ("none", "hint"),
    "CleanBrewingUnitStep2": ("acknowledge", "hint"),
    "CleanBrewingUnitStep3": ("acknowledge", "hint"),
    "RefillEmptyWaterTank": ("decision", "hint"),
    "MilkTubeRemoved": ("none", "hint"),
    "HeaterError": ("none", "critical"),
}


def _runtime_data(events: dict[str, tuple[int, str]]) -> SimpleNamespace:
    description = {
        "event": [
            {
                "uid": uid,
                "name": PREFIX + name,
                "handling": HANDLING[name][0],
                "level": HANDLING[name][1],
            }
            for name, (uid, _) in events.items()
        ]
    }
    return SimpleNamespace(
        coordinator=SimpleNamespace(
            config_entry=SimpleNamespace(data={CONF_DESCRIPTION: description})
        ),
        appliance=SimpleNamespace(
            events={
                PREFIX + name: SimpleNamespace(uid=uid, value=value)
                for name, (uid, value) in events.items()
            }
        ),
    )


def test_picks_the_present_acknowledge_event() -> None:
    """Only an event that is Present and wants an acknowledge is picked."""
    runtime_data = _runtime_data(
        {
            "MilkTubeRemoved": (4689, "Off"),
            "RefillEmptyWaterTank": (4700, "Present"),
            "CleanBrewingUnitStep2": (4701, "Off"),
            "CleanBrewingUnitStep3": (4702, "Present"),
        }
    )
    assert pending_acknowledge_event_uid(runtime_data) == 4702


@pytest.mark.parametrize("state", ["Off", "Confirmed"])
def test_nothing_pending(state: str) -> None:
    """Off and Confirmed events need nothing."""
    runtime_data = _runtime_data({"CleanBrewingUnitStep2": (4701, state)})
    assert pending_acknowledge_event_uid(runtime_data) is None


def test_decision_and_plain_events_are_not_acknowledged() -> None:
    """Decision events and events without handling stay out."""
    runtime_data = _runtime_data(
        {"RefillEmptyWaterTank": (4700, "Present"), "CleanBrewingUnitStep1": (4717, "Present")}
    )
    assert pending_acknowledge_event_uid(runtime_data) is None


def _button(runtime_data: SimpleNamespace) -> tuple[HCButton, AsyncMock]:
    button = HCButton.__new__(HCButton)
    button._runtime_data = runtime_data
    button.entity_description = HCButtonEntityDescription(
        key="button_acknowledge_event", press_value=None
    )
    command = AsyncMock()
    button._entity = SimpleNamespace(set_value=command)
    return button, command


async def test_press_sends_the_uid_of_the_pending_event() -> None:
    """Pressing sends the uid of the waiting event."""
    button, command = _button(_runtime_data({"CleanBrewingUnitStep3": (4702, "Present")}))
    await button.async_press()
    command.assert_awaited_once_with(4702)


async def test_press_without_pending_event_raises() -> None:
    """Without a waiting event the press answers with an error and sends nothing."""
    button, command = _button(_runtime_data({"CleanBrewingUnitStep3": (4702, "Off")}))
    with pytest.raises(HomeAssistantError):
        await button.async_press()
    command.assert_not_awaited()
