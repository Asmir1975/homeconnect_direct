"""Laundry, dishwasher and coffee settings/status values that had no entity yet."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from custom_components.homeconnect_ws.sensor import HCSensor
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

ERROR_CODES = "BSH.Common.Status.ErrorCodesList"

NEW_ENTITIES = [
    (
        "binary_sensor",
        "status",
        "BSH.Common.Status.BackendConnected",
        "binary_sensor_backend_connected",
    ),
    (
        "binary_sensor",
        "event",
        "LaundryCare.Dryer.Event.CoolDownPhaseRunning",
        "binary_sensor_dryer_cooldown_running",
    ),
    (
        "binary_sensor",
        "event",
        "LaundryCare.Dryer.Event.DryerSelfCleaning.CleanSelfCleaningModule",
        "binary_sensor_dryer_clean_self_cleaning_module",
    ),
    (
        "binary_sensor",
        "event",
        "LaundryCare.Dryer.Event.EvaporatorFrozen",
        "binary_sensor_dryer_evaporator_frozen",
    ),
    ("sensor", "status", ERROR_CODES, "sensor_error_codes"),
    (
        "sensor",
        "status",
        "LaundryCare.Washer.Status.ProcessingData.LaundryLoad",
        "sensor_washer_laundry_load",
    ),
    (
        "sensor",
        "status",
        "LaundryCare.Washer.Status.ProcessingData.TextileType",
        "sensor_washer_textile_type",
    ),
    (
        "sensor",
        "status",
        "LaundryCare.Washer.Status.ProcessingData.PeakFinalSpinSpeed",
        "sensor_washer_peak_final_spin_speed",
    ),
    (
        "sensor",
        "status",
        "LaundryCare.Common.Status.Version.Smm.BusinessLogicFw",
        "sensor_fw_business_logic",
    ),
    ("sensor", "status", "LaundryCare.Common.Status.Version.Smm.DomainFw", "sensor_fw_domain"),
    ("sensor", "status", "LaundryCare.Common.Status.Version.Smm.HcFw", "sensor_fw_hc"),
    ("sensor", "status", "LaundryCare.Common.Status.Version.Smm.UiLogicFw", "sensor_fw_ui_logic"),
    ("sensor", "status", "LaundryCare.Common.Status.Version.Smm.OperatingSystem", "sensor_fw_os"),
    (
        "select",
        "setting",
        "ConsumerProducts.CoffeeMaker.Setting.Illumination",
        "select_coffee_illumination",
    ),
    (
        "select",
        "setting",
        "Dishcare.Dishwasher.Setting.DoorOpeningHandling",
        "select_dishwasher_door_opening_handling",
    ),
    (
        "switch",
        "setting",
        "Dishcare.Dishwasher.Setting.EcoPrognosis",
        "switch_dishwasher_eco_prognosis",
    ),
    (
        "switch",
        "setting",
        "Dishcare.Dishwasher.Setting.ErrorLightEnabled",
        "switch_dishwasher_error_light",
    ),
    (
        "switch",
        "setting",
        "Dishcare.Dishwasher.Setting.TimeLight",
        "switch_dishwasher_time_light",
    ),
]


@pytest.mark.parametrize(("platform", "kind", "name", "key"), NEW_ENTITIES)
async def test_new_entity_is_created_when_appliance_reports_it(
    mock_homeconnect_appliance: MockApplianceType,
    platform: str,
    kind: str,
    name: str,
    key: str,
) -> None:
    """Each value gets its entity only on appliances that report it."""
    access = Access.READ if kind in {"status", "event"} else Access.READ_WRITE
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            **{kind: [EntityDescription(uid=301, name=name, available=True, access=access)]},
        )
    )
    keys = [description.key for description in get_available_entities(appliance)[platform]]
    assert key in keys

    empty = await mock_homeconnect_appliance(
        description=DeviceDescription(info={"deviceID": "synthetic"})
    )
    keys = [description.key for description in get_available_entities(empty)[platform]]
    assert key not in keys


async def test_error_codes_count_and_attribute(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The error code list shows as a count, with the codes as an attribute."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"deviceID": "synthetic"},
            status=[
                EntityDescription(uid=302, name=ERROR_CODES, available=True, access=Access.READ)
            ],
        )
    )
    description = next(
        d for d in get_available_entities(appliance)["sensor"] if d.key == "sensor_error_codes"
    )
    sensor = HCSensor(
        description,
        SimpleNamespace(
            appliance=appliance,
            coordinator=MagicMock(connected=True),
            device_info={},
        ),
    )
    assert sensor.native_value is None

    await appliance.entities[ERROR_CODES].update({"value": []})
    assert sensor.native_value == 0
    assert sensor.extra_state_attributes["codes"] == []

    await appliance.entities[ERROR_CODES].update({"value": ["E:12", "E:34"]})
    assert sensor.native_value == 2
    assert sensor.extra_state_attributes["codes"] == ["E:12", "E:34"]
