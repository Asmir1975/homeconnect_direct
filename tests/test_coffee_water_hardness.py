"""Water hardness of a coffee maker can be set, and is off by default."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

FIXTURES = Path(__file__).parent / "fixtures"
TRANSLATIONS = Path(__file__).parents[1] / "custom_components/homeconnect_ws/translations"


async def test_water_hardness_select_is_disabled_by_default(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Seen on a Siemens TQ703D07: readwrite setting with four values, the sensor stays."""
    fixture = json.loads((FIXTURES / "tq703d07_coffeemaker.json").read_text())
    appliance = await mock_homeconnect_appliance(description=fixture["entry_data"]["description"])
    descriptions = get_available_entities(appliance)
    select = next(d for d in descriptions["select"] if d.key == "select_eq700_water_hardness")
    assert select.force_disabled_default
    assert select.entity == "ConsumerProducts.CoffeeMaker.Setting.WaterHardness"
    assert any(d.key == "sensor_eq700_water_hardness" for d in descriptions["sensor"])


@pytest.mark.parametrize("lang", ["en", "de"])
def test_water_hardness_select_is_translated(lang: str) -> None:
    """Name and all four values have a text."""
    texts = json.loads((TRANSLATIONS / f"{lang}.json").read_text(encoding="utf-8"))
    select = texts["entity"]["select"]["select_eq700_water_hardness"]
    assert select["name"]
    assert set(select["state"]) == {"soft", "medium", "hard", "veryhard"}
