"""Generic CoffeeMaker quantity choices against sanitized device descriptions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws import HCData, entity_descriptions
from custom_components.homeconnect_ws.coffee_quantity import COFFEE_QUANTITIES, FILL_QUANTITY
from custom_components.homeconnect_ws.number import HCNumber
from custom_components.homeconnect_ws.select import HCCoffeeQuantitySelect
from homeassistant.const import CONF_DESCRIPTION
from homeassistant.exceptions import ServiceValidationError
from homeconnect_websocket.errors import CodeResponsError
from homeconnect_websocket.message import Action, Message

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance
    from homeconnect_websocket.testutils import MockApplianceType


@pytest.fixture
def eq700_description() -> dict:
    """Load the credential-free EQ700 device description."""
    return json.loads((Path(__file__).parent / "fixtures/eq700_quantity.json").read_text())


@pytest.fixture
def ti9555_description() -> dict:
    """Load the TI9555 profile with its conflicting XL default."""
    return json.loads((Path(__file__).parent / "fixtures/ti9555_quantity.json").read_text())


def runtime_for(appliance: HomeAppliance, description: dict) -> HCData:
    """Make runtime data with the actual saved description available."""
    coordinator = MagicMock(connected=True)
    coordinator.config_entry.data = {CONF_DESCRIPTION: description}
    return HCData(
        appliance=appliance,
        device_info=MagicMock(),
        available_entity_descriptions=entity_descriptions.get_available_entities(appliance),
        coordinator=coordinator,
    )


async def test_every_coffeemaker_keeps_active_box_and_gets_one_quantity_select(
    eq700_description: dict,
    ti9555_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Create the same Select and keep the active Number on two models."""
    for description in (eq700_description, ti9555_description):
        appliance = await mock_homeconnect_appliance(description=description)
        available = entity_descriptions.get_available_entities(appliance)
        assert [item.key for item in available["coffee_quantity"]] == [
            "select_coffee_fill_quantity"
        ]
        numbers = [item for item in available["number"] if item.key == "number_fill_quantity"]
        assert len(numbers) == 1
        assert not numbers[0].force_disabled_default

    unknown = json.loads(json.dumps(eq700_description))
    unknown["program"] = [x for x in unknown["program"] if x["name"].endswith("Beverage.Ristretto")]
    appliance = await mock_homeconnect_appliance(description=unknown)
    available = entity_descriptions.get_available_entities(appliance)
    assert len(available["coffee_quantity"]) == 1
    assert any(x.key == "number_fill_quantity" for x in available["number"])

    other = json.loads(json.dumps(eq700_description))
    other["info"]["type"] = "Dishwasher"
    appliance = await mock_homeconnect_appliance(description=other)
    available = entity_descriptions.get_available_entities(appliance)
    assert not available["coffee_quantity"]


async def test_eq700_classics_follow_profile_and_validate_both_write_paths(
    eq700_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Filter and write the eleven EQ700 app grids for both entity paths."""
    appliance = await mock_homeconnect_appliance(description=eq700_description)
    appliance.session.connected = True
    runtime = runtime_for(appliance, eq700_description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    number = HCNumber(
        next(
            x
            for x in runtime.available_entity_descriptions["number"]
            if x.key == "number_fill_quantity"
        ),
        runtime,
    )
    selected = appliance.entities["BSH.Common.Root.SelectedProgram"]
    fill = appliance.entities[FILL_QUANTITY]

    assert len(COFFEE_QUANTITIES) == 11
    for name, values in COFFEE_QUANTITIES.items():
        await selected.update({"value": appliance.programs[name].uid})
        assert quantity.options == [f"{value} ml" for value in values]
        assert quantity.available
        await fill.update({"value": values[0]})
        assert quantity.current_option == f"{values[0]} ml"

    crema = "ConsumerProducts.CoffeeMaker.Program.Beverage.Coffee"
    await selected.update({"value": appliance.programs[crema].uid})
    for call in (quantity.async_select_option("85 ml"), number.async_set_native_value(85)):
        with pytest.raises(ServiceValidationError) as error:
            await call
        assert error.value.translation_key == "invalid_coffee_quantity"
    appliance.session.send_sync.assert_not_awaited()
    await quantity.async_select_option("100 ml")
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 5122, "value": 100})
    )

    ristretto = "ConsumerProducts.CoffeeMaker.Program.Beverage.Ristretto"
    await selected.update({"value": appliance.programs[ristretto].uid})
    assert quantity.options == []
    assert not quantity.available


async def test_profile_conflict_falls_back_to_old_box_with_clear_400(
    ti9555_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Fall back on the 1.12.5 Number when TI9555 XL defaults to 300 ml."""
    appliance = await mock_homeconnect_appliance(description=ti9555_description)
    appliance.session.connected = True
    runtime = runtime_for(appliance, ti9555_description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    number = HCNumber(
        next(
            x
            for x in runtime.available_entity_descriptions["number"]
            if x.key == "number_fill_quantity"
        ),
        runtime,
    )
    selected = appliance.entities["BSH.Common.Root.SelectedProgram"]
    xl = "ConsumerProducts.CoffeeMaker.Program.Beverage.XLCoffee"
    await selected.update({"value": appliance.programs[xl].uid})
    assert quantity.options == []
    assert not quantity.available
    appliance.session.send_sync.side_effect = CodeResponsError(400, "/ro/values")
    with pytest.raises(ServiceValidationError) as error:
        await number.async_set_native_value(305)
    assert error.value.translation_key == "coffee_quantity_rejected"

    espresso = "ConsumerProducts.CoffeeMaker.Program.Beverage.Espresso"
    await selected.update({"value": appliance.programs[espresso].uid})
    assert quantity.options == ["35 ml", "40 ml", "45 ml", "50 ml"]
    with pytest.raises(ServiceValidationError) as error:
        await quantity.async_select_option("40 ml")
    assert error.value.translation_key == "coffee_quantity_rejected"


async def test_program_constraints_narrow_shared_grid(
    eq700_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Use a program-reported range and step ahead of the app fallback."""
    description = json.loads(json.dumps(eq700_description))
    espresso = next(x for x in description["program"] if x["name"].endswith("Beverage.Espresso"))
    espresso["options"][0].update({"min": "40", "max": "50", "stepSize": "10"})
    appliance = await mock_homeconnect_appliance(description=description)
    runtime = runtime_for(appliance, description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    await appliance.entities["BSH.Common.Root.SelectedProgram"].update(
        {"value": appliance.programs[espresso["name"]].uid}
    )
    assert quantity.options == ["40 ml", "50 ml"]


async def test_live_appliance_range_preserves_values_beyond_eq700_grid(
    eq700_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An EQ.9-style descriptionChange must not lose valid volumes."""
    appliance = await mock_homeconnect_appliance(description=eq700_description)
    appliance.session.connected = True
    runtime = runtime_for(appliance, eq700_description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    number = HCNumber(
        next(
            x
            for x in runtime.available_entity_descriptions["number"]
            if x.key == "number_fill_quantity"
        ),
        runtime,
    )
    selected = appliance.entities["BSH.Common.Root.SelectedProgram"]
    fill = appliance.entities[FILL_QUANTITY]
    espresso = "ConsumerProducts.CoffeeMaker.Program.Beverage.Espresso"
    await selected.update({"value": appliance.programs[espresso].uid})
    assert quantity.options == ["35 ml", "40 ml", "45 ml", "50 ml"]

    await fill.update({"min": 35, "max": 60, "stepSize": 5})
    assert quantity.options == ["35 ml", "40 ml", "45 ml", "50 ml", "55 ml", "60 ml"]
    await number.async_set_native_value(55)
    appliance.session.send_sync.assert_awaited_once_with(
        Message(resource="/ro/values", action=Action.POST, data={"uid": 5122, "value": 55})
    )

    cappuccino = "ConsumerProducts.CoffeeMaker.Program.Beverage.Cappuccino"
    await selected.update({"value": appliance.programs[cappuccino].uid})
    await fill.update({"min": 100, "max": 300, "stepSize": 20})
    assert quantity.options == [f"{value} ml" for value in range(100, 301, 20)]


async def test_reported_range_works_with_conflicting_profile_default(
    ti9555_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A device-provided grid is usable even if its default misses EQ700's grid."""
    appliance = await mock_homeconnect_appliance(description=ti9555_description)
    runtime = runtime_for(appliance, ti9555_description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    xl = "ConsumerProducts.CoffeeMaker.Program.Beverage.XLCoffee"
    await appliance.entities["BSH.Common.Root.SelectedProgram"].update(
        {"value": appliance.programs[xl].uid}
    )
    assert quantity.options == []
    await appliance.entities[FILL_QUANTITY].update({"min": 280, "max": 400, "stepSize": 20})
    assert quantity.options == [f"{value} ml" for value in range(280, 401, 20)]


async def test_unmapped_beverage_uses_its_own_reported_range(
    eq700_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """A beverage absent from the EQ700 table still gets device-reported values."""
    description = json.loads(json.dumps(eq700_description))
    description["program"] = [
        item for item in description["program"] if item["name"].endswith("Beverage.Ristretto")
    ]
    appliance = await mock_homeconnect_appliance(description=description)
    runtime = runtime_for(appliance, description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    ristretto = description["program"][0]
    await appliance.entities["BSH.Common.Root.SelectedProgram"].update(
        {"value": appliance.programs[ristretto["name"]].uid}
    )
    assert quantity.options == []
    await appliance.entities[FILL_QUANTITY].update({"min": 15, "max": 35, "stepSize": 5})
    assert quantity.options == ["15 ml", "20 ml", "25 ml", "30 ml", "35 ml"]


async def test_description_change_switches_program_quantity_ranges(
    eq700_description: dict,
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The pinned library must apply per-program NOTIFY bounds before the UI reads them."""
    appliance = await mock_homeconnect_appliance(description=eq700_description)
    runtime = runtime_for(appliance, eq700_description)
    quantity = HCCoffeeQuantitySelect(
        runtime.available_entity_descriptions["coffee_quantity"][0], runtime
    )
    espresso = appliance.programs["ConsumerProducts.CoffeeMaker.Program.Beverage.Espresso"]
    cappuccino = appliance.programs["ConsumerProducts.CoffeeMaker.Program.Beverage.Cappuccino"]

    await appliance._message_handler(
        Message(
            resource="/ro/descriptionChange",
            action=Action.NOTIFY,
            data=[
                {"uid": 257, "value": espresso.uid},
                {"uid": 5122, "parentUID": espresso.uid, "min": 35, "max": 60, "stepSize": 5},
            ],
        )
    )
    assert quantity.options == [f"{value} ml" for value in range(35, 61, 5)]

    await appliance._message_handler(
        Message(
            resource="/ro/descriptionChange",
            action=Action.NOTIFY,
            data=[
                {"uid": 257, "value": cappuccino.uid},
                {"uid": 5122, "parentUID": cappuccino.uid, "min": 100, "max": 300, "stepSize": 20},
            ],
        )
    )
    assert quantity.options == [f"{value} ml" for value in range(100, 301, 20)]

    await appliance._message_handler(
        Message(
            resource="/ro/descriptionChange",
            action=Action.NOTIFY,
            data=[{"uid": 257, "value": espresso.uid}],
        )
    )
    assert quantity.options == [f"{value} ml" for value in range(35, 61, 5)]
