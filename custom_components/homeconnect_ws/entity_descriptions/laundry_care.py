"""Description for LaundryCare Entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberMode
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfMass,
    UnitOfVolume,
)

from .common import software_messages
from .descriptions_definitions import (
    HCBinarySensorEntityDescription,
    HCLightEntityDescription,
    HCNumberEntityDescription,
    HCSelectEntityDescription,
    HCSensorEntityDescription,
    HCSwitchEntityDescription,
)

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance
    from homeconnect_websocket.entities import Entity as HcEntity

    from .descriptions_definitions import _EntityDescriptionsDefinitionsType


LAUNDRY_LOAD_UNKNOWN = 0xFFFF


def _laundry_load(entity: HcEntity) -> int | None:
    """Return the measured load in grams, None when the washer reports no value."""
    if entity.value_raw == LAUNDRY_LOAD_UNKNOWN:
        return None
    return entity.value


def generate_washer_speed_perfect(appliance: HomeAppliance) -> HCSwitchEntityDescription | None:
    """
    Get the Washer-specific SpeedPerfect switch description.

    Distinct key only when the Common variant is also present, avoids the
    unique_id collision without changing existing entity_ids.
    """
    if "LaundryCare.Washer.Option.SpeedPerfect" not in appliance.entities:
        return None
    key = "switch_laundry_speed_perfect"
    if "LaundryCare.Common.Option.SpeedPerfect" in appliance.entities:
        key = "switch_laundry_speed_perfect_washer"
    return HCSwitchEntityDescription(
        key=key,
        translation_key="switch_laundry_speed_perfect",
        entity="LaundryCare.Washer.Option.SpeedPerfect",
        device_class=SwitchDeviceClass.SWITCH,
    )


# Errors first, then everyday events, then reminders; the sensor shows the first one that
# is active, else "none".
LAUNDRY_MESSAGES = (
    # Errors first, then everyday events, then reminders.
    ("LaundryCare.Washer.Event.Circulation.Pump.ErrorLockedRotor", "circulation_pump_locked_rotor"),
    ("LaundryCare.Washer.Event.Circulation.Pump.ErrorMaxTorque", "circulation_pump_max_torque"),
    ("LaundryCare.Common.Event.SupplyPower.BlackedOut", "power_blackout"),
    ("LaundryCare.Dryer.Event.DryingProcessFinished", "drying_process_finished"),
    ("LaundryCare.Common.Event.DelayedShutdown", "delayed_shutdown"),
    ("LaundryCare.Common.Event.DelayedShutdownCanceled", "delayed_shutdown_canceled"),
    ("LaundryCare.Washer.Event.WaterSupply.WarmWaterAbsent", "warm_water_absent"),
    ("LaundryCare.Dryer.Event.RefresherContainerEmpty", "refresher_container_empty"),
    ("LaundryCare.Dryer.Event.DryerSelfCleaning.CleanLintFilter", "clean_lint_filter"),
    ("LaundryCare.Dryer.Event.EasyClean.Filter.RemindCleaning", "filter_cleaning_reminder"),
)


def generate_laundry_message(appliance: HomeAppliance) -> HCSensorEntityDescription | None:
    """Get the most urgent active washer or dryer message, else "none"."""
    messages = [(entity, key) for entity, key in LAUNDRY_MESSAGES if entity in appliance.entities]
    if not messages:
        return None
    messages += software_messages(appliance)
    return HCSensorEntityDescription(
        key="sensor_laundry_message",
        entities=tuple(entity for entity, _ in messages),
        device_class=SensorDeviceClass.ENUM,
        options=[key for _, key in messages] + ["none"],
    )


LAUNDRY_ENTITY_DESCRIPTIONS: _EntityDescriptionsDefinitionsType = {
    "sensor": [
        HCSensorEntityDescription(
            key="sensor_laundry_reload",
            entity="LaundryCare.Common.Status.Laundry.Reload",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_laundry_process_phase",
            entity="LaundryCare.Common.Option.ProcessPhase",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_dryer_process_phase",
            entity="LaundryCare.Dryer.Option.ProcessPhase",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_laundry_spin_speed",
            entity="LaundryCare.Washer.Option.SpinSpeed",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_laundry_load_recommendation",
            entity="LaundryCare.Common.Option.LoadRecommendation",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.GRAMS,
            suggested_unit_of_measurement=UnitOfMass.KILOGRAMS,
        ),
        HCSensorEntityDescription(
            key="sensor_laundry_status_idos1_fill_level",
            entity="LaundryCare.Washer.Status.IDos1FillLevel",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
            entity_registry_enabled_default=False,
        ),
        HCSensorEntityDescription(
            key="sensor_laundry_status_idos2_fill_level",
            entity="LaundryCare.Washer.Status.IDos2FillLevel",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
            entity_registry_enabled_default=False,
        ),
        HCSensorEntityDescription(
            key="sensor_washer_laundry_load",
            entity="LaundryCare.Washer.Status.ProcessingData.LaundryLoad",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.GRAMS,
            suggested_unit_of_measurement=UnitOfMass.KILOGRAMS,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=_laundry_load,
        ),
        HCSensorEntityDescription(
            key="sensor_washer_textile_type",
            entity="LaundryCare.Washer.Status.ProcessingData.TextileType",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
    ],
    "binary_sensor": [
        HCBinarySensorEntityDescription(
            key="binary_sensor_refresher_level",
            entity="LaundryCare.Dryer.Status.RefresherFillLevel",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on=("Poor"),
            value_off=("Filled"),
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_condensate_container_full",
            entity="LaundryCare.Dryer.Event.CondensateContainerFull",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_lint_filter_full",
            entity="LaundryCare.Dryer.Event.LintFilterFull",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_maintenance_reminder",
            entity="LaundryCare.Dryer.Event.Maintenance.Remind",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_foam_detection",
            entity="LaundryCare.Common.Event.FoamDetection",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_supply_voltage_too_low",
            entity="LaundryCare.Common.Event.SupplyPower.SupplyVoltageTooLow",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_water_level_too_high",
            entity="LaundryCare.Common.Event.DoorLock.WaterLevelTooHigh",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_door_not_lockable",
            entity="LaundryCare.Common.Event.DoorNotLockable",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_door_not_unlockable",
            entity="LaundryCare.Common.Event.DoorNotUnlockable",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_door_open",
            entity="LaundryCare.Common.Event.DoorOpen",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_fatal_error_occurred",
            entity="LaundryCare.Common.Event.FatalErrorOccured",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_drum_clean_reminder",
            entity="LaundryCare.Washer.Event.DrumCleanReminder",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_idos1_fill_level_poor",
            entity="LaundryCare.Washer.Event.IDos1FillLevelPoor",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_idos2_fill_level_poor",
            entity="LaundryCare.Washer.Event.IDos2FillLevelPoor",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_idos_unit_defect",
            entity="LaundryCare.Washer.Event.IDosUnitDefect",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_pump_error",
            entity="LaundryCare.Washer.Event.PumpError",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_spin_abort",
            entity="LaundryCare.Washer.Event.Spin.SpinAbort",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_release_rinse_hold_pending",
            entity="LaundryCare.Washer.Event.ReleaseRinseHoldPending",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            entity_registry_enabled_default=False,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_idos_open_tray",
            entity="LaundryCare.Washer.Event.IDos.IDosOpenTray",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_dryer_cooldown_running",
            entity="LaundryCare.Dryer.Event.CoolDownPhaseRunning",
            entity_category=EntityCategory.DIAGNOSTIC,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_dryer_clean_self_cleaning_module",
            entity="LaundryCare.Dryer.Event.DryerSelfCleaning.CleanSelfCleaningModule",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_dryer_evaporator_frozen",
            entity="LaundryCare.Dryer.Event.EvaporatorFrozen",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
    ],
    "select": [
        HCSelectEntityDescription(
            key="select_auto_power_off",
            entity="LaundryCare.Common.Setting.AutoPowerOff",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_brightness",
            entity="LaundryCare.Common.Setting.BrightnessLevel",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_door_light_ring_mode",
            entity="LaundryCare.Common.Setting.DoorLightRing.ActiveMode",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_door_light_ring_brightness",
            entity="LaundryCare.Common.Setting.DoorLightRing.BrightnessLevel",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_end_signal_volume",
            entity="LaundryCare.Common.Setting.EndSignalVolume",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_key_signal_volume",
            entity="LaundryCare.Common.Setting.KeySignalVolume",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_sound_volume",
            entity="LaundryCare.Common.Setting.Sound.Volume",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_power_rating",
            entity="LaundryCare.Common.Setting.SupplyPower.PowerRating",
            entity_category=EntityCategory.CONFIG,
            has_state_translation=False,
        ),
        HCSelectEntityDescription(
            key="select_laundry_wrinkle_guard",
            entity="LaundryCare.Dryer.Option.WrinkleGuard",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_cupboard_dry_fine_adjust",
            entity="LaundryCare.Dryer.Setting.CupboardDryFineAdjust",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_cupboard_dry_plus_fine_adjust",
            entity="LaundryCare.Dryer.Setting.CupboardDryPlusFineAdjust",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_iron_dry_fine_adjust",
            entity="LaundryCare.Dryer.Setting.IronDryFineAdjust",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_spin_speed_before_drying",
            entity="LaundryCare.Dryer.Setting.SpinSpeedBeforeDrying",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_drying_target",
            entity="LaundryCare.Dryer.Option.DryingTarget",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_refresher",
            entity="LaundryCare.Dryer.Option.Refresher",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_idos2_content",
            entity="LaundryCare.Washer.Setting.IDos2Content",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_idos2_level",
            entity="LaundryCare.Washer.Option.IDos2DosingLevel",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_idos1_level",
            entity="LaundryCare.Washer.Option.IDos1DosingLevel",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_vario_perfect",
            entity="LaundryCare.Common.Option.VarioPerfect",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_hygienic_steam_intensity",
            entity="LaundryCare.Common.Option.HygienicSteamIntensity",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_multiple_soak",
            entity="LaundryCare.Washer.Option.MultipleSoak",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_rinseplus",
            entity="LaundryCare.Washer.Option.RinsePlus",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_spin_speed",
            entity="LaundryCare.Washer.Option.SpinSpeed",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_option_stains",
            entity="LaundryCare.Washer.Option.Stains",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_option_temperature",
            entity="LaundryCare.Washer.Option.Temperature",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_laundry_option_water_and_rinse_plus",
            entity="LaundryCare.Washer.Option.WaterAndRinsePlus",
            has_state_translation=True,
            entity_registry_enabled_default=False,
        ),
    ],
    "number": [
        HCNumberEntityDescription(
            key="number_laundry_brightness",
            entity="LaundryCare.Common.Setting.Brightness",
            native_unit_of_measurement=PERCENTAGE,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_door_light_ring_brightness",
            entity="LaundryCare.Common.Setting.DoorLightRing.Brightness",
            native_unit_of_measurement=PERCENTAGE,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_laundry_spin_class",
            entity="LaundryCare.Dryer.Option.SpinClass",
            native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_idos1_base_level",
            entity="LaundryCare.Washer.Setting.IDos1BaseLevel",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfVolume.MILLILITERS,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_idos2_base_level",
            entity="LaundryCare.Washer.Setting.IDos2BaseLevel",
            entity_category=EntityCategory.CONFIG,
            native_unit_of_measurement=UnitOfVolume.MILLILITERS,
            mode=NumberMode.AUTO,
        ),
    ],
    "switch": [
        HCSwitchEntityDescription(
            key="switch_laundry_end_signal",
            entity="LaundryCare.Common.Setting.EndSignal",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_sound_mute",
            entity="LaundryCare.Common.Setting.Sound.Mute",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_time_light",
            entity="LaundryCare.Common.Setting.TimeLight.Active",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_wrinkle_guard",
            entity="LaundryCare.Common.Setting.WrinkleGuard",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_silent_mode",
            entity="LaundryCare.Common.Option.SilentMode",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_speed_perfect",
            entity="LaundryCare.Common.Option.SpeedPerfect",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_low_temperature_hygiene",
            entity="LaundryCare.Common.Option.LowTemperatureHygiene",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_gentle",
            entity="LaundryCare.Dryer.Option.Gentle",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_half_load",
            entity="LaundryCare.Dryer.Option.HalfLoad",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_hygiene",
            entity="LaundryCare.Dryer.Option.Hygiene",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_idos1_active",
            entity="LaundryCare.Washer.Option.IDos1Active",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_idos2_active",
            entity="LaundryCare.Washer.Option.IDos2Active",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_idos1_active",
            entity="LaundryCare.Washer.Option.IDos1.Active",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_idos2_active",
            entity="LaundryCare.Washer.Option.IDos2.Active",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_intensive_plus",
            entity="LaundryCare.Washer.Option.IntensivePlus",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_less_ironing",
            entity="LaundryCare.Washer.Option.LessIroning",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_silent_wash",
            entity="LaundryCare.Washer.Option.SilentWash",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        generate_washer_speed_perfect,
        HCSwitchEntityDescription(
            key="switch_laundry_soak",
            entity="LaundryCare.Washer.Option.Soak",
            device_class=SwitchDeviceClass.SWITCH,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_prewash",
            entity="LaundryCare.Washer.Option.Prewash",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_rinse_hold",
            entity="LaundryCare.Washer.Option.RinseHold",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_rinse_plus1",
            entity="LaundryCare.Washer.Option.RinsePlus1",
            device_class=SwitchDeviceClass.SWITCH,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_rinse_plus3",
            entity="LaundryCare.Washer.Option.RinsePlus3",
            device_class=SwitchDeviceClass.SWITCH,
            entity_registry_enabled_default=False,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_water_and_rinse_plus1",
            entity="LaundryCare.Washer.Option.WaterAndRinsePlus1",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_water_plus",
            entity="LaundryCare.Washer.Option.WaterPlus",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_disinfectant",
            entity="LaundryCare.Washer.Option.Disinfectant",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_laundry_hygienic_steam",
            entity="LaundryCare.Washer.Option.HygienicSteam",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    ],
    "event_sensor": [generate_laundry_message],
    "light": [
        HCLightEntityDescription(
            key="light_door_ring",
            entity="LaundryCare.Common.Setting.DoorLightRing.Active",
        ),
        HCLightEntityDescription(
            key="light_drum_light",
            entity="LaundryCare.Common.Setting.DrumLight.Active",
        ),
    ],
}
