"""Program-aware CoffeeMaker quantity choices from device and saved profile."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_DESCRIPTION

if TYPE_CHECKING:
    from . import HCData

FILL_QUANTITY = "ConsumerProducts.CoffeeMaker.Option.FillQuantity"
_BEVERAGE = "ConsumerProducts.CoffeeMaker.Program.Beverage."

# EQ700 app observations are a fallback when the appliance reports no narrower grid.
# A program whose own profile default conflicts with the fallback uses the legacy box.
COFFEE_QUANTITIES: dict[str, tuple[int, ...]] = {
    _BEVERAGE + "Espresso": (35, 40, 45, 50),
    _BEVERAGE + "EspressoDoppio": (60, 65, 70, 75),
    _BEVERAGE + "Coffee": (80, 100, 120, 140),
    _BEVERAGE + "CaffeGrande": (160, 200, 240, 280),
    _BEVERAGE + "XLCoffee": (280, 320, 360, 400),
    _BEVERAGE + "Cappuccino": (140, 180, 220, 260),
    _BEVERAGE + "LatteMacchiato": (200, 250, 300, 350),
    _BEVERAGE + "CaffeLatte": (160, 200, 240, 280),
    _BEVERAGE + "MilkFroth": (100, 150, 200, 250),
    _BEVERAGE + "WarmMilk": (100, 150, 200, 250),
    _BEVERAGE + "HotWater": (100, 150, 200, 250),
}


def _reported_values(
    minimum: float | None, maximum: float | None, step: float | None
) -> tuple[int, ...]:
    """Build a bounded integer list from a device-reported range."""
    if (
        minimum is None
        or maximum is None
        or step is None
        or not all(value.is_integer() for value in (minimum, maximum, step))
        or minimum < 0
        or maximum < minimum
        or step <= 0
        or (maximum - minimum) / step > 100
    ):
        return ()
    return tuple(range(int(minimum), int(maximum) + 1, int(step)))


def selected_quantity_options(runtime_data: HCData) -> tuple[int, ...]:  # noqa: PLR0911
    """Prefer reported ranges; use app observations only for known programs."""
    appliance = runtime_data.appliance
    if appliance.info.get("type") != "CoffeeMaker":
        return ()
    fill = appliance.entities.get(FILL_QUANTITY)
    program = appliance.selected_program or appliance.active_program
    if fill is None or program is None:
        return ()

    description = runtime_data.coordinator.config_entry.data.get(CONF_DESCRIPTION, {})
    program_description = next(
        (item for item in description.get("program", ()) if item.get("name") == program.name),
        None,
    )
    if program_description is None:
        return ()
    option_description = next(
        (item for item in program_description.get("options", ()) if item.get("refUID") == fill.uid),
        None,
    )
    if option_description is None or option_description.get("available") is False:
        return ()
    minimum = option_description.get("min", fill.min)
    maximum = option_description.get("max", fill.max)
    step = option_description.get("stepSize", fill.step)
    try:
        minimum = float(minimum) if minimum is not None else None
        maximum = float(maximum) if maximum is not None else None
        step = float(step) if step is not None else None
    except TypeError, ValueError:
        return ()
    if step is not None and step <= 0:
        return ()

    base_option = next(
        (item for item in description.get("option", ()) if item.get("uid") == fill.uid),
        {},
    )
    # /ro/descriptionChange can replace the broad base range for this beverage.
    # Its reported range takes precedence over the EQ700 app observations.
    reported_range = any(key in option_description for key in ("min", "max", "stepSize"))
    for key, current in (("min", minimum), ("max", maximum), ("stepSize", step)):
        if current is None or key not in base_option:
            continue
        try:
            reported_range |= float(base_option[key]) != current
        except TypeError, ValueError:
            continue
    if reported_range:
        return _reported_values(minimum, maximum, step)

    try:
        default = int(option_description["default"])
    except KeyError, TypeError, ValueError:
        return ()
    grid = COFFEE_QUANTITIES.get(program.name)
    if grid is None or default not in grid:
        return ()
    values = tuple(
        value
        for value in grid
        if (minimum is None or value >= minimum)
        and (maximum is None or value <= maximum)
        and (step is None or ((value - (minimum or 0)) / step).is_integer())
    )
    return values if default in values else ()
