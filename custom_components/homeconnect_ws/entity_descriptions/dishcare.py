"""Description for Dishcare.Dishwasher Entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import EntityCategory, UnitOfTime

from .descriptions_definitions import (
    HCBinarySensorEntityDescription,
    HCNumberEntityDescription,
    HCSelectEntityDescription,
    HCSensorEntityDescription,
    HCSwitchEntityDescription,
    _EntityDescriptionsDefinitionsType,
)

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance

# Most urgent first; the sensor shows the first one that is active, else "none"
# (drain-blocking errors before FlexSpray errors before maintenance reminders).
DISHWASHER_MESSAGES = (
    ("Dishcare.Dishwasher.Event.DrainPumpBlocked", "drain_pump_blocked"),
    ("Dishcare.Dishwasher.Event.DrainingNotPossible", "draining_not_possible"),
    ("Dishcare.Dishwasher.Event.FlexSpray.Error.Blocked", "flexspray_error_blocked"),
    ("Dishcare.Dishwasher.Event.FlexSpray.Error.General", "flexspray_error_general"),
    (
        "Dishcare.Dishwasher.Event.FlexSpray.Error.SprayArmNotMounted",
        "flexspray_error_spray_arm_not_mounted",
    ),
    ("Dishcare.Dishwasher.Event.WaterheaterCalcified", "waterheater_calcified"),
    ("Dishcare.Dishwasher.Event.CheckFilterSystem", "check_filter_system"),
    (
        "Dishcare.Dishwasher.Event.MachineCareAndFilterCleaningReminder",
        "machine_care_and_filter_cleaning_reminder",
    ),
    ("Dishcare.Dishwasher.Event.SmartFilterCleaningReminder", "smart_filter_cleaning_reminder"),
    ("Dishcare.Dishwasher.Event.MachineCareReminder", "machine_care_reminder"),
    ("Dishcare.Dishwasher.Event.LowVoltage", "low_voltage"),
    ("BSH.Common.Event.ProgramAborted", "program_aborted"),
)


def generate_dishwasher_message(appliance: HomeAppliance) -> HCSensorEntityDescription | None:
    """Get the most urgent active maintenance/error message, else "none" (Asko 18.10.2026)."""
    messages = [
        (entity, key) for entity, key in DISHWASHER_MESSAGES if entity in appliance.entities
    ]
    if not messages:
        return None
    return HCSensorEntityDescription(
        key="sensor_dishwasher_message",
        entities=tuple(entity for entity, _ in messages),
        device_class=SensorDeviceClass.ENUM,
        options=[key for _, key in messages] + ["none"],
    )


DISHCARE_ENTITY_DESCRIPTIONS: _EntityDescriptionsDefinitionsType = {
    "binary_sensor": [
        HCBinarySensorEntityDescription(
            key="binary_sensor_intensiv_zone_active",
            entity="Dishcare.Dishwasher.Option.IntensivZone",
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_half_load_active",
            entity="Dishcare.Dishwasher.Option.HalfLoad",
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_hygiene_plus_active",
            entity="Dishcare.Dishwasher.Option.HygienePlus",
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_pretreatment_active",
            entity="Dishcare.Dishwasher.Option.Pretreatment",
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_eco_dry_active",
            entity="Dishcare.Dishwasher.Status.EcoDryActive",
            entity_registry_enabled_default=False,
        ),
        # FlexSpray error events
        # NOTE: Bosch refers to this feature as "PowerControl" in marketing/UI.
        # The protocol/API objects use the name "FlexSpray", which is kept here.
    ],
    "event_sensor": [
        generate_dishwasher_message,
        HCSensorEntityDescription(
            key="sensor_rinse_aid",
            entities=[
                "Dishcare.Dishwasher.Event.RinseAidLack",
                "Dishcare.Dishwasher.Event.RinseAidNearlyEmpty",
            ],
            device_class=SensorDeviceClass.ENUM,
            options=["empty", "nearly_empty", "full"],
        ),
        HCSensorEntityDescription(
            key="sensor_salt",
            entities=[
                "Dishcare.Dishwasher.Event.SaltLack",
                "Dishcare.Dishwasher.Event.SaltNearlyEmpty",
            ],
            device_class=SensorDeviceClass.ENUM,
            options=["empty", "nearly_empty", "full"],
        ),
    ],
    "select": [
        HCSelectEntityDescription(
            key="select_dishwasher_interior_light_mode",
            entity="Dishcare.Dishwasher.Setting.InteriorLightMode",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            force_disabled_default=True,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_drying_assistant_all_programs",
            entity="Dishcare.Dishwasher.Setting.DryingAssistantAllPrograms",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_hot_water",
            entity="Dishcare.Dishwasher.Setting.HotWater",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_rinse_aid",
            entity="Dishcare.Dishwasher.Setting.RinseAid",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_sound_level_signal",
            entity="Dishcare.Dishwasher.Setting.SoundLevelSignal",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_sound_level_key",
            entity="Dishcare.Dishwasher.Setting.SoundLevelKey",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_water_hardness",
            entity="Dishcare.Dishwasher.Setting.WaterHardness",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_sensitivity_turbidity",
            entity="Dishcare.Dishwasher.Setting.SensitivityTurbidity",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eco_as_default",
            entity="Dishcare.Dishwasher.Setting.EcoAsDefault",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        # FlexSpray configuration options
        # NOTE: Bosch refers to this feature as "PowerControl" in marketing/UI.
        # The protocol/API objects use the name "FlexSpray", which is kept here.
        HCSelectEntityDescription(
            key="select_flexspray_type",
            entity="Dishcare.Dishwasher.Option.FlexSpray.Type",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_front_left",
            entity="Dishcare.Dishwasher.Option.FlexSpray.FrontLeft",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_back_left",
            entity="Dishcare.Dishwasher.Option.FlexSpray.BackLeft",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_back_right",
            entity="Dishcare.Dishwasher.Option.FlexSpray.BackRight",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_front_right",
            entity="Dishcare.Dishwasher.Option.FlexSpray.FrontRight",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        # FlexSpray custom settings
        HCSelectEntityDescription(
            key="select_flexspray_custom_front_left",
            entity="Dishcare.Dishwasher.Setting.FlexSpray.Custom.FrontLeft",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_custom_back_left",
            entity="Dishcare.Dishwasher.Setting.FlexSpray.Custom.BackLeft",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_custom_back_right",
            entity="Dishcare.Dishwasher.Setting.FlexSpray.Custom.BackRight",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flexspray_custom_front_right",
            entity="Dishcare.Dishwasher.Setting.FlexSpray.Custom.FrontRight",
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            has_state_translation=True,
        ),
    ],
    "sensor": [
        HCSensorEntityDescription(
            key="sensor_program_phase",
            entity="Dishcare.Dishwasher.Status.ProgramPhase",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_machine_care_reminder",
            entity="Dishcare.Dishwasher.Status.MachineCareReminder.RemainingProgramRuns",
            entity_category=EntityCategory.DIAGNOSTIC,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        HCSensorEntityDescription(
            key="sensor_silence_on_demand_remaining_time",
            entity="Dishcare.Dishwasher.Status.SilenceOnDemandRemainingTime",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
        ),
    ],
    "switch": [
        HCSwitchEntityDescription(
            key="switch_extra_dry_option",
            entity="Dishcare.Dishwasher.Option.ExtraDry",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_hygiene_plus",
            entity="Dishcare.Dishwasher.Option.HygienePlus",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_intensiv_zone",
            entity="Dishcare.Dishwasher.Option.IntensivZone",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_vario_speed_plus",
            entity="Dishcare.Dishwasher.Option.VarioSpeedPlus",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_silence_on_demand",
            entity="Dishcare.Dishwasher.Option.SilenceOnDemand",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_brilliance_dry",
            entity="Dishcare.Dishwasher.Option.BrillianceDry",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        # Also referred to as "CrystalDry"
        HCSwitchEntityDescription(
            key="switch_zeolite_dry",
            entity="Dishcare.Dishwasher.Option.ZeoliteDry",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_extra_dry",
            entity="Dishcare.Dishwasher.Setting.ExtraDry",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_speed_on_demand",
            entity="Dishcare.Dishwasher.Setting.SpeedOnDemand",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_info_light",
            entity="Dishcare.Dishwasher.Setting.InfoLight",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_dishwasher_gap_illumination",
            entity="Dishcare.Dishwasher.Setting.GapIllumination",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
            entity_registry_enabled_default=False,
            force_disabled_default=True,
        ),
        HCSwitchEntityDescription(
            key="switch_half_load",
            entity="Dishcare.Dishwasher.Option.HalfLoad",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_extra_rinse",
            entity="Dishcare.Dishwasher.Option.ExtraRinse",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_pretreatment",
            entity="Dishcare.Dishwasher.Option.Pretreatment",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_eco_dry",
            entity="Dishcare.Dishwasher.Option.EcoDry",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    ],
    "number": [
        HCNumberEntityDescription(
            key="number_silence_on_demand_default_time",
            entity="Dishcare.Dishwasher.Setting.SilenceOnDemandDefaultTime",
            device_class=NumberDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            mode=NumberMode.BOX,
            enforce_step=True,
            entity_category=EntityCategory.CONFIG,
        ),
    ],
}
