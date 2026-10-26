"""Meat probe temperature of ovens that list it only under the cavity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType

CAVITY_PROBE = "Cooking.Oven.Status.Cavity.001.CurrentMeatprobeTemperature"
GENERAL_PROBE = "Cooking.Oven.Status.CurrentMeatprobeTemperature"
KEY = "sensor_oven_cavity_meatprobe_temperature_001"
PLUGGED = "Cooking.Oven.Status.Cavity.001.MeatprobePlugged"
PLUGGED_KEY = "binary_sensor_oven_cavity_meatprobe_plugged_001"


def _status(uid: int, name: str) -> EntityDescription:
    return EntityDescription(
        uid=uid, name=name, protocolType="Float", access=Access.READ, available=True
    )


def _sensors(appliance_type: str, *statuses: EntityDescription) -> DeviceDescription:
    return DeviceDescription(info={"type": appliance_type}, status=list(statuses))


async def test_cavity_meatprobe_gets_a_sensor(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The probe is only listed under Cavity.001: names and uids from the HR776GMB1 profile."""
    appliance = await mock_homeconnect_appliance(
        description=_sensors("Oven", _status(6086, CAVITY_PROBE))
    )
    sensors = {item.key: item for item in get_available_entities(appliance)["sensor"]}
    assert KEY in sensors
    assert sensors[KEY].entity == CAVITY_PROBE
    assert sensors[KEY].device_class is SensorDeviceClass.TEMPERATURE
    assert not sensors[KEY].force_disabled_default


async def test_general_meatprobe_is_not_doubled(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """An oven that also has the general probe entity keeps only that sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_sensors("Oven", _status(6086, CAVITY_PROBE), _status(4101, GENERAL_PROBE))
    )
    keys = [item.key for item in get_available_entities(appliance)["sensor"]]
    assert KEY not in keys
    assert "sensor_oven_current_meatprobe_temperature" in keys


async def test_oven_without_meatprobe_gets_no_sensor(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """No probe in the profile, no probe sensor."""
    appliance = await mock_homeconnect_appliance(
        description=_sensors(
            "Oven", _status(6090, "Cooking.Oven.Status.Cavity.001.CurrentTemperature")
        )
    )
    keys = [item.key for item in get_available_entities(appliance)["sensor"]]
    assert KEY not in keys


async def test_cavity_meatprobe_plugged_gets_a_sensor(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The plug state is listed under Cavity.001 as well (HR776GMB1 profile)."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"type": "Oven"},
            status=[
                EntityDescription(
                    uid=6088,
                    name=PLUGGED,
                    protocolType="Boolean",
                    access=Access.READ,
                    available=True,
                )
            ],
        )
    )
    sensors = {item.key: item for item in get_available_entities(appliance)["binary_sensor"]}
    assert PLUGGED_KEY in sensors
    assert sensors[PLUGGED_KEY].entity == PLUGGED
    assert sensors[PLUGGED_KEY].device_class is BinarySensorDeviceClass.PLUG


async def test_target_temperature_comes_from_the_status(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """The target is the cavity status, only listed while cooking (HR776GMB1)."""
    name = "Cooking.Oven.Status.Server.Cavity.001.MeatProbeSetpointTemperatureCelsius"
    appliance = await mock_homeconnect_appliance(
        description=_sensors(
            "Oven",
            _status(2071, name),
            _status(6084, "Cooking.Oven.Status.Cavity.001.CurrentTemperature"),
        )
    )
    sensors = {item.key: item for item in get_available_entities(appliance)["sensor"]}
    description = sensors["sensor_oven_meatprobe_target_temperature_001"]
    assert description.entity == name
    assert description.device_class is SensorDeviceClass.TEMPERATURE
    assert not description.force_disabled_default
