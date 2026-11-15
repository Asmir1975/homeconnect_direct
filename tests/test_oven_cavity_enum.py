"""Cavity status sensors of ovens that report an enumeration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.homeconnect_ws.entity_descriptions import get_available_entities
from homeassistant.components.sensor import SensorDeviceClass
from homeconnect_websocket.entities import Access, DeviceDescription, EntityDescription

if TYPE_CHECKING:
    from homeconnect_websocket.testutils import MockApplianceType


def _enum_status(uid: int, name: str, enumeration: dict[str, str]) -> EntityDescription:
    return EntityDescription(
        uid=uid,
        name=name,
        protocolType="Integer",
        contentType="enumeration",
        enumeration=enumeration,
        access=Access.READ,
        available=True,
    )


async def test_cavity_level_and_selector_are_enum_sensors(
    mock_homeconnect_appliance: MockApplianceType,
) -> None:
    """Seen on HR776G1B1: both report an enumeration, names and uids from its profile."""
    appliance = await mock_homeconnect_appliance(
        description=DeviceDescription(
            info={"type": "Oven"},
            status=[
                _enum_status(
                    6099,
                    "Cooking.Oven.Status.Cavity.001.Level",
                    {"1": "Level01", "2": "Level02", "3": "Level03"},
                ),
                _enum_status(6076, "Cooking.Oven.Status.Cavity.001.CavitySelector", {"1": "Main"}),
            ],
        )
    )
    sensors = {item.key: item for item in get_available_entities(appliance)["sensor"]}
    for key in ("sensor_oven_cavity_level_001", "sensor_oven_cavity_selector_001"):
        assert sensors[key].device_class is SensorDeviceClass.ENUM
        assert sensors[key].force_disabled_default
