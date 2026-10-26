"""Button entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeconnect_websocket.entities import Execution

from .const import DOMAIN
from .entity import HCEntity
from .helpers import (
    create_entities,
    error_decorator,
    pending_acknowledge_event_uid,
    start_coffee_favorite_with_fallback,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeconnect_websocket.entities import ActiveProgram, Command

    from . import HCConfigEntry
    from .entity_descriptions.descriptions_definitions import HCButtonEntityDescription

PARALLEL_UPDATES = 0

COFFEE_MAKER_TYPE = "CoffeeMaker"
COFFEE_FAVORITE_PREFIX = "BSH.Common.Program.Favorite."


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HCConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up button platform."""
    entities = create_entities(
        {"button": HCButton, "start_button": HCStartButton}, config_entry.runtime_data
    )
    async_add_entites(entities)


class HCButton(HCEntity, ButtonEntity):
    """Abort Button Entity."""

    _entity: Command
    entity_description: HCButtonEntityDescription

    @error_decorator
    async def async_press(self) -> None:
        press_value = self.entity_description.press_value
        if press_value is None:
            press_value = pending_acknowledge_event_uid(self._runtime_data)
            if press_value is None:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="no_pending_event",
                )
        await self._entity.set_value(press_value)


class HCStartButton(HCEntity, ButtonEntity):
    """Start Button Entity."""

    _entity: ActiveProgram
    entity_description: HCButtonEntityDescription

    @property
    def available(self) -> bool:
        available = super().available
        available &= self._runtime_data.appliance.selected_program is not None
        if self._runtime_data.appliance.selected_program is not None:
            available &= (
                self._runtime_data.appliance.selected_program.execution
                == Execution.SELECT_AND_START
            )
        return available

    @error_decorator
    async def async_press(self) -> None:
        program = self._runtime_data.appliance.selected_program
        is_coffee_maker = self._runtime_data.appliance.info.get("type") == COFFEE_MAKER_TYPE
        if is_coffee_maker and program.name.startswith(COFFEE_FAVORITE_PREFIX):
            # A Siemens coffee maker answered 400 to the start of a favorite that
            # carried values for unavailable options. Only favorites on coffee
            # makers get the single retry, everything else keeps the plain start.
            await start_coffee_favorite_with_fallback(program)
        else:
            await program.start()
