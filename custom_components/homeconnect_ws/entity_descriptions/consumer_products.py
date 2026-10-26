"""Description for ConsumerProducts Entities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.number import NumberDeviceClass, NumberMode
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.const import EntityCategory, UnitOfVolume
from homeconnect_websocket.entities import Access

from custom_components.homeconnect_ws.coffee_quantity import FILL_QUANTITY

from .descriptions_definitions import (
    EntityDescriptions,
    HCBinarySensorEntityDescription,
    HCNumberEntityDescription,
    HCSelectEntityDescription,
    HCSensorEntityDescription,
    HCSwitchEntityDescription,
)

if TYPE_CHECKING:
    from homeconnect_websocket import HomeAppliance
    from homeconnect_websocket.entities import Entity as HcEntity

    from .descriptions_definitions import _EntityDescriptionsDefinitionsType


def generate_bean_container_empty(
    appliance: HomeAppliance,
) -> HCBinarySensorEntityDescription | None:
    """Get the bean container sensor, empty when the appliance reports it or asks for beans."""
    entities = tuple(
        name
        for name in (
            "ConsumerProducts.CoffeeMaker.Event.BeanContainerEmpty",
            "ConsumerProducts.CoffeeMaker.Event.RefillEmptyBeanContainer",
        )
        if name in appliance.entities
    )
    if not entities:
        return None
    return HCBinarySensorEntityDescription(
        key="binary_sensor_bean_container_empty",
        entities=entities,
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_on={"Present"},
        value_off={"Off", "Confirmed"},
    )


CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS: _EntityDescriptionsDefinitionsType = {
    "binary_sensor": [
        generate_bean_container_empty,
        HCBinarySensorEntityDescription(
            key="binary_sensor_child_lock_active",
            entity="ConsumerProducts.CoffeeMaker.Status.ChildLockActive",
            entity_category=EntityCategory.DIAGNOSTIC,
            force_disabled_default=True,
        ),
    ],
    "event_sensor": [
        HCSensorEntityDescription(
            key="sensor_drip_tray",
            entities=[
                "ConsumerProducts.CoffeeMaker.Event.DripTrayFull",
                "ConsumerProducts.CoffeeMaker.Event.DripTrayNotInserted",
            ],
            device_class=SensorDeviceClass.ENUM,
            options=["full", "not_inserted", "ok"],
        ),
    ],
    "select": [
        HCSelectEntityDescription(
            key="select_coffee_temperature",
            entity="ConsumerProducts.CoffeeMaker.Option.CoffeeTemperature",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_bean_amount",
            entity="ConsumerProducts.CoffeeMaker.Option.BeanAmount",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_beverage_size",
            entity="ConsumerProducts.CoffeeMaker.Option.BeverageSize",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_coffee_milk_ratio",
            entity="ConsumerProducts.CoffeeMaker.Option.CoffeeMilkRatio",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_hot_water_temperature",
            entity="ConsumerProducts.CoffeeMaker.Option.HotWaterTemperature",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_flow_rate",
            entity="ConsumerProducts.CoffeeMaker.Option.FlowRate",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_coarsness",
            entity="ConsumerProducts.CoffeeMaker.Option.Coarsness",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_coffee_strength",
            entity="ConsumerProducts.CoffeeMaker.Option.CoffeeStrength",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_aroma_select",
            entity="ConsumerProducts.CoffeeMaker.Option.AromaSelect",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_bean_container",
            entity="ConsumerProducts.CoffeeMaker.Option.BeanContainerSelection",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_cups",
            entity="ConsumerProducts.CoffeeMaker.Option.Cups",
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_favorite_order",
            entity="ConsumerProducts.CoffeeMaker.Setting.FavoriteOrder",
            device_class=SensorDeviceClass.ENUM,
            entity_category=EntityCategory.CONFIG,
            has_state_translation=True,
        ),
    ],
    "switch": [
        HCSwitchEntityDescription(
            key="switch_multiple_beverages",
            entity="ConsumerProducts.CoffeeMaker.Option.MultipleBeverages",
            device_class=SwitchDeviceClass.SWITCH,
        ),
        HCSwitchEntityDescription(
            key="switch_cup_warmer",
            entity="ConsumerProducts.CoffeeMaker.Setting.CupWarmer",
            device_class=SwitchDeviceClass.SWITCH,
        ),
    ],
    "number": [
        HCNumberEntityDescription(
            key="number_fill_quantity",
            entity="ConsumerProducts.CoffeeMaker.Option.FillQuantity",
            device_class=NumberDeviceClass.VOLUME,
            native_unit_of_measurement=UnitOfVolume.MILLILITERS,
            mode=NumberMode.BOX,
        )
    ],
    "sensor": [
        HCSensorEntityDescription(
            key="sensor_countdown_calc_n_clean",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCountdownCalcNClean",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        HCSensorEntityDescription(
            key="sensor_countdown_cleaning",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCountdownCleaning",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        HCSensorEntityDescription(
            key="sensor_countdown_descaling",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCountdownDescaling",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        HCSensorEntityDescription(
            key="sensor_countdown_water_filter",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCountdownWaterfilter",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        HCSensorEntityDescription(
            key="sensor_count_ristretto_espresso",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterRistrettoEspresso",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_coffee",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffee",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_coffee_milk",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterCoffeeAndMilk",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_frothy_milk",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterFrothyMilk",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_hot_milk",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotMilk",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_hot_water",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotWater",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_hot_water_cups",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterHotWaterCups",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_count_powder_coffee",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterPowderCoffee",
            entity_registry_enabled_default=False,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        HCSensorEntityDescription(
            key="sensor_coffeemaker_process_phase",
            entity="ConsumerProducts.CoffeeMaker.Status.ProcessPhase",
            entity_registry_enabled_default=False,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
    ],
}


# Profile-backed coffee maker settings.
CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("switch", []).extend(
    [
        HCSwitchEntityDescription(
            key="switch_eq700_skip_rinse_on",
            entity="ConsumerProducts.CoffeeMaker.Setting.SkipRinseOn",
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_eq700_key_tones",
            entity="ConsumerProducts.CoffeeMaker.Setting.KeyTones",
            entity_category=EntityCategory.CONFIG,
        ),
        HCSwitchEntityDescription(
            key="switch_eq700_maintenance_tone",
            entity="ConsumerProducts.CoffeeMaker.Setting.MaintenanceTone",
            entity_category=EntityCategory.CONFIG,
        ),
    ]
)

CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("select", []).extend(
    [
        HCSelectEntityDescription(
            key="select_eq700_switch_off_after",
            entity="ConsumerProducts.CoffeeMaker.Setting.SwitchOffAfter",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eq700_coffee_milk_order",
            entity="ConsumerProducts.CoffeeMaker.Setting.CoffeeMilkOrder",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eq700_macchiato_pause",
            entity="ConsumerProducts.CoffeeMaker.Setting.MacchiatoPause",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eq700_coffee_milk_order_mac",
            entity="ConsumerProducts.CoffeeMaker.Setting.CoffeeMilkOrderMac",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eq700_brewing_temperature",
            entity="ConsumerProducts.CoffeeMaker.Setting.BrewingTemperature",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSelectEntityDescription(
            key="select_eq700_start_up_category",
            entity="ConsumerProducts.CoffeeMaker.Setting.StartUpCategory",
            entity_category=EntityCategory.CONFIG,
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
    ]
)

CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("number", []).extend(
    [
        HCNumberEntityDescription(
            key="number_eq700_brightness_display",
            entity="ConsumerProducts.CoffeeMaker.Setting.BrightnessDisplay",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.SLIDER,
        ),
        HCNumberEntityDescription(
            key="number_eq700_touch_screen_sound_volume",
            entity="ConsumerProducts.CoffeeMaker.Setting.TouchScreenSoundVolume",
            entity_category=EntityCategory.CONFIG,
            mode=NumberMode.SLIDER,
        ),
    ]
)

CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("sensor", []).extend(
    [
        HCSensorEntityDescription(
            key="sensor_shot_count",
            entity="ConsumerProducts.CoffeeMaker.Option.Shot.Count",
            available_access=(Access.READ, Access.READ_WRITE, Access.READ_STATIC),
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_eq700_water_hardness",
            entity="ConsumerProducts.CoffeeMaker.Setting.WaterHardness",
            available_access=(Access.READ, Access.READ_WRITE, Access.READ_STATIC),
            device_class=SensorDeviceClass.ENUM,
            has_state_translation=True,
        ),
        HCSensorEntityDescription(
            key="sensor_eq700_beverage_counter_milk",
            entity="ConsumerProducts.CoffeeMaker.Status.BeverageCounterMilk",
            available_access=(Access.READ, Access.READ_WRITE, Access.READ_STATIC),
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
    ]
)

_EVENT = "ConsumerProducts.CoffeeMaker.Event."
# Events that matter in everyday use come first, rare device faults second, the rest after.
# Both groups switch the Problem sensor on.
_COFFEE_EVERYDAY = (
    "BrewingUnitIsMissing",
    "CleanBrewingUnit",
    "WaterTankEmpty",
    "WaterCriticallyEmpty",
    "EmptyDripTrayRemoveContainer",
    "AdjustGrindSetting",
    "DeviceDescalingOverdue",
    "DeviceDescalingBlockage",
    "DeviceCalcNCleanBlockage",
    "InsertWaterFilter",
)
_COFFEE_RARE = (
    "HeaterError",
    "TemperatureError",
    "WaterDistribError",
    "GrinderError",
    "PowerSupplyError",
    "DeviceIsToCold4C",
    "SystemHasRunDry",
    "RestartAppliance",
    "SwitchOffPower30sekBackOn",
    "UnderOverVoltage",
)


def _coffee_severity(message: tuple[str, str]) -> int:
    """Rank a message: everyday problems, rare faults, everything else, each in list order."""
    name = message[0].removeprefix(_EVENT)
    for rank, names in enumerate((_COFFEE_EVERYDAY, _COFFEE_RARE)):
        if name in names:
            return rank * 100 + names.index(name)
    return 200


_COFFEE_MESSAGES = (
    ("ConsumerProducts.CoffeeMaker.Event.BeanContainerNearlyEmpty", "bean_container_nearly_empty"),
    ("ConsumerProducts.CoffeeMaker.Event.BeanContainerIsNotPresent", "bean_container_not_present"),
    (
        "ConsumerProducts.CoffeeMaker.Event.BeanContainerNotFullyInserted",
        "bean_container_not_fully_inserted",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.PomaceContainerMissing", "pomace_container_missing"),
    ("ConsumerProducts.CoffeeMaker.Event.DripTrayOverFull", "drip_tray_over_full"),
    ("ConsumerProducts.CoffeeMaker.Event.HeaterError", "heater_error"),
    ("ConsumerProducts.CoffeeMaker.Event.TemperatureError", "temperature_error"),
    ("ConsumerProducts.CoffeeMaker.Event.WaterDistribError", "water_distrib_error"),
    ("ConsumerProducts.CoffeeMaker.Event.WaterCriticallyEmpty", "water_critically_empty"),
    ("ConsumerProducts.CoffeeMaker.Event.PomaceCaveFull", "pomace_cave_full"),
    ("ConsumerProducts.CoffeeMaker.Event.PreparationResume", "preparation_resume"),
    ("ConsumerProducts.CoffeeMaker.Event.MaintenanceContinue", "maintenance_continue"),
    ("ConsumerProducts.CoffeeMaker.Event.MilkTubeRemoved", "milk_tube_removed"),
    ("ConsumerProducts.CoffeeMaker.Event.MilkContainerConnected", "milk_container_connected"),
    (
        "ConsumerProducts.CoffeeMaker.Event.RefillRemovedMilkContainer",
        "refill_removed_milk_container",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.InsertMilkTank", "insert_milk_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.RemoveMilkTank", "remove_milk_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.RemoveMilkTube", "remove_milk_tube"),
    (
        "ConsumerProducts.CoffeeMaker.Event.DripTrayTooFullForThisKindOfBeverage",
        "drip_tray_too_full_for_this_kind_of_beverage",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.KeepMilkTankCool", "keep_milk_tank_cool"),
    (
        "ConsumerProducts.CoffeeMaker.Event.NotEnoughWaterForThisKindOfBeverage",
        "not_enough_water_for_this_kind_of_beverage",
    ),
    (
        "ConsumerProducts.CoffeeMaker.Event.NotEnoughPomaceCapacityForThisKindOfBeverage",
        "not_enough_pomace_capacity_for_this_kind_of_beverage",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.GrinderError", "grinder_error"),
    ("BSH.Common.Event.SoftwareUpdateAvailable", "software_update_available"),
    ("BSH.Common.Event.SoftwareUpdateSuccessful", "software_update_successful"),
    ("BSH.Common.Event.ProgramFinished", "program_finished"),
    ("ConsumerProducts.CoffeeMaker.Event.DripTrayFull", "drip_tray_full"),
    ("ConsumerProducts.CoffeeMaker.Event.DripTrayNotInserted", "drip_tray_not_inserted"),
    ("ConsumerProducts.CoffeeMaker.Event.BrewingUnitIsMissing", "brewing_unit_is_missing"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnit", "clean_brewing_unit"),
    ("ConsumerProducts.CoffeeMaker.Event.BUCoverIsMissing", "bu_cover_is_missing"),
    ("ConsumerProducts.CoffeeMaker.Event.PowerSupplyError", "power_supply_error"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceIsToCold4C", "device_is_to_cold4_c"),
    ("ConsumerProducts.CoffeeMaker.Event.SystemHasRunDry", "system_has_run_dry"),
    ("ConsumerProducts.CoffeeMaker.Event.BeanContainerEmpty", "bean_container_empty"),
    ("ConsumerProducts.CoffeeMaker.Event.CoffeeOutletMissing", "coffee_outlet_missing"),
    ("ConsumerProducts.CoffeeMaker.Event.CloseDoor", "close_door"),
    ("ConsumerProducts.CoffeeMaker.Event.RefillEmptyBeanContainer", "refill_empty_bean_container"),
    ("ConsumerProducts.CoffeeMaker.Event.RefillEmptyWaterTank", "refill_empty_water_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.UnderOverVoltage", "under_over_voltage"),
    ("ConsumerProducts.CoffeeMaker.Event.MilkContainerRemoved", "milk_container_removed"),
    ("ConsumerProducts.CoffeeMaker.Event.RestartAppliance", "restart_appliance"),
    (
        "ConsumerProducts.CoffeeMaker.Event.SwitchOffPower30sekBackOn",
        "switch_off_power30sek_back_on",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.AdjustGrindSetting", "adjust_grind_setting"),
    ("ConsumerProducts.CoffeeMaker.Event.WaterTankNearlyEmpty", "water_tank_nearly_empty"),
    ("ConsumerProducts.CoffeeMaker.Event.WaterTankEmpty", "water_tank_empty"),
    ("ConsumerProducts.CoffeeMaker.Event.WaterTankNotInserted", "water_tank_not_inserted"),
    ("BSH.Common.Event.SoftwareDownloadAvailable", "software_download_available"),
    (
        "ConsumerProducts.CoffeeMaker.Event.ThrowCleaningDiscInTheDrawer",
        "throw_cleaning_disc_in_the_drawer",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.EmptyDripTray", "empty_drip_tray"),
    ("ConsumerProducts.CoffeeMaker.Event.FillDescaler", "fill_descaler"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanFillWaterTank", "clean_fill_water_tank"),
    (
        "ConsumerProducts.CoffeeMaker.Event.PlaceContainerUnderOutlet",
        "place_container_under_outlet",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.SpecialRinsing", "special_rinsing"),
    ("ConsumerProducts.CoffeeMaker.Event.EmptyWaterTank", "empty_water_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanMilkTank", "clean_milk_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.EmptyMilkTank", "empty_milk_tank"),
    ("ConsumerProducts.CoffeeMaker.Event.RemoveMilkContainer", "remove_milk_container"),
    (
        "ConsumerProducts.CoffeeMaker.Event.EmptyDripTrayRemoveContainer",
        "empty_drip_tray_remove_container",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.DescalingIn20Cups", "descaling_in20_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.DescalingIn15Cups", "descaling_in15_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.DescalingIn10Cups", "descaling_in10_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.DescalingIn5Cups", "descaling_in5_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.CalcNCleanIn20Cups", "calcn_clean_in20_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.CalcNCleanIn15Cups", "calcn_clean_in15_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.CalcNCleanIn10Cups", "calcn_clean_in10_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.CalcNCleanIn5Cups", "calcn_clean_in5_cups"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceCalcNCleanOverdue", "device_calcn_clean_overdue"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceCalcNCleanBlockage", "device_calcn_clean_blockage"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitManually", "clean_brewing_unit_manually"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceCleaningOverdue", "device_cleaning_overdue"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceShouldBeDescaled", "device_should_be_descaled"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceShouldBeCleaned", "device_should_be_cleaned"),
    (
        "ConsumerProducts.CoffeeMaker.Event.DeviceShouldBeCalcNCleaned",
        "device_should_be_calcn_cleaned",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceDescalingOverdue", "device_descaling_overdue"),
    ("ConsumerProducts.CoffeeMaker.Event.DeviceDescalingBlockage", "device_descaling_blockage"),
    ("ConsumerProducts.CoffeeMaker.Event.PlaceMilkHoseInDripPan", "place_milk_hose_in_drip_pan"),
    ("ConsumerProducts.CoffeeMaker.Event.DescalingSuccessfully", "descaling_successfully"),
    ("ConsumerProducts.CoffeeMaker.Event.FillWatertank", "fill_watertank"),
    (
        "ConsumerProducts.CoffeeMaker.Event.Place05lContainerUnderOutlet",
        "place05l_container_under_outlet",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.CleaningSuccessfully", "cleaning_successfully"),
    (
        "ConsumerProducts.CoffeeMaker.Event.Remove05lContainerUnderOutlet",
        "remove05l_container_under_outlet",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.CalcNCleanSuccessfully", "calcn_clean_successfully"),
    (
        "ConsumerProducts.CoffeeMaker.Event.MilkSystemCleaningSuccessfully",
        "milk_system_cleaning_successfully",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.ApplianceSwitchesOff", "appliance_switches_off"),
    (
        "ConsumerProducts.CoffeeMaker.Event.InsertMilkContainerDuringMaintenance",
        "insert_milk_container_during_maintenance",
    ),
    (
        "ConsumerProducts.CoffeeMaker.Event.RemoveContainerEmptyDripTray",
        "remove_container_empty_drip_tray",
    ),
    (
        "ConsumerProducts.CoffeeMaker.Event.SpecialRinsingSuccessfully",
        "special_rinsing_successfully",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.TurnAromaRingToA", "turn_aroma_ring_to_a"),
    ("ConsumerProducts.CoffeeMaker.Event.TurnAromaRingToB", "turn_aroma_ring_to_b"),
    ("ConsumerProducts.CoffeeMaker.Event.TurnAromaRingToC", "turn_aroma_ring_to_c"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep1", "clean_brewing_unit_step1"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep2", "clean_brewing_unit_step2"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep3", "clean_brewing_unit_step3"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep4", "clean_brewing_unit_step4"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep5", "clean_brewing_unit_step5"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep6", "clean_brewing_unit_step6"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep7", "clean_brewing_unit_step7"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep8", "clean_brewing_unit_step8"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep9", "clean_brewing_unit_step9"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep10", "clean_brewing_unit_step10"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep11", "clean_brewing_unit_step11"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep12", "clean_brewing_unit_step12"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanBrewingUnitStep13", "clean_brewing_unit_step13"),
    (
        "ConsumerProducts.CoffeeMaker.Event.BrewingUnitCleaningSuccessfully",
        "brewing_unit_cleaning_successfully",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep1", "clean_outlet_step1"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep2", "clean_outlet_step2"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep3", "clean_outlet_step3"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep4", "clean_outlet_step4"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep5", "clean_outlet_step5"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep6", "clean_outlet_step6"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletStep7", "clean_outlet_step7"),
    ("ConsumerProducts.CoffeeMaker.Event.CleanOutletSuccessfully", "clean_outlet_successfully"),
    ("ConsumerProducts.CoffeeMaker.Event.RemoveWaterFilter", "remove_water_filter"),
    ("ConsumerProducts.CoffeeMaker.Event.InsertWaterFilter", "insert_water_filter"),
    (
        "ConsumerProducts.CoffeeMaker.Event.WaterFilterShouldBeChanged",
        "water_filter_should_be_changed",
    ),
    ("ConsumerProducts.CoffeeMaker.Event.PrepareWaterFilterChange", "prepare_water_filter_change"),
    (
        "ConsumerProducts.CoffeeMaker.Event.InsertWaterFilterSuccessfully",
        "insert_water_filter_successfully",
    ),
    (
        "ConsumerProducts.CoffeeMaker.Event.RemoveWaterFilterSuccessfully",
        "remove_water_filter_successfully",
    ),
    (
        "ConsumerProducts.CoffeeMaker.Event.ReplaceWaterFilterSuccessfully",
        "replace_water_filter_successfully",
    ),
)

COFFEE_MAXIMUM_MESSAGES = tuple(sorted(_COFFEE_MESSAGES, key=_coffee_severity))


def generate_coffee_maximum(appliance: HomeAppliance) -> EntityDescriptions:
    """Expose selected everyday coffee functions without changing existing entities."""
    result = EntityDescriptions(binary_sensor=[], event_sensor=[], sensor=[])
    if not any(name.startswith("ConsumerProducts.CoffeeMaker.") for name in appliance.entities):
        return result
    problems = tuple(
        _EVENT + name
        for name in (*_COFFEE_EVERYDAY, *_COFFEE_RARE)
        if _EVENT + name in appliance.entities
    )
    if problems:
        result["binary_sensor"].append(
            HCBinarySensorEntityDescription(
                key="binary_sensor_eq700_problem",
                entities=problems,
                device_class=BinarySensorDeviceClass.PROBLEM,
                value_on={"Present", "Confirmed"},
            )
        )
    messages = [(name, key) for name, key in COFFEE_MAXIMUM_MESSAGES if name in appliance.entities]
    if messages:
        result["event_sensor"].append(
            HCSensorEntityDescription(
                key="sensor_eq700_messages",
                entities=tuple(name for name, _ in messages),
                device_class=SensorDeviceClass.ENUM,
                options=[key for _, key in messages] + ["none"],
                extra_attributes=[
                    {"name": name.split(".Event.")[-1], "entity": name} for name, _ in messages
                ],
            )
        )
    # Resolve the profile's program UID; do not present an unexplained number.
    mapping = {name: name.lower().replace(".", "_") for name in appliance.programs}

    def program_value(entity: HcEntity) -> str | None:
        program = appliance.entities_uid.get(entity.value)
        return mapping.get(program.name) if program is not None else None

    for tail, key in (
        ("LastSelectedBeverage", "sensor_eq700_last_selected_beverage"),
        ("LastSelectedCoffeeWorldBeverage", "sensor_eq700_last_selected_coffee_world_beverage"),
    ):
        name = f"ConsumerProducts.CoffeeMaker.Status.{tail}"
        if name in appliance.entities:
            result["sensor"].append(
                HCSensorEntityDescription(
                    key=key,
                    entity=name,
                    device_class=SensorDeviceClass.ENUM,
                    options=list(mapping.values()),
                    value_fn=program_value,
                    extra_attributes=[{"name": "program_uid", "entity": name}],
                )
            )
    return result


CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("dynamic", []).append(generate_coffee_maximum)


def generate_coffee_quantity_select(appliance: HomeAppliance) -> EntityDescriptions:
    """Create a quantity Select only when a beverage uses FillQuantity."""
    descriptions = EntityDescriptions(coffee_quantity=[])
    if (
        appliance.info.get("type") == "CoffeeMaker"
        and FILL_QUANTITY in appliance.entities
        and any(
            option.uid == appliance.entities[FILL_QUANTITY].uid
            for program in appliance.programs.values()
            for option in program.options
        )
    ):
        descriptions["coffee_quantity"].append(
            HCSelectEntityDescription(key="select_coffee_fill_quantity", entity=FILL_QUANTITY)
        )
    return descriptions


CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("dynamic", []).append(
    generate_coffee_quantity_select
)


# (key, events with their state, in priority order, state without an active event, minimum events)
_COFFEE_CONTAINERS = (
    (
        "sensor_water_tank",
        (
            ("WaterTankEmpty", "empty"),
            ("WaterCriticallyEmpty", "critically_empty"),
            ("WaterTankNearlyEmpty", "nearly_empty"),
            ("WaterTankNotInserted", "not_inserted"),
        ),
        "full",
        1,
    ),
    (
        "sensor_bean_container",
        (
            ("BeanContainerIsNotPresent", "not_present"),
            ("BeanContainerNotFullyInserted", "not_fully_inserted"),
            ("BeanContainerEmpty", "empty"),
            ("BeanContainerNearlyEmpty", "nearly_empty"),
        ),
        "ok",
        2,
    ),
    (
        "sensor_pomace_container",
        (("PomaceContainerMissing", "missing"), ("PomaceCaveFull", "full")),
        "ok",
        1,
    ),
)


def generate_coffee_containers(appliance: HomeAppliance) -> EntityDescriptions:
    """
    Container state sensors from the events a coffee maker reports.

    The bean container needs at least two events, otherwise it would only repeat the
    binary sensor for "empty".
    """
    descriptions = EntityDescriptions(event_sensor=[])
    for key, events, ok_state, minimum in _COFFEE_CONTAINERS:
        present = [
            (_EVENT + name, state) for name, state in events if _EVENT + name in appliance.entities
        ]
        if len(present) >= minimum:
            descriptions["event_sensor"].append(
                HCSensorEntityDescription(
                    key=key,
                    entities=tuple(name for name, _ in present),
                    device_class=SensorDeviceClass.ENUM,
                    options=[state for _, state in present] + [ok_state],
                )
            )
    return descriptions


CONSUMER_PRODUCTS_ENTITY_DESCRIPTIONS.setdefault("dynamic", []).append(generate_coffee_containers)
