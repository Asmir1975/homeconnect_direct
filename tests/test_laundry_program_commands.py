"""Abort, pause and resume of a washer follow the access field alone."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.button import HCButton
from custom_components.homeconnect_ws.entity_descriptions.descriptions_definitions import (
    HCButtonEntityDescription,
)
from homeassistant.exceptions import HomeAssistantError
from homeconnect_websocket.testutils import MockAppliance

ABORT, PAUSE, RESUME = 512, 537, 546
NAMES = {
    ABORT: "BSH.Common.Command.AbortProgram",
    PAUSE: "BSH.Common.Command.PauseProgram",
    RESUME: "BSH.Common.Command.ResumeProgram",
}


def _buttons(appliance_type: str) -> tuple[MockAppliance, dict[int, HCButton]]:
    """WGB24409FG commands, activeProgram and OperationState from its profile."""
    path = Path(__file__).parent / "fixtures/wgb24409fg_commands.json"
    description = deepcopy(json.loads(path.read_text()))
    description["info"]["type"] = appliance_type
    appliance = MockAppliance(description, "host", "app", "id", "PSK")
    data = HCData(
        appliance=appliance,
        device_info={},
        available_entity_descriptions={},
        coordinator=MagicMock(connected=True),
    )
    buttons = {
        uid: HCButton(HCButtonEntityDescription(key=f"button_{uid}", entity=name), data)
        for uid, name in NAMES.items()
    }
    return appliance, buttons


async def _change(appliance: MockAppliance, *changes: dict) -> None:
    """Replay description changes as the washer sent them."""
    await appliance._update_entities(list(changes))


async def _before_start(appliance: MockAppliance) -> None:
    """Mark the three commands unavailable (assumed state after connect)."""
    await _change(
        appliance,
        {"uid": ABORT, "available": False},
        {"uid": PAUSE, "available": False},
        {"uid": RESUME, "available": False},
    )


def _states(buttons: dict[int, HCButton]) -> list[bool]:
    return [buttons[uid].available for uid in NAMES]


@pytest.mark.parametrize("appliance_type", ["Washer", "Dryer", "WasherDryer"])
async def test_buttons_follow_access_through_pause_and_resume(appliance_type: str) -> None:
    """Idle: off. Run: abort and pause. Pause: abort and resume. Resume: abort and pause."""
    appliance, buttons = _buttons(appliance_type)
    await _before_start(appliance)
    assert _states(buttons) == [False, False, False]

    await _change(appliance, {"uid": ABORT, "access": "WRITEONLY"})
    await _change(appliance, {"uid": PAUSE, "access": "WRITEONLY"})
    assert _states(buttons) == [True, True, False]

    await _change(
        appliance, {"uid": PAUSE, "access": "NONE"}, {"uid": RESUME, "access": "WRITEONLY"}
    )
    assert _states(buttons) == [True, False, True]

    await _change(
        appliance, {"uid": RESUME, "access": "NONE"}, {"uid": PAUSE, "access": "WRITEONLY"}
    )
    assert _states(buttons) == [True, True, False]

    await _change(appliance, {"uid": PAUSE, "access": "NONE"}, {"uid": ABORT, "access": "NONE"})
    assert _states(buttons) == [False, False, False]


async def test_other_appliances_keep_the_available_check() -> None:
    """An oven switches these by available, so access alone must not enable them."""
    appliance, buttons = _buttons("Oven")
    await _change(
        appliance,
        {"uid": PAUSE, "access": "WRITEONLY", "available": False},
        {"uid": RESUME, "access": "WRITEONLY", "available": True},
    )
    assert not buttons[PAUSE].available
    assert buttons[RESUME].available


async def test_press_sends_the_command_although_available_is_false() -> None:
    """The command class refuses this press, the washer accepts it."""
    appliance, buttons = _buttons("Washer")
    await _before_start(appliance)
    await _change(appliance, {"uid": PAUSE, "access": "WRITEONLY"})

    await buttons[PAUSE].async_press()

    sent = appliance.session.send_sync.await_args.args[0]
    assert sent.data == {"uid": PAUSE, "value": True}


async def test_press_without_access_is_refused() -> None:
    """No write access, nothing is sent."""
    appliance, buttons = _buttons("Washer")
    await _before_start(appliance)

    with pytest.raises(HomeAssistantError):
        await buttons[RESUME].async_press()

    appliance.session.send_sync.assert_not_awaited()
