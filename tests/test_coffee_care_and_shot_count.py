"""CoffeeMaker care-program filter and read-only shot count."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from custom_components.homeconnect_ws import entity_descriptions

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

CARE = "ConsumerProducts.CoffeeMaker.Program.CleaningModes."


@pytest.fixture
def description() -> dict:
    """EQ700 description plus one available and one unavailable care program."""
    data = json.loads((Path(__file__).parent / "fixtures/eq700_quantity.json").read_text())
    template = data["program"][0]
    top = max(item["uid"] for item in data["program"])
    for offset, (name, available) in enumerate((("Clean", True), ("SpecialRinsing", False)), 1):
        program = deepcopy(template)
        program.update({"uid": top + offset, "name": CARE + name, "available": available})
        data["program"].append(program)
    fill = next(item for item in data["option"] if item["name"].endswith("FillQuantity"))
    shot = deepcopy(fill)
    shot.update(
        {
            "uid": max(item["uid"] for item in data["option"]) + 1,
            "name": "ConsumerProducts.CoffeeMaker.Option.Shot.Count",
            "access": "read",
            "enumeration": {"10": "Double", "20": "Triple"},
        }
    )
    for key in ("min", "max", "stepSize", "default"):
        shot.pop(key, None)
    data["option"].append(shot)
    return data


async def test_unavailable_care_programs_are_not_offered(
    description: dict, mock_homeconnect_appliance: MockApplianceType
) -> None:
    """The appliance app hides them, so the program select does too."""
    appliance = await mock_homeconnect_appliance(description=description)
    available = entity_descriptions.get_available_entities(appliance)
    mapping = available["program"][0].mapping
    assert CARE + "Clean" in mapping
    assert CARE + "SpecialRinsing" not in mapping
    # The appliance runs some of these itself, so the active program sensor must know them.
    assert CARE + "SpecialRinsing" in available["active_program"][0].mapping

    description["info"]["type"] = "Dishwasher"
    appliance = await mock_homeconnect_appliance(description=description)
    mapping = entity_descriptions.get_available_entities(appliance)["program"][0].mapping
    assert CARE + "SpecialRinsing" in mapping


async def test_shot_count_is_a_sensor_not_a_select(
    description: dict, mock_homeconnect_appliance: MockApplianceType
) -> None:
    """The option is read-only on every known profile, so it is no dropdown."""
    appliance = await mock_homeconnect_appliance(description=description)
    available = entity_descriptions.get_available_entities(appliance)
    assert any(item.key == "sensor_shot_count" for item in available["sensor"])
    assert not any(item.key == "select_shot_count" for item in available["select"])
