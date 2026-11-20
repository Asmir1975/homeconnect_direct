"""Entity creation for appliances whose diagnostics we have, one fixture per model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

FIXTURES = Path(__file__).parent / "fixtures"
KNOWN_DEVICES = [
    "hb774g1b1_oven",
    "sx63hx52be_dishwasher",
    "ex851lyv5e_hob",
    "lc91klt60_hood",
    "tq703d07_coffeemaker",
    "wnc244070_washerdryer",
]


@pytest.mark.parametrize("name", KNOWN_DEVICES)
async def test_known_device_creates_entities(
    mock_homeconnect_appliance: MockApplianceType, name: str
) -> None:
    """Each known appliance gets entities, and no platform repeats a key."""
    fixture = json.loads((FIXTURES / f"{name}.json").read_text())
    appliance = await mock_homeconnect_appliance(description=fixture["entry_data"]["description"])
    for state in fixture["appliance_state"]["entities"]:
        if state["name"] in appliance.entities and state["value_raw"] is not None:
            await appliance.entities[state["name"]].update({"value": state["value_raw"]})

    descriptions = get_available_entities(appliance)
    assert any(descriptions.values())
    for platform, items in descriptions.items():
        keys = [item.key for item in items]
        assert len(keys) == len(set(keys)), platform
