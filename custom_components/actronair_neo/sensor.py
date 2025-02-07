"""Sensor platform for Actron Air Neo integration."""

import logging

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

from .entity import (
    EntitySensor,
    PeripheralBatterySensor,
    PeripheralHumiditySensor,
    PeripheralTemperatureSensor,
    ZoneHumiditySensor,
    ZonePostionSensor,
    ZoneTemperatureSensor,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air Neo sensors."""
    coordinator = config_entry.runtime_data

    # Diagnostic sensor configurations
    diagnostic_configs = [
        (
            "clean_filter",
            ["Alerts"],
            "CleanFilter",
            None,
            None,
            False,
        ),
        (
            "defrost_mode",
            ["Alerts"],
            "Defrosting",
            None,
            None,
            False,
        ),
        (
            "compressor_chasing_temperature",
            ["LiveAircon"],
            "CompressorChasingTemperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            True,
        ),
        (
            "compressor_live_temperature",
            ["LiveAircon"],
            "CompressorLiveTemperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            True,
        ),
        (
            "compressor_mode",
            ["LiveAircon"],
            "CompressorMode",
            None,
            None,
            True,
        ),
        (
            "system_on",
            ["UserAirconSettings"],
            "isOn",
            None,
            None,
            False,
        ),
        (
            "compressor_speed",
            ["LiveAircon", "OutdoorUnit"],
            "CompSpeed",
            SensorDeviceClass.SPEED,
            None,
            True,
        ),
        (
            "compressor_power",
            ["LiveAircon", "OutdoorUnit"],
            "CompPower",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            True,
        ),
        (
            "outdoor_temperature",
            ["MasterInfo"],
            "LiveOutdoorTemp_oC",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            False,
        ),
        (
            "humidity",
            ["MasterInfo"],
            "LiveHumidity_pc",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            False,
        ),
    ]

    entities: list[EntitySensor] = []

    assert coordinator.systems is not None

    systems = coordinator.systems["_embedded"]["ac-system"]
    for system in systems:
        serial_number = system["serial"]

        # Create diagnostic sensors
        for (
            translation_key,
            path,
            key,
            device_class,
            unit,
            diagnostic_sensor,
        ) in diagnostic_configs:
            entities.append(
                EntitySensor(
                    coordinator,
                    serial_number,
                    translation_key,
                    path,
                    key,
                    device_class,
                    unit,
                    diagnostic_sensor,
                )
            )

        # Fetch Zones
        zones = coordinator.data[serial_number].get("RemoteZoneInfo", [])

        # Create zones & sensors
        zone_map = {zone_number: zone for zone_number, zone in enumerate(zones, start=0)}
        for zone_number, zone in zone_map.items():
            if zone["NV_Exists"]:
                zone_name = zone["NV_Title"]
                entities.append(ZonePostionSensor(coordinator, serial_number, zone, zone_number))
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
