"""CoffeeMaker bean container and tray event coverage on a profile-shaped mock."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from custom_components.homeconnect_ws import HCData
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.sensor import HCEventSensor
from homeconnect_websocket.entities import DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType


EVENTS = (
    "BeanContainerNearlyEmpty",
    "RefillEmptyBeanContainer",
    "BeanContainerIsNotPresent",
    "BeanContainerNotFullyInserted",
    "PomaceCaveFull",
    "PomaceContainerMissing",
    "DripTrayOverFull",
)
PREFIX = "ConsumerProducts.CoffeeMaker.Event."


async def test_coffee_messages_exist_only_for_profile_events(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A profile without these events has no sensor; a partial profile only reports its own."""
    empty = await mock_homeconnect_appliance(description=DeviceDescription())
    assert not any(
        item.key == "sensor_eq700_messages"
        for item in get_available_entities(empty)["event_sensor"]
    )

    partial = await mock_homeconnect_appliance(
        description=DeviceDescription(
            event=[
                EntityDescription(
                    uid=4627,
                    name=PREFIX + "BeanContainerNearlyEmpty",
                    enumeration={"0": "Off", "1": "Present", "2": "Confirmed"},
                )
            ]
        )
    )
    descriptions = [
        item
        for item in get_available_entities(partial)["event_sensor"]
        if item.key == "sensor_eq700_messages"
    ]
    assert len(descriptions) == 1
    assert tuple(descriptions[0].entities) == (PREFIX + "BeanContainerNearlyEmpty",)
    assert not descriptions[0].force_disabled_default


async def test_coffee_messages_keep_simultaneous_event_values(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """All seven iQ700 events are observable even when more than one is active."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            event=[
                EntityDescription(
                    uid=4627 + index,
                    name=PREFIX + event,
                    enumeration={"0": "Off", "1": "Present", "2": "Confirmed"},
                )
                for index, event in enumerate(EVENTS)
            ]
        )
    )
    appliance.info = {"deviceID": "test_coffeemaker"}
    available = get_available_entities(appliance)
    description = next(
        item for item in available["event_sensor"] if item.key == "sensor_eq700_messages"
    )
    runtime = HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=available,
        coordinator=MagicMock(),
    )
    sensor = HCEventSensor(description, runtime)
    assert sensor.native_value == "none"

    await appliance.entities[PREFIX + "BeanContainerNearlyEmpty"].update({"value": 1})
    await appliance.entities[PREFIX + "PomaceCaveFull"].update({"value": 1})
    assert sensor.native_value == "bean_container_nearly_empty"
    assert sensor.extra_state_attributes["BeanContainerNearlyEmpty"] == "Present"
    assert sensor.extra_state_attributes["PomaceCaveFull"] == "Present"
    assert len(sensor.extra_state_attributes) == 7

    await appliance.entities[PREFIX + "BeanContainerNearlyEmpty"].update({"value": 0})
    assert sensor.native_value == "pomace_cave_full"


def test_coffee_translations_have_issue_programs_and_events() -> None:
    """Both languages cover iQ700-only programs and all message states."""
    translations = Path(__file__).parents[1] / "custom_components/homeconnect_ws/translations"
    program_suffixes = (
        "babyccino",
        "coffeepot",
        "xlamericano",
        "xlcappuccino",
        "xlhotwater",
        "xllattemacchiato",
    )
    for lang in ("de", "en"):
        data = json.loads((translations / f"{lang}.json").read_text())
        entities = data["entity"]
        for kind, key in (("select", "select_program"), ("sensor", "sensor_active_program")):
            states = entities[kind][key]["state"]
            assert all(
                "consumerproducts_coffeemaker_program_beverage_" + suffix in states
                for suffix in program_suffixes
            )
        message_states = entities["sensor"]["sensor_eq700_messages"]["state"]
        assert set(message_states) >= {
            "bean_container_nearly_empty",
            "refill_empty_bean_container",
            "bean_container_not_present",
            "bean_container_not_fully_inserted",
            "pomace_cave_full",
            "pomace_container_missing",
            "drip_tray_over_full",
            "none",
        }
