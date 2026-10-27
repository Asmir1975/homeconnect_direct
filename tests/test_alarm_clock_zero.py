"""The oven alarm clock reads 0 once its elapsed event shows up."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from custom_components.homeconnect_ws.entity_descriptions.descriptions_definitions import (
    HCNumberEntityDescription,
)
from custom_components.homeconnect_ws.number import HCNumber

SETTING = "Cooking.Oven.Setting.Cavity.001.AlarmClock"
EVENT = "Cooking.Oven.Event.Cavity.001.AlarmClockElapsed"


def _number(
    setting_value: int, event_value: str, *, with_event: bool = True
) -> tuple[HCNumber, SimpleNamespace, SimpleNamespace]:
    setting = SimpleNamespace(value=setting_value, uid=6135, _type=None)
    event = SimpleNamespace(value=event_value, uid=6131)
    description = HCNumberEntityDescription(
        key="number_oven_setting_001_alarm_clock",
        entity=SETTING,
        entities=[EVENT] if with_event else None,
        zero_when_event_present=with_event,
    )
    runtime_data = SimpleNamespace(
        coordinator=MagicMock(),
        device_info=MagicMock(),
        appliance=SimpleNamespace(
            info={"deviceID": "device"},
            entities={SETTING: setting, EVENT: event},
        ),
    )
    number = HCNumber(description, runtime_data)
    number.async_write_ha_state = MagicMock()
    return number, setting, event


async def test_reads_zero_after_the_event_until_a_new_value() -> None:
    """The appliance does not always report 0 at the end, 0 holds until a new value comes."""
    number, setting, event = _number(59, "Off")
    assert number.native_value == 59

    event.value = "Present"
    await number.callback(event)
    assert number.native_value == 0

    event.value = "Off"
    await number.callback(event)
    assert number.native_value == 0

    setting.value = 120
    await number.callback(setting)
    assert number.native_value == 120


async def test_event_that_is_already_present_reads_zero() -> None:
    """A restart while the event is Present shows 0 instead of the stale value."""
    number, _, _ = _number(59, "Present")
    assert number.native_value == 0


async def test_without_the_flag_the_value_is_untouched() -> None:
    """Numbers without the flag follow the appliance value."""
    number, _, event = _number(59, "Off", with_event=False)

    event.value = "Present"
    await number.callback(event)

    assert number.native_value == 59
