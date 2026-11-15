"""Steam level and steam boost of an oven, sent with the program start."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from custom_components.homeconnect_ws.entity_descriptions.cooking import (
    COOKING_ENTITY_DESCRIPTIONS,
)
from custom_components.homeconnect_ws.helpers import start_option_running, write_with_start
from homeassistant.exceptions import ServiceValidationError
from homeconnect_websocket.testutils import MockAppliance

LEVEL = "Cooking.Oven.Option.SteamAssistLevel"
BOOST = "Cooking.Oven.Option.SteamBoost"
HOT_AIR = 8208
KEEP_WARM_NAME = "Cooking.Oven.Program.HeatingMode.KeepWarm"
INACTIVE, READY, RUN, PAUSE, ACTION_REQUIRED, FINISHED = 0, 1, 3, 4, 5, 6


async def _oven(operation_state: int, program: int | None = None) -> SimpleNamespace:
    """Build the oven from the HR776G1B1 profile."""
    description = json.loads((Path(__file__).parent / "fixtures/hr776g1b1_steam.json").read_text())
    appliance = MockAppliance(description, "host", "app", "id", "PSK")
    updates = [
        {"uid": 552, "value": operation_state},
        {"uid": 5120, "value": 180},
        {"uid": 548, "value": 120},
        {"uid": 5125, "value": 0},
        {"uid": 5151, "value": False},
    ]
    if program is not None:
        updates.append({"uid": 256, "value": program})
    await appliance._update_entities(updates)
    return SimpleNamespace(appliance=appliance)


def _sent(runtime: SimpleNamespace) -> list:
    return [call.args[0] for call in runtime.appliance.session.send_sync.await_args_list]


def test_both_are_sent_with_the_start() -> None:
    """Neither writes a single value."""
    found = [
        item
        for platform in ("select", "switch")
        for item in COOKING_ENTITY_DESCRIPTIONS[platform]
        if not callable(item) and item.entity in (LEVEL, BOOST)
    ]
    assert {item.entity for item in found} == {LEVEL, BOOST}
    assert all(item.sent_with_start for item in found)


@pytest.mark.parametrize("operation_state", [INACTIVE, READY])
async def test_idle_oven_keeps_the_level_for_the_next_start(operation_state: int) -> None:
    """Nothing is written, the start sends the kept value."""
    runtime = await _oven(operation_state)
    entities = runtime.appliance.entities
    await write_with_start(runtime, entities[LEVEL], 2)
    assert _sent(runtime) == []
    assert entities[LEVEL].value_shadow == 2
    assert entities[BOOST].value_shadow is False
    options = {
        option["uid"]: option["value"]
        for option in runtime.appliance.entities_uid[HOT_AIR]._build_options()
    }
    assert options[5125] == 2


async def test_idle_oven_keeps_either_the_boost_or_a_level() -> None:
    """Seen on HR776G1B1: with the boost the oven reports the level off."""
    runtime = await _oven(READY)
    entities = runtime.appliance.entities
    await write_with_start(runtime, entities[LEVEL], 3)
    await write_with_start(runtime, entities[BOOST], value=True)
    assert (entities[LEVEL].value_shadow, entities[BOOST].value_shadow) == (0, True)
    await write_with_start(runtime, entities[LEVEL], 1)
    assert (entities[LEVEL].value_shadow, entities[BOOST].value_shadow) == (1, False)
    assert _sent(runtime) == []


async def test_running_program_gets_the_start_again() -> None:
    """Seen on HR776G1B1: the same start with other steam values changes the run."""
    runtime = await _oven(RUN, HOT_AIR)
    await write_with_start(runtime, runtime.appliance.entities[LEVEL], 3)
    (message,) = _sent(runtime)
    assert message.resource == "/ro/activeProgram"
    assert message.data == {
        "program": HOT_AIR,
        "options": [
            {"uid": 5120, "value": 180},
            {"uid": 548, "value": 120},
            {"uid": 5125, "value": 3},
            {"uid": 5151, "value": False},
        ],
    }


async def test_running_program_gets_the_boost_without_a_level() -> None:
    """The boost goes out with the level off."""
    runtime = await _oven(RUN, HOT_AIR)
    await runtime.appliance._update_entities([{"uid": 5125, "value": 2}])
    await write_with_start(runtime, runtime.appliance.entities[BOOST], value=True)
    (message,) = _sent(runtime)
    options = {option["uid"]: option["value"] for option in message.data["options"]}
    assert (options[5125], options[5151]) == (0, True)


async def test_running_program_without_the_option_is_refused() -> None:
    """Keep warm has no steam boost in the HR776G1B1 profile."""
    runtime = await _oven(RUN)
    keep_warm = runtime.appliance.entities[KEEP_WARM_NAME]
    await runtime.appliance._update_entities([{"uid": 256, "value": keep_warm.uid}])
    with pytest.raises(ServiceValidationError):
        await write_with_start(runtime, runtime.appliance.entities[BOOST], value=True)
    assert _sent(runtime) == []


@pytest.mark.parametrize(
    ("operation_state", "running"),
    [
        (INACTIVE, False),
        (READY, False),
        (RUN, True),
        (PAUSE, None),
        (ACTION_REQUIRED, None),
        (FINISHED, None),
    ],
)
async def test_only_idle_and_run_take_a_value(operation_state: int, running: bool | None) -> None:  # noqa: FBT001
    """Seen on HR776G1B1: a start after the end of a program went to continue cooking."""
    runtime = await _oven(operation_state)
    assert start_option_running(runtime.appliance) is running
