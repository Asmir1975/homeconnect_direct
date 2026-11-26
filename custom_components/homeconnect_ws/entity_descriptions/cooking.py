"""Description for Cooking Entities."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfMass,
    UnitOfTemperature,
    UnitOfTime,
)

from custom_components.homeconnect_ws.helpers import get_groups_from_regex

from .common import software_messages
from .descriptions_definitions import (
    EntityDescriptions,
    HCBinarySensorEntityDescription,
    HCButtonEntityDescription,
    HCFanEntityDescription,
    HCLightEntityDescription,
    HCNumberEntityDescription,
    HCSelectEntityDescription,
    HCSensorEntityDescription,
    HCSwitchEntityDescription,
    _EntityDescriptionsDefinitionsType,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeconnect_websocket import HomeAppliance


def _append_oven_cavity_extra_status(
    descriptions: EntityDescriptions, appliance: HomeAppliance, group: tuple[str], group_name: str
) -> None:
    """Append additional per-cavity status entities."""
    entity = f"Cooking.Oven.Status.Cavity.{group[0]}.CavitySelector"
    if entity in appliance.entities:
        descriptions["sensor"].append(
            HCSensorEntityDescription(
                key=f"sensor_oven_cavity_selector_{group[0]}",
                translation_key="sensor_oven_cavity_selector",
                translation_placeholders={"group_name": group_name},
                entity=entity,
                device_class=SensorDeviceClass.ENUM,
                force_disabled_default=True,
            )
        )

    entity = f"Cooking.Oven.Status.Cavity.{group[0]}.Level"
    if entity in appliance.entities:
        descriptions["sensor"].append(
            HCSensorEntityDescription(
                key=f"sensor_oven_cavity_level_{group[0]}",
                translation_key="sensor_oven_cavity_level",
                translation_placeholders={"group_name": group_name},
                entity=entity,
                device_class=SensorDeviceClass.ENUM,
                force_disabled_default=True,
            )
        )


def generate_oven_status(appliance: HomeAppliance) -> EntityDescriptions:
    """Get Oven status descriptions."""
    pattern = re.compile(r"^Cooking\.Oven\.Status\.Cavity\.(\d+)\..*$")
    groups = get_groups_from_regex(appliance, pattern)
    descriptions = EntityDescriptions(binary_sensor=[], event_sensor=[], sensor=[])
    for group in groups:
        group_name = f" {int(group[0])}"
        if len(groups) == 1:
            group_name = ""

        # Water Tank
        entities = (
            f"Cooking.Oven.Status.Cavity.{group[0]}.WaterTankUnplugged",
            f"Cooking.Oven.Status.Cavity.{group[0]}.WaterTankEmpty",
        )
        if all(entity in appliance.entities for entity in entities):
            descriptions["event_sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_water_tank_{group[0]}",
                    translation_key="sensor_oven_water_tank",
                    translation_placeholders={"group_name": group_name},
                    entities=entities,
                    device_class=SensorDeviceClass.ENUM,
                    options=["unplugged", "empty", "ok"],
                )
            )

        # Temperatur
        entity = f"Cooking.Oven.Status.Cavity.{group[0]}.CurrentTemperature"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_current_temperature_{group[0]}",
                    translation_key="sensor_oven_current_temperature",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                )
            )

        # Meat probe, only when the appliance has no general entity for it
        entity = f"Cooking.Oven.Status.Cavity.{group[0]}.CurrentMeatprobeTemperature"
        if (
            entity in appliance.entities
            and "Cooking.Oven.Status.CurrentMeatprobeTemperature" not in appliance.entities
        ):
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_cavity_meatprobe_temperature_{group[0]}",
                    translation_key="sensor_oven_cavity_meatprobe_temperature",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                )
            )

        entity = f"Cooking.Oven.Status.Server.Cavity.{group[0]}.MeatProbeSetpointTemperatureCelsius"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_meatprobe_target_temperature_{group[0]}",
                    translation_key="sensor_oven_meatprobe_target_temperature",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                )
            )

        entity = f"Cooking.Oven.Status.Cavity.{group[0]}.MeatprobePlugged"
        if entity in appliance.entities:
            descriptions["binary_sensor"].append(
                HCBinarySensorEntityDescription(
                    key=f"binary_sensor_oven_cavity_meatprobe_plugged_{group[0]}",
                    translation_key="binary_sensor_oven_cavity_meatprobe_plugged",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=BinarySensorDeviceClass.PLUG,
                )
            )

        # Running program, as shown in the app
        entity = f"Cooking.Oven.Status.Cavity.{group[0]}.ProgramName"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_program_name_{group[0]}",
                    translation_key="sensor_oven_program_name",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    force_disabled_default=True,
                )
            )
        for status, key in (("Selectable", "selectable"), ("Startable", "startable")):
            entity = f"Cooking.Oven.Status.Cavity.{group[0]}.{status}"
            if entity in appliance.entities:
                descriptions["binary_sensor"].append(
                    HCBinarySensorEntityDescription(
                        key=f"binary_sensor_oven_cavity_{key}_{group[0]}",
                        translation_key=f"binary_sensor_oven_cavity_{key}",
                        translation_placeholders={"group_name": group_name},
                        entity=entity,
                        force_disabled_default=True,
                    )
                )
        _append_oven_cavity_extra_status(descriptions, appliance, group, group_name)

    # Ovens without a Cavity namespace report the meat probe directly.
    if not groups and "Cooking.Oven.Status.MeatprobePlugged" in appliance.entities:
        descriptions["binary_sensor"].append(
            HCBinarySensorEntityDescription(
                key="binary_sensor_oven_meatprobe_plugged",
                translation_key="binary_sensor_oven_cavity_meatprobe_plugged",
                translation_placeholders={"group_name": ""},
                entity="Cooking.Oven.Status.MeatprobePlugged",
                device_class=BinarySensorDeviceClass.PLUG,
            )
        )
    return descriptions


# Cavity events of HB774G1B1 and their state keys: errors first, everyday events in the
# order they come up, reminders last. The message sensor shows the first active one.
OVEN_MESSAGES = (
    # Errors first, then everyday events in the order they come up, then reminders.
    ("CavityTemperatureTooHigh", "cavity_temperature_too_high"),
    ("OvenLockWhileCoolingDown", "oven_lock_while_cooling_down"),
    ("OperatingTimeLimitReached", "operating_time_limit_reached"),
    ("ForceFlushing", "force_flushing"),
    ("ErrorCodeE0502", "error_code_e0502"),
    ("ErrorDoorLatch", "error_door_latch"),
    ("ErrorSteamSystem", "error_steam_system"),
    ("ApplianceModuleError", "appliance_module_error"),
    ("ErrorPermanentButtonPressing", "error_permanent_button_pressing"),
    ("MaxMeatprobeTemperatureExceeded", "max_meatprobe_temperature_exceeded"),
    ("RegularPreheatFinished", "regular_preheat_finished"),
    ("FastPreheatFinished", "fast_preheat_finished"),
    ("SubsequentCookingRequest", "subsequent_cooking_request"),
    ("InsertFoodNow", "insert_food_now"),
    ("TurnFoodNow", "turn_food_now"),
    ("TurnJointNow", "turn_joint_now"),
    ("TurnFoodNowMeatprobe", "turn_food_now_meatprobe"),
    ("ApplySteamShot", "apply_steam_shot"),
    ("FillWaterContainer", "fill_water_container"),
    ("MeatprobeNecessary", "meatprobe_necessary"),
    ("MeatprobeTemperatureReached", "meatprobe_temperature_reached"),
    ("AlarmClockElapsed", "alarm_clock_elapsed"),
    ("ProgramFinished", "program_finished"),
    ("ProgramAborted", "program_aborted"),
    ("OpenDoor", "open_door"),
    ("CloseDoor", "close_door"),
    ("ToColdForSteamBoost", "too_cold_for_steam_boost"),
    ("InsertFoodLater", "insert_food_later"),
    ("TurnFoodLater", "turn_food_later"),
    ("UnplugMeatprobe", "unplug_meatprobe"),
    ("LeaveDoorOpen", "leave_door_open"),
    ("DescalingReminder", "descaling_reminder"),
    ("PrepareDescaling", "prepare_descaling"),
    ("DescaleBeforeSteam", "descale_before_steam"),
    ("RinseWaterTank", "rinse_water_tank"),
    ("DescalingCompleted", "descaling_completed"),
    ("CavityTemperatureTooHighInfo", "cavity_temperature_too_high_info"),
    ("OpenDoorInfrequently", "open_door_infrequently"),
    ("PyroRemoveAccessory", "pyro_remove_accessory"),
    ("PyrolysisRemoveTank", "pyrolysis_remove_tank"),
    ("AfterPyrolysisCleaning", "after_pyrolysis_cleaning"),
    ("EasyClean", "easy_clean"),
    ("WipeOutCavityEasyClean", "wipe_out_cavity_easy_clean"),
    ("PrepareDrying", "prepare_drying"),
    ("ClockPermanentOn", "clock_permanent_on"),
    ("IsNotShownAgain", "is_not_shown_again"),
)

# Events of HS658GXS7, which uses Cooking.Oven.Event.<Name> without a Cavity
# namespace, most urgent first. Events that also exist per cavity reuse the keys
# of OVEN_MESSAGES.
OVEN_FLAT_MESSAGES = (
    ("CavityTemperatureTooHigh", "cavity_temperature_too_high"),
    ("OperatingTimeLimitReached", "operating_time_limit_reached"),
    ("ForceFlushing", "force_flushing"),
    ("ForceDraining", "force_draining"),
    ("ApplianceModuleError", "appliance_module_error"),
    ("MeatprobeIncompatibleOperation", "meatprobe_incompatible_operation"),
    ("BakingSensorProgramAborted", "baking_sensor_program_aborted"),
    ("WaterContainerEmpty", "water_container_empty"),
    ("InsertWaterContainer", "insert_water_container"),
    ("CloseFrontPanel", "close_front_panel"),
    ("UserInteractionRequired", "user_interaction_required"),
    ("SubsequentCookingRequest", "subsequent_cooking_request"),
    ("PreheatFinished", "regular_preheat_finished"),
    ("EmptyWaterContainer", "empty_water_container"),
    ("WaterContainerNearlyEmpty", "water_container_nearly_empty"),
    ("DescalingRequest", "descaling_request"),
    ("EcolysisRequired", "ecolysis_required"),
)

# Most urgent first; the sensor shows the first one that is active, else "none".
HOOD_FILTER_MESSAGES = (
    ("Cooking.Common.Event.Hood.CarbonFilterMaxSaturationReached", "carbon_filter_saturated"),
    ("Cooking.Common.Event.Hood.GreaseFilterMaxSaturationReached", "grease_filter_saturated"),
    (
        "Cooking.Common.Event.Hood.RegenerativeCarbonFilterMaxSaturationReached",
        "regenerative_carbon_filter_saturated",
    ),
    (
        "Cooking.Common.Event.Hood.CarbonFilterMaxSaturationNearlyReached",
        "carbon_filter_nearly_saturated",
    ),
    (
        "Cooking.Common.Event.Hood.GreaseFilterMaxSaturationNearlyReached",
        "grease_filter_nearly_saturated",
    ),
    (
        "Cooking.Common.Event.Hood.RegenerativeCarbonFilterMaxSaturationNearlyReached",
        "regenerative_carbon_filter_nearly_saturated",
    ),
)


def generate_hood_filter_message(appliance: HomeAppliance) -> HCSensorEntityDescription | None:
    """Get the most saturated filter or a pending software update, else "none"."""
    messages = [
        (entity, key) for entity, key in HOOD_FILTER_MESSAGES if entity in appliance.entities
    ]
    if not messages:
        return None
    messages += software_messages(appliance)
    return HCSensorEntityDescription(
        key="sensor_hood_filter_message",
        entities=tuple(entity for entity, _ in messages),
        device_class=SensorDeviceClass.ENUM,
        options=[key for _, key in messages] + ["none"],
    )


def generate_oven_event(appliance: HomeAppliance) -> EntityDescriptions:
    """Get Oven event descriptions."""
    pattern = re.compile(r"^Cooking\.Oven\.Event\.Cavity\.([0-9]*)\..*$")
    groups = get_groups_from_regex(appliance, pattern)
    descriptions = EntityDescriptions(binary_sensor=[], event_sensor=[])
    for group in groups:
        group_name = f" {int(group[0])}"
        if len(groups) == 1:
            group_name = ""

        # AlarmClockElapsed
        entity = f"Cooking.Oven.Event.Cavity.{group[0]}.AlarmClockElapsed"
        if entity in appliance.entities:
            descriptions["binary_sensor"].append(
                HCBinarySensorEntityDescription(
                    key=f"binary_sensor_oven_alarm_clock_elapsed_{group[0]}",
                    translation_key="binary_sensor_oven_alarm_clock_elapsed",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    value_on={"Present", "Confirmed"},
                    value_off={"Off"},
                )
            )

        messages = [
            (f"Cooking.Oven.Event.Cavity.{group[0]}.{event}", key)
            for event, key in OVEN_MESSAGES
            if f"Cooking.Oven.Event.Cavity.{group[0]}.{event}" in appliance.entities
        ]
        if messages:
            if group == min(groups):
                messages += software_messages(appliance)
            descriptions["event_sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_oven_message_{group[0]}",
                    translation_key="sensor_oven_message",
                    translation_placeholders={"group_name": group_name},
                    entities=tuple(entity for entity, _ in messages),
                    device_class=SensorDeviceClass.ENUM,
                    options=[key for _, key in messages] + ["none"],
                )
            )

    if not groups:
        # Ovens without a Cavity namespace report their events directly.
        messages = [
            (f"Cooking.Oven.Event.{event}", key)
            for event, key in OVEN_FLAT_MESSAGES
            if f"Cooking.Oven.Event.{event}" in appliance.entities
        ]
        if messages:
            messages += software_messages(appliance)
            descriptions["event_sensor"].append(
                HCSensorEntityDescription(
                    key="sensor_oven_message",
                    translation_placeholders={"group_name": ""},
                    entities=tuple(entity for entity, _ in messages),
                    device_class=SensorDeviceClass.ENUM,
                    options=[key for _, key in messages] + ["none"],
                )
            )

    return descriptions


def generate_oven_settings(appliance: HomeAppliance) -> EntityDescriptions:
    """Get Oven status descriptions."""
    pattern = re.compile(r"^Cooking\.Oven\.Setting\.Cavity\.([0-9]*)\..*$")
    groups = get_groups_from_regex(appliance, pattern)
    descriptions = EntityDescriptions(number=[])
    for group in groups:
        group_name = f" {int(group[0])}"

        # AlarmClock
        entity = f"Cooking.Oven.Setting.Cavity.{group[0]}.AlarmClock"
        elapsed = f"Cooking.Oven.Event.Cavity.{group[0]}.AlarmClockElapsed"
        if entity in appliance.entities:
            descriptions["number"].append(
                HCNumberEntityDescription(
                    key=f"number_oven_setting_{group[0]}_alarm_clock",
                    translation_key="number_setting_alarm_clock",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=NumberDeviceClass.DURATION,
                    native_unit_of_measurement=UnitOfTime.SECONDS,
                    native_max_value=86399,
                    mode=NumberMode.BOX,
                    entities=[elapsed] if elapsed in appliance.entities else None,
                    zero_when_event_present=elapsed in appliance.entities,
                )
            )

    return descriptions


HOOD_FAN_ENTITIES = [
    "Cooking.Common.Option.Hood.VentingLevel",
    "Cooking.Common.Option.Hood.IntensiveLevel",
]

HOOD_VENTING_PROGRAM = "Cooking.Common.Program.Hood.Venting"


def generate_hood_fan(appliance: HomeAppliance) -> HCFanEntityDescription:
    """Get Hood Fan description."""
    program = appliance.programs.get(HOOD_VENTING_PROGRAM)
    if program is None:
        return None
    program_option_uids = {option.uid for option in program.options}
    available_entities = [
        entity
        for entity in HOOD_FAN_ENTITIES
        if entity in appliance.entities and appliance.entities[entity].uid in program_option_uids
    ]
    if available_entities:
        return HCFanEntityDescription(
            key="fan_hood",
            entities=available_entities,
            default_program=HOOD_VENTING_PROGRAM,
        )
    return None


def generate_hood_level_select(appliance: HomeAppliance) -> HCFanEntityDescription | None:
    """
    Get the Hood level Select description.

    Same Venting Program option matching as generate_hood_fan(), but exposed
    as a single always-visible Select instead of a Fan. Not
    wired into COOKING_ENTITY_DESCRIPTIONS's normal "fan" key on purpose.
    """
    program = appliance.programs.get(HOOD_VENTING_PROGRAM)
    if program is None:
        return None
    program_option_uids = {option.uid for option in program.options}
    available_entities = [
        entity
        for entity in HOOD_FAN_ENTITIES
        if entity in appliance.entities and appliance.entities[entity].uid in program_option_uids
    ]
    if available_entities:
        return HCFanEntityDescription(
            key="select_hood_venting_level",
            entities=available_entities,
            default_program=HOOD_VENTING_PROGRAM,
        )
    return None


def _is_hob_extension_zone(zone: str, zones: set[str]) -> bool:
    """
    Return True if the zone extends a main zone that is also present.

    Seen on EX851LYV5E: the extension zones 120, 121, 201, 301, 340 and 341 sit next
    to the main zones 100, 200 and 300 and never report a value for any of their
    16 UIDs. Hobs without zone 100 use 120 as a normal zone (PID775HC1E: zones 120,
    300 and 400, where 120 is the 32 cm zone on the left).

    Seen on EX975KXW1E: zones 120 and 340 next to 100 and 300 report their values and
    have a JoinZone status, which the EX851LYV5E zones lack. These are kept, see
    generate_hob_zones.
    """
    base = f"{zone[:1]}00"
    return zone != base and base in zones


def _append_hob_zone_program_status(
    descriptions: EntityDescriptions, appliance: HomeAppliance, group: tuple[str], group_name: str
) -> None:
    """Append ActiveProgram/SelectedProgram for a zone."""
    entity = f"Cooking.Hob.Status.Zone.{group[0]}.ActiveProgram"
    if entity in appliance.entities:
        descriptions["sensor"].append(
            HCSensorEntityDescription(
                key=f"sensor_hob_zone_{group[0]}_active_program",
                translation_key="sensor_hob_zone_active_program",
                translation_placeholders={"group_name": group_name},
                entity=entity,
                force_disabled_default=True,
            )
        )
    entity = f"Cooking.Hob.Status.Zone.{group[0]}.SelectedProgram"
    if entity in appliance.entities:
        descriptions["sensor"].append(
            HCSensorEntityDescription(
                key=f"sensor_hob_zone_{group[0]}_selected_program",
                translation_key="sensor_hob_zone_selected_program",
                translation_placeholders={"group_name": group_name},
                entity=entity,
                force_disabled_default=True,
            )
        )


def generate_hob_zones(appliance: HomeAppliance) -> HCFanEntityDescription:
    """Get Oven status descriptions."""
    pattern = re.compile(r"^Cooking\.Hob\.Status\.Zone\.([0-9]*)\..*$")
    all_groups = get_groups_from_regex(appliance, pattern)
    zones = {g[0] for g in all_groups}
    # Extension zones without a JoinZone status never reported a value, see
    # _is_hob_extension_zone. Those with one are kept but disabled by default.
    joined_extensions = {
        g[0]
        for g in all_groups
        if _is_hob_extension_zone(g[0], zones)
        and f"Cooking.Hob.Status.Zone.{g[0]}.JoinZone" in appliance.entities
    }
    groups = {
        g
        for g in all_groups
        if not _is_hob_extension_zone(g[0], zones) or g[0] in joined_extensions
    }
    descriptions = EntityDescriptions(sensor=[])
    for group in groups:
        group_name = f" {int(group[0])}"
        zone_state = appliance.entities.get(f"Cooking.Hob.Status.Zone.{group[0]}.State")
        force_disabled_default = (
            zone_state is not None and zone_state.value == "NotSelectable"
        ) or group[0] in joined_extensions

        _append_hob_zone_program_status(descriptions, appliance, group, group_name)

        # State
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.State"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_state",
                    translation_key="sensor_hob_zone_state",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.ENUM,
                    has_state_translation=True,
                    force_disabled_default=force_disabled_default,
                    extra_attributes=[
                        {
                            "name": "Type",
                            "entity": f"Cooking.Hob.Status.Zone.{group[0]}.Type",
                        }
                    ],
                )
            )

        # OperationState
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.OperationState"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_operationstate",
                    translation_key="sensor_hob_zone_operationstate",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.ENUM,
                    has_state_translation=True,
                    force_disabled_default=force_disabled_default,
                )
            )

        # PowerLevel
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.PowerLevel"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_power_level",
                    translation_key="sensor_hob_zone_power_level",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.ENUM,
                    has_state_translation=True,
                    force_disabled_default=force_disabled_default,
                )
            )

        # FryingSensorLevel
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.FryingSensorLevel"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_frying_sensor_level",
                    translation_key="sensor_hob_zone_frying_sensor_level",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.ENUM,
                    has_state_translation=True,
                    force_disabled_default=force_disabled_default,
                )
            )

        # CookingSensorLevel
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.CookingSensorLevel"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_cooking_sensor_level",
                    translation_key="sensor_hob_zone_cooking_sensor_level",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.ENUM,
                    force_disabled_default=True,
                )
            )

        # CurrentTemperature
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.CurrentTemperature"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_current_temperature",
                    translation_key="sensor_hob_zone_current_temperature",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.TEMPERATURE,
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    force_disabled_default=force_disabled_default,
                )
            )

        # HeatupProgress
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.HeatupProgress"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_heatup_progress",
                    translation_key="sensor_hob_zone_heatup_progress",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    native_unit_of_measurement=PERCENTAGE,
                    force_disabled_default=force_disabled_default,
                )
            )

        # Duration
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.Duration"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_duration",
                    translation_key="sensor_hob_zone_duration",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.DURATION,
                    native_unit_of_measurement=UnitOfTime.SECONDS,
                    suggested_unit_of_measurement=UnitOfTime.MINUTES,
                    force_disabled_default=force_disabled_default,
                )
            )

        # ElapsedProgramTime
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.ElapsedProgramTime"
        extra_entity = f"Cooking.Hob.Status.Zone.{group[0]}.ElapsedProgramTime.AutoCounting"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_elapsed_program_time",
                    translation_key="sensor_hob_zone_elapsed_program_time",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.DURATION,
                    native_unit_of_measurement=UnitOfTime.SECONDS,
                    suggested_unit_of_measurement=UnitOfTime.MINUTES,
                    extra_attributes=[{"name": "Auto Counting", "entity": extra_entity}],
                    force_disabled_default=force_disabled_default,
                    # A zone switched off alone resets this itself via Ready; the
                    # whole hob going straight to Inactive keeps the last value.
                    reset_when_operation_state_terminal=True,
                )
            )

        # RemainingProgramTime
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.RemainingProgramTime"
        extra_entity = f"Cooking.Hob.Status.Zone.{group[0]}.RemainingProgramTime.AutoCounting"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_remaining_program_time",
                    translation_key="sensor_hob_zone_remaining_program_time",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    device_class=SensorDeviceClass.DURATION,
                    native_unit_of_measurement=UnitOfTime.SECONDS,
                    suggested_unit_of_measurement=UnitOfTime.MINUTES,
                    extra_attributes=[{"name": "Auto Counting", "entity": extra_entity}],
                    force_disabled_default=force_disabled_default,
                )
            )

        # ProgramProgress
        entity = f"Cooking.Hob.Status.Zone.{group[0]}.ProgramProgress"
        if entity in appliance.entities:
            descriptions["sensor"].append(
                HCSensorEntityDescription(
                    key=f"sensor_hob_zone_{group[0]}_program_progress",
                    translation_key="sensor_hob_zone_program_progress",
                    translation_placeholders={"group_name": group_name},
                    entity=entity,
                    native_unit_of_measurement=PERCENTAGE,
                    force_disabled_default=force_disabled_default,
                )
            )

    return descriptions


def generate_hood_light(appliance: HomeAppliance) -> HCFanEntityDescription:
    """Get Hood light descriptions."""
    if "Cooking.Hood.Setting.ColorTemperaturePercent" in appliance.entities:
        return HCLightEntityDescription(
            key="light_cooking_lighting",
            entity="Cooking.Common.Setting.Lighting",
            brightness_entity="Cooking.Common.Setting.LightingBrightness",
            color_temperature_entity="Cooking.Hood.Setting.ColorTemperaturePercent",
        )

    if (
        "Cooking.Hood.Setting.LightingBrightness" in appliance.entities
        or "Cooking.Common.Setting.LightingBrightness" in appliance.entities
    ):
        return HCLightEntityDescription(
            key="light_cooking_lighting",
            entity="Cooking.Common.Setting.Lighting",
            brightness_entity="Cooking.Common.Setting.LightingBrightness",
        )

    if "Cooking.Common.Setting.Lighting" in appliance.entities:
        return HCLightEntityDescription(
            key="light_cooking_lighting",
            entity="Cooking.Common.Setting.Lighting",
        )
    return None


def generate_hood_ambient_light(appliance: HomeAppliance) -> HCFanEntityDescription:
    """Get Hood light descriptions."""
    if (
        "BSH.Common.Setting.AmbientLightCustomColor" in appliance.entities
        and "BSH.Common.Setting.AmbientLightColor" in appliance.entities
    ):
        return HCLightEntityDescription(
            key="light_cooking_ambient_lighting",
            entity="BSH.Common.Setting.AmbientLightEnabled",
            brightness_entity="BSH.Common.Setting.AmbientLightBrightness",
            color_entity="BSH.Common.Setting.AmbientLightCustomColor",
            color_mode_entity="BSH.Common.Setting.AmbientLightColor",
        )

    if "BSH.Common.Setting.AmbientLightBrightness" in appliance.entities:
        return HCLightEntityDescription(
            key="light_cooking_ambient_lighting",
            entity="BSH.Common.Setting.AmbientLightEnabled",
            brightness_entity="BSH.Common.Setting.AmbientLightBrightness",
        )

    if "BSH.Common.Setting.AmbientLightEnabled" in appliance.entities:
        return HCLightEntityDescription(
            key="light_cooking_ambient_lighting",
            entity="BSH.Common.Setting.AmbientLightEnabled",
        )
    return None


def generate_oven_cavity_light(appliance: HomeAppliance) -> HCLightEntityDescription | None:
    """Get oven cavity light description."""
    power = "Cooking.Oven.Setting.Light.Cavity.001.Power"
    brightness = "Cooking.Oven.Setting.Light.Cavity.001.Brightness"
    if power not in appliance.entities:
        return None

    return HCLightEntityDescription(
        key="light_oven_cavity",
        entity=power,
        brightness_entity=brightness if brightness in appliance.entities else None,
    )


def _generate_hood_favorite_functionality(
    slot: str,
) -> Callable[[HomeAppliance], HCSelectEntityDescription | None]:
    """Get the Select for what a hood favorite button press does."""

    def generate(appliance: HomeAppliance) -> HCSelectEntityDescription | None:
        # Ovens and dishwashers share this Setting name with other values
        # (Off/Program), where writing it would drop a saved favorite.
        entity = f"BSH.Common.Setting.Favorite.{slot}.Functionality"
        if appliance.info.get("type") != "Hood" or entity not in appliance.entities:
            return None
        return HCSelectEntityDescription(
            key=f"select_hood_favorite_{slot}_functionality",
            entity=entity,
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        )

    return generate


# Most urgent first; the sensor shows the first one that is active, else "none".
HOB_MESSAGES = (
    ("Cooking.Common.Event.ApplianceOverheated", "appliance_overheated"),
    ("Cooking.Common.Event.ApplianceModuleError", "appliance_module_error"),
    ("Cooking.Common.Event.ConfirmActionAtAppliance", "confirm_action_at_appliance"),
    ("Cooking.Common.Event.PreheatFinished", "preheat_finished"),
)


def generate_hob_message(appliance: HomeAppliance) -> HCSensorEntityDescription | None:
    """Get the most urgent active hob message, else "none"."""
    messages = [(entity, key) for entity, key in HOB_MESSAGES if entity in appliance.entities]
    if not messages:
        return None
    messages += software_messages(appliance)
    return HCSensorEntityDescription(
        key="sensor_hob_message",
        entities=tuple(entity for entity, _ in messages),
        device_class=SensorDeviceClass.ENUM,
        options=[key for _, key in messages] + ["none"],
    )


COOKING_ENTITY_DESCRIPTIONS: _EntityDescriptionsDefinitionsType = {
    "sensor": [
        HCSensorEntityDescription(
            key="sensor_hob_ventilation",
            entity="Cooking.Hob.Setting.Ventilation",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_oven_steam_assist_level",
            entity="Cooking.Oven.Option.SteamAssistLevel",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_interval_time_off",
            entity="Cooking.Hood.Setting.IntervalTimeOff",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            force_disabled_default=True,
        ),
        HCSensorEntityDescription(
            key="sensor_interval_time_on",
            entity="Cooking.Hood.Setting.IntervalTimeOn",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            force_disabled_default=True,
        ),
        HCSensorEntityDescription(
            key="sensor_delayed_shutoff_time",
            entity="Cooking.Hood.Setting.DelayedShutOffTime",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            force_disabled_default=True,
        ),
        HCSensorEntityDescription(
            key="sensor_heatup_progress",
            entity="Cooking.Oven.Option.HeatupProgress",
            native_unit_of_measurement=PERCENTAGE,
        ),
        HCSensorEntityDescription(
            key="sensor_grease_filter_saturation",
            entity="Cooking.Hood.Status.GreaseFilterSaturation",
            native_unit_of_measurement=PERCENTAGE,
        ),
        HCSensorEntityDescription(
            key="sensor_carbon_filter_saturation",
            entity="Cooking.Hood.Status.CarbonFilterSaturation",
            native_unit_of_measurement=PERCENTAGE,
        ),
        HCSensorEntityDescription(
            key="sensor_regenerative_carbon_filter_life_cycle",
            entity="Cooking.Hood.Status.RegenerativeCarbonFilterLifeCycle",
            native_unit_of_measurement=PERCENTAGE,
        ),
        HCSensorEntityDescription(
            key="sensor_regenerative_carbon_filter_saturation",
            entity="Cooking.Hood.Status.RegenerativeCarbonFilterSaturation",
            native_unit_of_measurement=PERCENTAGE,
            force_disabled_default=True,
        ),
        HCSensorEntityDescription(
            key="sensor_oven_current_temperature",
            entity="Cooking.Oven.Status.CurrentCavityTemperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
        HCSensorEntityDescription(
            key="sensor_oven_current_meatprobe_temperature",
            entity="Cooking.Oven.Status.CurrentMeatprobeTemperature",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        ),
    ],
    "event_sensor": [
        generate_hood_filter_message,
        generate_hob_message,
        HCSensorEntityDescription(
            key="sensor_oven_water_tank",
            translation_placeholders={"group_name": ""},
            entities=(
                "Cooking.Oven.Status.WaterTankUnplugged",
                "Cooking.Oven.Status.WaterTankEmpty",
            ),
            device_class=SensorDeviceClass.ENUM,
            options=["unplugged", "empty", "ok"],
        ),
    ],
    "dynamic": [
        generate_oven_status,
        generate_hob_zones,
        generate_oven_event,
        generate_oven_settings,
    ],
    "number": [
        HCNumberEntityDescription(
            key="number_oven_setpoint_temperature",
            entity="Cooking.Oven.Option.SetpointTemperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_oven_weight",
            entity="Cooking.Oven.Option.Weight",
            device_class=NumberDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.GRAMS,
            mode=NumberMode.AUTO,
            force_disabled_default=True,
        ),
        HCNumberEntityDescription(
            key="number_oven_display_brightness",
            entity="Cooking.Oven.Setting.DisplayBrightness",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_oven_meatprobe_temperature",
            entity="Cooking.Oven.Option.MeatProbeTemperature",
            device_class=NumberDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_oven_sound_volume",
            entity="Cooking.Oven.Setting.SoundVolume",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.SLIDER,
        ),
        HCNumberEntityDescription(
            key="number_hob_automatic_timer",
            entity="Cooking.Hob.Setting.AutomaticTimer",
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.SLIDER,
        ),
        HCNumberEntityDescription(
            key="number_hood_interval_off",
            entity="Cooking.Hood.Setting.IntervalTimeOff",
            device_class=NumberDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
            enforce_step=True,
        ),
        HCNumberEntityDescription(
            key="number_hood_interval_on",
            entity="Cooking.Hood.Setting.IntervalTimeOn",
            device_class=NumberDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
            enforce_step=True,
        ),
        HCNumberEntityDescription(
            key="number_hood_delayed_shutoff_time",
            entity="Cooking.Hood.Setting.DelayedShutOffTime",
            device_class=NumberDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
            enforce_step=True,
        ),
        HCNumberEntityDescription(
            key="number_hood_boost_time",
            entity="Cooking.Hood.Setting.BoostTime",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_hood_sensor_sensitivity",
            entity="Cooking.Hood.Setting.SensorSensitivity",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_hood_automatic_sensitivity",
            entity="Cooking.Hood.Setting.AutomaticSensitivity",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.AUTO,
        ),
        HCNumberEntityDescription(
            key="number_hood_interval_total_time",
            entity="Cooking.Hood.Setting.IntervalTotalExecutionTime",
            device_class=NumberDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.BOX,
            enforce_step=True,
        ),
    ],
    "select": [
        HCSelectEntityDescription(
            key="select_oven_water_hardness",
            entity="Cooking.Oven.Setting.WaterHardness",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_level",
            entity="Cooking.Oven.Option.Level",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_oven_steam_assist_level",
            entity="Cooking.Oven.Option.SteamAssistLevel",
            has_state_translation=True,
            sent_with_start=True,
        ),
        HCSelectEntityDescription(
            key="select_oven_used_heating_mode",
            entity="Cooking.Oven.Option.UsedHeatingMode",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_pyrolysis_level",
            entity="Cooking.Oven.Option.PyrolysisLevel",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_oven_child_lock_setting",
            entity="Cooking.Oven.Setting.ConfigureChildLock",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_switch_on_delay",
            entity="Cooking.Oven.Setting.SwitchOnDelay",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_cooling_fan_runtime",
            entity="Cooking.Oven.Setting.CoolingFanRunOnTime",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_signal_duration",
            entity="Cooking.Oven.Setting.SignalDuration",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_interval_stage",
            entity="Cooking.Hood.Setting.IntervalStage",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_hob_ventilation",
            entity="Cooking.Hob.Setting.Ventilation",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_automatic_key_lock",
            entity="Cooking.Hob.Setting.AutomaticKeyLock",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_buzzer_beep_level",
            entity="Cooking.Hob.Setting.BuzzerBeepLevel",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_end_timer_signal_duration",
            entity="Cooking.Hob.Setting.EndTimerSignalduration",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_bridge_zone_mode",
            entity="Cooking.Hob.Setting.BridgeZoneMode",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_management",
            entity="Cooking.Hob.Setting.PowerManagement",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_energy_consumption_indication",
            entity="Cooking.Hob.Setting.EnergyConsumptionIndication",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_hood_automatic_start",
            entity="Cooking.Hob.Setting.HoodAutomaticStart",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_hood_after_run",
            entity="Cooking.Hob.Setting.HoodAfterRun",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_hood_automatic_light_on",
            entity="Cooking.Hob.Setting.HoodAutomaticLightOn",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_hood_automatic_light_off",
            entity="Cooking.Hob.Setting.HoodAutomaticLightOff",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_front_left",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueFrontLeft",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_middle_left",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueMiddleLeft",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_rear_left",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueRearLeft",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_front_right",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueFrontRight",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_middle_right",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueMiddleRight",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hob_power_move_rear_right",
            entity="Cooking.Hob.Setting.PowerMoveModeDefaultValueRearRight",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_clock_display",
            entity="Cooking.Oven.Setting.ClockDisplay",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_clock_prompt",
            entity="Cooking.Oven.Setting.ClockPrompt",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_dishes",
            entity="Cooking.Oven.Setting.Dishes",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_regional_dishes",
            entity="Cooking.Oven.Setting.RegionalDishes",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_count_up_timer",
            entity="Cooking.Oven.Setting.CountUpTimer",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_startup_menu",
            entity="Cooking.Oven.Setting.StartupMenu",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_operation_after_restart",
            entity="Cooking.Oven.Setting.OperationAfterRestart",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_oven_cavity_illumination",
            entity="Cooking.Oven.Setting.CavityIllumination",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_delayed_shutoff_stage",
            entity="Cooking.Hood.Setting.DelayedShutOffStage",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_hood_carbon_filter_type",
            entity="Cooking.Hood.Setting.CarbonFilterType",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_ambient_light_color",
            entity="BSH.Common.Setting.AmbientLightColor",
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_hood_light_startup",
            entity="Cooking.Hood.Setting.WorkingLightStartupSetting",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_light_shutdown",
            entity="Cooking.Hood.Setting.WorkingLightShutdownSetting",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_color_temperature",
            entity="Cooking.Hood.Setting.ColorTemperature",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_ventilation_startup",
            entity="Cooking.Hood.Setting.VentilationStartupSetting",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_ventilation_shutdown",
            entity="Cooking.Hood.Setting.VentilationShutdownSetting",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_ventilation_profile",
            entity="Cooking.Hood.Setting.VentilationProfileOperating",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSelectEntityDescription(
            key="select_hood_filter_notification",
            entity="Cooking.Hood.Setting.FilterSaturationNotificationInterval",
            has_state_translation=True,
            entity_category=EntityCategory.CONFIG,
        ),
        _generate_hood_favorite_functionality("001"),
        _generate_hood_favorite_functionality("002"),
    ],
    "switch": [
        HCSwitchEntityDescription(
            key="switch_hood_interval_total_time_limitation",
            entity="Cooking.Hood.Setting.IntervalTotalExecutionTimeLimitation",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_fast_pre_heat",
            entity="Cooking.Oven.Option.FastPreHeat",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_steam_boost",
            entity="Cooking.Oven.Option.SteamBoost",
            device_class=SwitchDeviceClass.SWITCH,
            sent_with_start=True,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_button_tones",
            entity="Cooking.Oven.Setting.ButtonTones",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_light_during_operation",
            entity="Cooking.Oven.Setting.OvenLightDuringOperation",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_sabbath_mode",
            entity="Cooking.Oven.Setting.SabbathMode",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_night_dimout",
            entity="Cooking.Oven.Setting.NightDimout",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_fast_pre_heat_setting",
            entity="Cooking.Oven.Setting.FastPreHeat",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_telescopic_slide_out",
            entity="Cooking.Oven.Setting.TeloscopicSlideOutRefited",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_oven_display_brand_logo",
            entity="Cooking.Oven.Setting.DisplayBrandLogo",
            device_class=SwitchDeviceClass.SWITCH,
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_hood_silence_mode",
            entity="Cooking.Hood.Setting.NoiseReduction",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    ],
    "light": [generate_hood_light, generate_hood_ambient_light, generate_oven_cavity_light],
    "fan": [generate_hood_fan],
    "hood_level": [generate_hood_level_select],
    "button": [
        HCButtonEntityDescription(
            key="button_hood_carbon_filter_reset",
            entity="Cooking.Common.Command.Hood.CarbonFilterReset",
            entity_category=EntityCategory.CONFIG,
        ),
        HCButtonEntityDescription(
            key="button_hood_grease_filter_reset",
            entity="Cooking.Common.Command.Hood.GreaseFilterReset",
            entity_category=EntityCategory.CONFIG,
        ),
        HCButtonEntityDescription(
            key="button_hood_regenerative_carbon_filter_reset",
            entity="Cooking.Common.Command.Hood.RegenerativeCarbonFilterReset",
            entity_category=EntityCategory.CONFIG,
            force_disabled_default=True,
        ),
        HCButtonEntityDescription(
            key="button_hood_regenerative_carbon_filter_lifetime_reset",
            entity="Cooking.Common.Command.Hood.RegenerativeCarbonFilterLifeTimeReset",
            entity_category=EntityCategory.CONFIG,
        ),
    ],
    "binary_sensor": [
        HCBinarySensorEntityDescription(
            key="binary_sensor_hob_join_zone",
            entity="Cooking.Hob.Option.JoinZone",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_hood_regenerative_carbon_filter_lifetime_exceeded",
            entity="Cooking.Common.Event.Hood.RegenerativeCarbonFilterLifeTimeExceeded",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            force_disabled_default=True,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
        HCBinarySensorEntityDescription(
            key="binary_sensor_hood_regenerative_carbon_filter_lifetime_nearly_exceeded",
            entity="Cooking.Common.Event.Hood.RegenerativeCarbonFilterLifeTimeNearlyExceeded",
            entity_category=EntityCategory.DIAGNOSTIC,
            device_class=BinarySensorDeviceClass.PROBLEM,
            force_disabled_default=True,
            value_on={"Present", "Confirmed"},
            value_off={"Off"},
        ),
    ],
}
