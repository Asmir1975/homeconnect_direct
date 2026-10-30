"""SelectedProgram write on an oven whose description sets fullOptionSet."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws import HCData, entity_descriptions
from custom_components.homeconnect_ws.helpers import write_through_selected_program
from custom_components.homeconnect_ws.select import HCProgram
from homeassistant.const import CONF_DESCRIPTION
from homeassistant.exceptions import HomeAssistantError
from homeconnect_websocket.errors import CodeResponsError
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeconnect_websocket import HomeAppliance
    from homeconnect_websocket.testutils import MockApplianceType

HOT_AIR = "Cooking.Oven.Program.HeatingMode.HotAir"
MICRO_HOT_AIR = "Cooking.Oven.Program.MicroCombiModes.HotAir"
SUBSEQUENT_COOKING = "Cooking.Oven.Program.Dish.SubsequentCooking"
DURATION_OPTION = "BSH.Common.Option.Duration"
SETPOINT_TEMPERATURE = 5120
MICROWAVE_POWER = 5124
DURATION = 548
FAST_PRE_HEAT = 5123
START_IN_RELATIVE = 558
REQUIRED = {SETPOINT_TEMPERATURE, DURATION}

FULL_SET = [
    {"uid": SETPOINT_TEMPERATURE, "value": 160},
    {"uid": DURATION, "value": 60},
    {"uid": FAST_PRE_HEAT, "value": False},
    {"uid": START_IN_RELATIVE, "value": 0},
]


@pytest.fixture
def oven_description() -> dict:
    """Load the CM836GNB6 device description (three programs, credential-free)."""
    return json.loads((Path(__file__).parent / "fixtures/cm836gnb6_select.json").read_text())


def runtime_of(appliance: HomeAppliance, description: dict) -> HCData:
    """Make the runtime data with the actual saved description available."""
    coordinator = MagicMock(connected=True)
    coordinator.config_entry.data = {CONF_DESCRIPTION: description}
    coordinator.config_entry.options = {}
    return HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=entity_descriptions.get_available_entities(appliance),
        coordinator=coordinator,
    )


def program_select(appliance: HomeAppliance, description: dict) -> HCProgram:
    """Make the program select."""
    runtime = runtime_of(appliance, description)
    return HCProgram(runtime.available_entity_descriptions["program"][0], runtime)


def oven_answering(appliance: HomeAppliance, rule: Callable[[set[int]], int | None]) -> None:
    """Answer a SelectedProgram write with the code the rule returns for the sent uids."""

    async def send_sync(message: Message) -> None:
        if message.resource == "/ro/selectedProgram":
            sent = {option["uid"] for option in message.data["options"]}
            if code := rule(sent):
                raise CodeResponsError(code, message.resource)

    appliance.session.send_sync.side_effect = send_sync


def label_of(select: HCProgram, program: str) -> str:
    """Option label the select shows for a program."""
    return select._labels()[program]


def sent_options(appliance: HomeAppliance) -> list[list[dict]]:
    """Return the options of every message the appliance received."""
    return [call.args[0].data["options"] for call in appliance.session.send_sync.await_args_list]


async def test_oven_with_full_option_set_gets_profile_defaults(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Send the writable defaults, whole numbers as integers like the number entities."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    oven_answering(appliance, lambda sent: None if sent >= REQUIRED else 526)
    select = program_select(appliance, oven_description)

    await select.async_select_option(label_of(select, HOT_AIR))

    (options,) = sent_options(appliance)
    # Dict equality alone would consider 160.0 equal to 160.
    assert json.dumps(options) == json.dumps(FULL_SET)


async def test_empty_option_list_is_rejected_like_in_the_report(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The simulated oven refuses the old payload, so the test above proves the change."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    oven_answering(appliance, lambda sent: None if sent >= REQUIRED else 526)

    with pytest.raises(CodeResponsError):
        await appliance.programs[HOT_AIR].select(override_options=True)


async def test_any_error_is_raised_after_a_single_attempt(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """No retry with other options, the error reaches the user."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    oven_answering(appliance, lambda _sent: 400)
    select = program_select(appliance, oven_description)

    with pytest.raises(HomeAssistantError):
        await select.async_select_option(label_of(select, HOT_AIR))

    assert sent_options(appliance) == [FULL_SET]


async def test_oven_without_flag_keeps_empty_option_list(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Ovens that already work send exactly what they sent before."""
    description = deepcopy(oven_description)
    description["selectedProgram"]["fullOptionSet"] = False
    appliance = await mock_homeconnect_appliance(description=description)
    select = program_select(appliance, description)

    await select.async_select_option(label_of(select, HOT_AIR))

    assert sent_options(appliance) == [[]]


async def test_other_appliance_type_with_flag_keeps_empty_option_list(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The flag is only read for ovens, a hob with the flag is not touched."""
    description = deepcopy(oven_description)
    description["info"]["type"] = "Hob"
    appliance = await mock_homeconnect_appliance(description=description)
    select = program_select(appliance, description)

    await select.async_select_option(label_of(select, HOT_AIR))

    assert sent_options(appliance) == [[]]


async def test_default_falls_back_to_the_option_definition(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """MicrowavePower has no default in the program, only on the option itself."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    select = program_select(appliance, oven_description)

    await select.async_select_option(label_of(select, MICRO_HOT_AIR))

    assert {"uid": MICROWAVE_POWER, "value": 9} in sent_options(appliance)[0]


async def test_program_without_any_default_keeps_empty_option_list(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Never guess a value the profile does not give."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    select = program_select(appliance, oven_description)

    await select.async_select_option(label_of(select, SUBSEQUENT_COOKING))

    assert sent_options(appliance) == [[]]


async def select_hot_air_on_device(appliance: HomeAppliance) -> None:
    """Report HotAir as selected with its option values, like the oven does."""
    await appliance._message_handler(
        Message(
            resource="/ro/values",
            action=Action.NOTIFY,
            data=[
                {"uid": 257, "value": 8208},
                {"uid": SETPOINT_TEMPERATURE, "value": 160},
                {"uid": DURATION, "value": 60},
                {"uid": FAST_PRE_HEAT, "value": False},
                {"uid": START_IN_RELATIVE, "value": 0},
            ],
        )
    )


async def test_option_change_is_written_with_the_selected_program(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The oven answers 527 to a single value, so the whole set goes out with the new value."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    await select_hot_air_on_device(appliance)
    runtime = runtime_of(appliance, oven_description)

    handled = await write_through_selected_program(runtime, appliance.options[DURATION_OPTION], 600)

    assert handled
    (options,) = sent_options(appliance)
    assert json.dumps(options) == json.dumps(
        [{"uid": SETPOINT_TEMPERATURE, "value": 160}, {"uid": DURATION, "value": 600}]
    )


async def test_option_change_needs_a_selected_oven_program_with_the_flag(
    oven_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """No selected program or no flag: nothing is written."""
    appliance = await mock_homeconnect_appliance(description=oven_description)
    runtime = runtime_of(appliance, oven_description)
    duration = appliance.options[DURATION_OPTION]

    assert not await write_through_selected_program(runtime, duration, 600)

    description = deepcopy(oven_description)
    description["selectedProgram"]["fullOptionSet"] = False
    appliance = await mock_homeconnect_appliance(description=description)
    await select_hot_air_on_device(appliance)

    assert not await write_through_selected_program(
        runtime_of(appliance, description), appliance.options[DURATION_OPTION], 600
    )
    assert sent_options(appliance) == []
