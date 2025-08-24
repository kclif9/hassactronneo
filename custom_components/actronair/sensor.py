"""Sensor platform for Actron Air integration."""

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ActronAirConfigEntry
from .entity import (
    EntitySensor,
    PeripheralBatterySensor,
    PeripheralHumiditySensor,
    PeripheralTemperatureSensor,
    ZoneHumiditySensor,
    ZoneTemperatureSensor,
    DIAGNOSTIC_CATEGORY,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronAirConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air entities."""

    # Sensor configurations with appropriate entity categories, device classes, and enabled_default
    # Format: translation_key, sensor_name, device_class, unit, entity_category, state_class, enabled_default
    sensor_configs = [
        (
            "clean_filter",
            "clean_filter",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            True,
        ),
        (
            "defrost_mode",
            "defrost_mode",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_chasing_temperature",
            "compressor_chasing_temperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_live_temperature",
            "compressor_live_temperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_mode",
            "compressor_mode",
            SensorDeviceClass.ENUM,
            None,
            DIAGNOSTIC_CATEGORY,
            None,
            False,
        ),
        (
            "system_on",
            "system_on",
            SensorDeviceClass.ENUM,
            None,
            None,
            None,
            True,
        ),
        (
            "compressor_speed",
            "compressor_speed",
            SensorDeviceClass.SPEED,
            None,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "compressor_power",
            "compressor_power",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            DIAGNOSTIC_CATEGORY,
            SensorStateClass.MEASUREMENT,
            False,
        ),
        (
            "outdoor_temperature",
            "outdoor_temperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            None,
            SensorStateClass.MEASUREMENT,
            True,
        ),
        (
            "humidity",
            "humidity",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            None,
            SensorStateClass.MEASUREMENT,
            True,
        ),
    ]

    system_coordinators = entry.runtime_data.system_coordinators
    entities: list[EntitySensor] = []

    for coordinator in system_coordinators.values():
        status = coordinator.data

        for (
            translation_key,
            sensor_name,
            device_class,
            unit,
            entity_category,
            state_class,
            enabled_default,
        ) in sensor_configs:
            sensor = EntitySensor(
                coordinator = coordinator,
                translation_key = translation_key,
                sensor_name = sensor_name,
                device_class = device_class,
                unit_of_measurement = unit,
                is_diagnostic = False,
                entity_category = entity_category,
                state_class = state_class,
                enabled_default = enabled_default,
            )
            entities.append(sensor)

        for zone in status.remote_zone_info:
            if zone.exists:
                entities.append(ZoneTemperatureSensor(coordinator, zone))
                entities.append(ZoneHumiditySensor(coordinator, zone))

        for peripheral in status.peripherals:
            entities.append(PeripheralBatterySensor(coordinator, peripheral))
            entities.append(PeripheralTemperatureSensor(coordinator, peripheral))
            entities.append(PeripheralHumiditySensor(coordinator, peripheral))

        # Add all sensors
        async_add_entities(entities)
