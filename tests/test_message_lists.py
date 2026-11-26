"""Message sensors of hobs, washers and dryers, and the order of the oven message list."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.entity_descriptions.common import SOFTWARE_MESSAGES
from custom_components.homeconnect_ws.entity_descriptions.cooking import (
    HOB_MESSAGES,
    OVEN_MESSAGES,
)
from custom_components.homeconnect_ws.entity_descriptions.laundry_care import LAUNDRY_MESSAGES
from custom_components.homeconnect_ws.sensor import HCEventSensor
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

ENUM = {"0": "Off", "1": "Present", "2": "Confirmed"}
TRANSLATIONS = (
    Path(__file__).parent.parent / "custom_components" / "homeconnect_ws" / "translations"
)


def _profile(*names: str) -> DeviceDescription:
    return DeviceDescription(
        event=[
            EntityDescription(uid=uid, name=name, enumeration=ENUM)
            for uid, name in enumerate(names, start=1)
        ]
    )


async def _sensor(
    mock_homeconnect_appliance: MockApplianceType, key: str, *names: str
) -> tuple[HCEventSensor, dict]:
    appliance = await mock_homeconnect_appliance(description=_profile(*names))
    appliance.info = {"deviceID": "test_device_id"}
    available = get_available_entities(appliance)
    description = next(item for item in available["event_sensor"] if item.key == key)
    runtime_data = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    for name in names:
        await appliance.entities[name].update({"value": 0})
    return HCEventSensor(description, runtime_data), appliance.entities


async def test_hob_message_shows_most_urgent_event(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The hob message sensor shows the most urgent active event, else none."""
    overheated = "Cooking.Common.Event.ApplianceOverheated"
    confirm = "Cooking.Common.Event.ConfirmActionAtAppliance"
    sensor, entities = await _sensor(
        mock_homeconnect_appliance, "sensor_hob_message", confirm, overheated
    )
    assert sensor.native_value == "none"
    await entities[confirm].update({"value": 1})
    assert sensor.native_value == "confirm_action_at_appliance"
    await entities[overheated].update({"value": 1})
    assert sensor.native_value == "appliance_overheated"
    await entities[overheated].update({"value": 0})
    assert sensor.native_value == "confirm_action_at_appliance"


async def test_hob_message_shows_preheat_finished(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Preheat finished (uid 53260 in the profile of a T69FUV4L0) is a hob message."""
    preheat = "Cooking.Common.Event.PreheatFinished"
    confirm = "Cooking.Common.Event.ConfirmActionAtAppliance"
    sensor, entities = await _sensor(
        mock_homeconnect_appliance, "sensor_hob_message", preheat, confirm
    )
    assert sensor.native_value == "none"
    await entities[preheat].update({"value": 1})
    assert sensor.native_value == "preheat_finished"
    await entities[confirm].update({"value": 1})
    assert sensor.native_value == "confirm_action_at_appliance"


async def test_dryer_message_shows_drying_finished(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A dryer reports the end of the drying process in the laundry message sensor."""
    finished = "LaundryCare.Dryer.Event.DryingProcessFinished"
    lint = "LaundryCare.Dryer.Event.DryerSelfCleaning.CleanLintFilter"
    sensor, entities = await _sensor(
        mock_homeconnect_appliance, "sensor_laundry_message", finished, lint
    )
    assert sensor.native_value == "none"
    await entities[lint].update({"value": 1})
    assert sensor.native_value == "clean_lint_filter"
    await entities[finished].update({"value": 1})
    assert sensor.native_value == "drying_process_finished"


async def test_no_message_sensor_without_its_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Appliances without any of the events get no hob or laundry message sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_profile("BSH.Common.Event.ProgramFinished")
    )
    appliance.info = {"deviceID": "test_device_id"}
    keys = {item.key for item in get_available_entities(appliance)["event_sensor"]}
    assert not keys & {"sensor_hob_message", "sensor_laundry_message"}


def test_message_states_translated() -> None:
    """Every state of the hob and laundry message sensors has an English and German text."""
    expected = {
        "sensor_hob_message": [key for _, key in (*HOB_MESSAGES, *SOFTWARE_MESSAGES)],
        "sensor_laundry_message": [key for _, key in (*LAUNDRY_MESSAGES, *SOFTWARE_MESSAGES)],
    }
    for language in ("en", "de"):
        translation = json.loads((TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8"))
        for sensor_key, keys in expected.items():
            states = translation["entity"]["sensor"][sensor_key]["state"]
            assert set(states) == {*keys, "none"}, (language, sensor_key)


def test_preheat_finished_comes_before_door_and_food_prompts() -> None:
    """Pre-heat finished sits below the errors and above the door and insert food prompts."""
    order = [event for event, _ in OVEN_MESSAGES]
    preheat = order.index("RegularPreheatFinished")
    assert order.index("ErrorPermanentButtonPressing") < preheat
    assert order.index("FastPreheatFinished") == preheat + 1
    assert preheat < order.index("OpenDoor")
    assert preheat < order.index("InsertFoodNow")


@pytest.mark.parametrize(
    ("fixture", "sensor_key"),
    [
        ("hb774g1b1_oven", "sensor_oven_message_001"),
        ("ex851lyv5e_hob", "sensor_hob_message"),
        ("lc91klt60_hood", "sensor_hood_filter_message"),
        ("sx63hx52be_dishwasher", "sensor_dishwasher_message"),
        ("wgb244a7nl_washer", "sensor_laundry_message"),
        ("wnc244070_washerdryer", "sensor_laundry_message"),
        ("wqb246c7nl_dryer", "sensor_laundry_message"),
    ],
)
async def test_software_update_ends_one_message_sensor(
    mock_homeconnect_appliance: MockApplianceType, fixture: str, sensor_key: str
) -> None:
    """The software update events close the list of exactly one message sensor."""
    path = Path(__file__).parent / "fixtures" / f"{fixture}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(data["entry_data"]["description"])
    )
    appliance.info = {"deviceID": "test_device_id"}
    software = [name for name, _ in SOFTWARE_MESSAGES]
    with_software = [
        item
        for item in get_available_entities(appliance)["event_sensor"]
        if set(software) & set(item.entities)
    ]
    assert [item.key for item in with_software] == [sensor_key]
    assert list(with_software[0].entities[-3:]) == software


async def test_software_update_reaches_washer_without_laundry_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Without own message events the general message sensor shows the software update."""
    software = [name for name, _ in SOFTWARE_MESSAGES]
    sensor, entities = await _sensor(
        mock_homeconnect_appliance,
        "sensor_dishwasher_message",
        "BSH.Common.Event.LowWaterPressure",
        "BSH.Common.Event.ProgramAborted",
        *software,
    )
    await entities[software[0]].update({"value": 1})
    assert sensor.native_value == "software_update_available"
    await entities["BSH.Common.Event.ProgramAborted"].update({"value": 1})
    assert sensor.native_value == "program_aborted"
