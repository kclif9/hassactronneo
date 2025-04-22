"""Sensor platform for Actron Air Neo integration."""

import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ActronConfigEntry
from .const import _LOGGER
from .entity import (
    EntitySensor,
    PeripheralBatterySensor,
    PeripheralHumiditySensor,
    PeripheralTemperatureSensor,
    ZoneHumiditySensor,
    ZonePositionSensor,
    ZoneTemperatureSensor,
    DIAGNOSTIC_CATEGORY,
    CONFIG_CATEGORY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air Neo sensors."""
    coordinator = entry.runtime_data

    # Sensor configurations with appropriate entity categories, device classes, and enabled_default
    # Format: translation_key, path, key, device_class, unit, entity_category, state_class, enabled_default
    sensor_configs = [
        (
            "clean_filter",
            ["Alerts"],
            "CleanFilter",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            True,
        ),
        (
            "defrost_mode",
            ["Alerts"],
            "Defrosting",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_chasing_temperature",
            ["LiveAircon"],
            "CompressorChasingTemperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_live_temperature",
            ["LiveAircon"],
            "CompressorLiveTemperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_mode",
            ["LiveAircon"],
            "CompressorMode",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            None,
            False,
        ),
        (
            "system_on",
            ["UserAirconSettings"],
            "isOn",
            SensorDeviceClass.ENUM,
            None,
            None,
            None,
            True,
        ),
        (
            "compressor_speed",
            ["LiveAircon", "OutdoorUnit"],
            "CompSpeed",
            SensorDeviceClass.SPEED,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_power",
            ["LiveAircon", "OutdoorUnit"],
            "CompPower",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "outdoor_temperature",
            ["MasterInfo"],
            "LiveOutdoorTemp_oC",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            None,
            SensorStateClass.MEASUREMENT,
            True,
        ),
        (
            "humidity",
            ["MasterInfo"],
            "LiveHumidity_pc",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            None,
            SensorStateClass.MEASUREMENT,
            True,
        ),
    ]

    entities: list[EntitySensor] = []

    for system in coordinator.api.systems:
        serial_number = system["serial"]

        # Create sensors with appropriate categories and device classes
        for (
            translation_key,
            path,
            key,
            device_class,
            unit,
            entity_category,
            state_class,
            enabled_default,
        ) in sensor_configs:
            sensor = EntitySensor(
                coordinator,
                serial_number,
                translation_key,
                path,
                key,
                device_class,
                unit,
                is_diagnostic=False,
                entity_category=entity_category,
                enabled_default=enabled_default,
            )
            # Set state class if provided
            if state_class:
                sensor._attr_state_class = state_class
            entities.append(sensor)

        # Fetch Zones
        zones = coordinator.data[serial_number].get("RemoteZoneInfo", [])

        # Create zones & sensors
        zone_map = {zone_number: zone for zone_number, zone in enumerate(zones, start=0)}
        for zone_number, zone in zone_map.items():
            if zone["NV_Exists"]:
                zone_name = zone["NV_Title"]
                entities.append(ZonePositionSensor(coordinator, serial_number, zone, zone_number))
                entities.append(ZoneTemperatureSensor(coordinator, serial_number, zone, zone_number))
                entities.append(ZoneHumiditySensor(coordinator, serial_number, zone, zone_number))

        # Fetch Peripherals
        peripherals = coordinator.data[serial_number].get("AirconSystem", {}).get("Peripherals", [])

        for peripheral in peripherals:
            logical_address = peripheral["LogicalAddress"]
            zone_number = peripheral.get("ZoneAssignment")[0] - 1
            zone = zone_map.get(zone_number)

            entities.append(PeripheralBatterySensor(coordinator, serial_number, zone, peripheral))
            entities.append(PeripheralTemperatureSensor(coordinator, serial_number, zone, peripheral))
            entities.append(PeripheralHumiditySensor(coordinator, serial_number, zone, peripheral))

        # Add all sensors
        async_add_entities(entities)
