"""WiFi and light status on the diagnostics card of coffee makers and other appliances."""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import pytest
from custom_components.homeconnect_ws.entity_descriptions import get_available_entities

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

WIFI = "BSH.Common.Status.WiFiSignalStrength"
LIGHT = "BSH.Common.Status.InteriorIlluminationActive"


def _description(appliance_type: str, *, wifi: bool = True, light: bool = True) -> dict:
    status = []
    if wifi:
        status.append(
            {
                "uid": 27,
                "name": WIFI,
                "protocolType": "Integer",
                "access": "read",
                "available": True,
            }
        )
    if light:
        status.append(
            {
                "uid": 532,
                "name": LIGHT,
                "protocolType": "Boolean",
                "access": "read",
                "available": True,
            }
        )
    return deepcopy(
        {
            "info": {
                "brand": "SIEMENS",
                "type": appliance_type,
                "vib": "TEST",
                "deviceID": "diag-test",
                "mac": "00-00-00-00-00-00",
            },
            "status": status,
        }
    )


async def test_coffee_maker_polls_wifi_and_has_no_light_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The EQ700 profile lists both, but the appliance reports neither."""
    appliance = await mock_homeconnect_appliance(description=_description("CoffeeMaker"))
    available = get_available_entities(appliance)
    assert [item.key for item in available["wifi"]] == ["sensor_wifi_signal_strength"]
    assert not any(item.key == "sensor_wifi_signal_strength" for item in available["sensor"])
    assert not any(
        item.key == "binary_sensor_interior_illumination" for item in available["binary_sensor"]
    )


async def test_other_appliances_keep_the_reported_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An oven reports both values, so it keeps the entities that follow the status."""
    appliance = await mock_homeconnect_appliance(description=_description("Oven"))
    available = get_available_entities(appliance)
    assert not available["wifi"]
    wifi = [item for item in available["sensor"] if item.key == "sensor_wifi_signal_strength"]
    assert len(wifi) == 1
    assert wifi[0].entity == WIFI
    assert any(
        item.key == "binary_sensor_interior_illumination" for item in available["binary_sensor"]
    )


async def test_wifi_is_polled_when_the_status_is_missing(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Without the status entity every appliance asks the network info instead."""
    appliance = await mock_homeconnect_appliance(
        description=_description("Dishwasher", wifi=False, light=False)
    )
    available = get_available_entities(appliance)
    assert [item.key for item in available["wifi"]] == ["sensor_wifi_signal_strength"]
    assert not any(item.key == "sensor_wifi_signal_strength" for item in available["sensor"])
    assert not any(
        item.key == "binary_sensor_interior_illumination" for item in available["binary_sensor"]
    )


ESTIMATED = "BSH.Common.Option.EstimatedTotalProgramTime"


def _estimated_description(appliance_type: str) -> dict:
    description = _description(appliance_type, wifi=False, light=False)
    description["option"] = [
        {
            "uid": 531,
            "name": ESTIMATED,
            "protocolType": "Integer",
            "access": "read",
            "available": True,
        }
    ]
    return description


@pytest.mark.parametrize("appliance_type", ["Oven", "Washer", "Dryer", "Dishwasher"])
async def test_other_appliances_keep_the_estimated_program_time(
    appliance_type: str, mock_homeconnect_appliance: MockApplianceType
) -> None:
    """Washers and dryers report the value, so the sensor stays for everything but coffee makers."""
    appliance = await mock_homeconnect_appliance(description=_estimated_description(appliance_type))
    sensors = get_available_entities(appliance)["sensor"]
    assert any(item.key == "sensor_estimated_remaining_program_time" for item in sensors)


async def test_coffee_maker_has_no_estimated_program_time(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The EQ700 lists it but never reports a value."""
    appliance = await mock_homeconnect_appliance(description=_estimated_description("CoffeeMaker"))
    sensors = get_available_entities(appliance)["sensor"]
    assert not any(item.key == "sensor_estimated_remaining_program_time" for item in sensors)
