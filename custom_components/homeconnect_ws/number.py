"""Number entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import DEFAULT_MAX_VALUE, DEFAULT_MIN_VALUE, NumberEntity
from homeassistant.exceptions import ServiceValidationError
from homeconnect_websocket.errors import CodeResponsError

from .coffee_quantity import FILL_QUANTITY, selected_quantity_options
from .const import DOMAIN
from .entity import HCEntity
from .helpers import (
    create_entities,
    ensure_writable,
    error_decorator,
    write_through_selected_program,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeconnect_websocket.entities import Entity as HcEntity

    from . import HCConfigEntry, HCData
    from .entity_descriptions.descriptions_definitions import HCNumberEntityDescription

PARALLEL_UPDATES = 0

_STEP_TOLERANCE = 1e-6


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001
    config_entry: HCConfigEntry,
    async_add_entites: AddEntitiesCallback,
) -> None:
    """Set up number platform."""
    entities = create_entities({"number": HCNumber}, config_entry.runtime_data)
    async_add_entites(entities)


class HCNumber(HCEntity, NumberEntity):
    """Number Entity."""

    entity_description: HCNumberEntityDescription

    def __init__(
        self,
        entity_description: HCNumberEntityDescription,
        runtime_data: HCData,
    ) -> None:
        super().__init__(entity_description, runtime_data)
        self._entity._type = int  # noqa: SLF001 Force integer type
        self._elapsed_event = (
            self._entities[-1] if entity_description.zero_when_event_present else None
        )
        self._expired = self._elapsed_event is not None and self._elapsed_event.value == "Present"

    async def callback(self, entity: HcEntity) -> None:
        if self._elapsed_event is not None:
            if entity is self._elapsed_event and entity.value == "Present":
                self._expired = True
            elif entity is self._entity:
                self._expired = False
        await super().callback(entity)

    @property
    def native_value(self) -> int | float:
        if self._expired:
            return 0
        return self._entity.value

    @property
    def native_min_value(self) -> float:
        if hasattr(self._entity, "min") and self._entity.min is not None:
            return self._entity.min
        if self.entity_description.native_min_value is not None:
            return self.entity_description.native_min_value
        return DEFAULT_MIN_VALUE

    @property
    def native_max_value(self) -> float:
        if hasattr(self._entity, "max") and self._entity.max is not None:
            return self._entity.max
        if self.entity_description.native_max_value is not None:
            return self.entity_description.native_max_value
        return DEFAULT_MAX_VALUE

    @property
    def native_step(self) -> float | None:
        if hasattr(self._entity, "step") and self._entity.step is not None:
            if (
                self.entity_description.enforce_step
                and self.unit_of_measurement != self.native_unit_of_measurement
            ):
                # Home Assistant converts min and max to the chosen unit but hands
                # the native step on unchanged (60 s would stay 60 min). Let it derive
                # the step from the converted range instead (1 for 1 to 30 min).
                return None
            return self._entity.step
        return None

    def _ensure_valid_step(self, value: float) -> None:
        """Raise a clear error for a value the appliance would reject with 400."""
        step = getattr(self._entity, "step", None)
        if not step:
            return
        minimum = getattr(self._entity, "min", None) or 0
        remainder = (value - minimum) % step
        if min(remainder, step - remainder) < _STEP_TOLERANCE:
            return
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_step",
            translation_placeholders={
                "step": f"{step:g}",
                "min": f"{minimum:g}",
                "max": f"{self.native_max_value:g}",
                "unit": str(self.native_unit_of_measurement or ""),
            },
        )

    @error_decorator
    async def async_set_native_value(self, value: float) -> None:
        ensure_writable(self._entity)
        if self.entity_description.enforce_step:
            self._ensure_valid_step(value)
        if (
            self._entity.name == FILL_QUANTITY
            and (choices := selected_quantity_options(self._runtime_data))
            and value not in choices
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="invalid_coffee_quantity"
            )
        try:
            await self._entity.set_value(int(value))
        except CodeResponsError as exc:
            if exc.code == 527 and await write_through_selected_program(
                self._runtime_data, self._entity, int(value)
            ):
                return
            if exc.code == 400 and self._entity.name == FILL_QUANTITY:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="coffee_quantity_rejected"
                ) from None
            if exc.code != 400 or self._entity.name != "BSH.Common.Option.StartInRelative":
                raise
            # HB774G1B1 answers 400 without a program and for programs without delayed start.
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key=(
                    "start_in_needs_program"
                    if self._runtime_data.appliance.selected_program is None
                    else "start_in_not_supported"
                ),
            ) from None
