"""Sensor platform for Actron Neo integration."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
)
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import ActronNeoDataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DIAGNOSTIC_CATEGORY = EntityCategory.DIAGNOSTIC
CONFIG_CATEGORY = EntityCategory.CONFIG


class EntitySensor(CoordinatorEntity, Entity):
    """Representation of a diagnostic sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        translation_key,
        path,
        key,
        device_class=None,
        unit_of_measurement=None,
        is_diagnostic=False,
        entity_category=None,
        enabled_default=True,
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._path = path if isinstance(path, list) else [
            path]
        self._key = key
        self._serial_number = serial_number
        self._status = coordinator.data.get(self._serial_number, {}) if coordinator.data else {}
        self._is_diagnostic = is_diagnostic
        self._entity_category = entity_category
        self._enabled_default = enabled_default
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = translation_key
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._serial_number in self.coordinator.data
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self.available:
            return None

        data = self.coordinator.data.get(self._serial_number, {})
        if data:
            # Traverse the path dynamically
            for key in self._path:
                data = data.get(key, {})
            return data.get(self._key, None)
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category."""
        if self._entity_category:
            return self._entity_category
        return DIAGNOSTIC_CATEGORY if self._is_diagnostic else None

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default


class BaseZoneSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        serial_number: str,
        zone,
        zone_number,
        translation_key,
        state_key,
        device_class,
        unit_of_measurement,
        entity_category=None,
        enabled_default=True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._status = coordinator.data.get(self._serial_number, {}) if coordinator.data else {}
        self._zone = zone
        self._zone_number = zone_number
        self._state_key = state_key
        self._entity_category = entity_category
        self._enabled_default = enabled_default
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{self._serial_number}_zone_{self._zone_number}_{translation_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self._serial_number}_zone_{self._zone_number}")},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._serial_number in self.coordinator.data
        )

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if not self.available:
            return None

        zones = self.coordinator.data.get(self._serial_number, {}).get("RemoteZoneInfo", [])
        for zone_number, zone in enumerate(zones, start=0):
            if zone_number == self._zone_number:
                return zone.get(self._state_key, None)
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category."""
        return self._entity_category

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default


class ZonePositionSensor(BaseZoneSensor):
    """Position sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, zone_number) -> None:
        """Initialize the position sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            zone_number,
            "position",
            "ZonePosition",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            entity_category=DIAGNOSTIC_CATEGORY,
            enabled_default=False,
        )


class ZoneTemperatureSensor(BaseZoneSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, zone_number) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            zone_number,
            "temperature",
            "LiveTemp_oC",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS
        )


class ZoneHumiditySensor(BaseZoneSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, zone_number) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            zone_number,
            "humidity",
            "LiveHumidity_pc",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE
        )


class BasePeripheralSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        serial_number: str,
        zone,
        peripheral,
        translation_key,
        path,
        key,
        device_class,
        unit_of_measurement,
        entity_category=None,
        enabled_default=True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._status = coordinator.data.get(self._serial_number, {}) if coordinator.data else {}
        self._zone = zone
        self._peripheral = peripheral
        self._logical_address = peripheral["LogicalAddress"]
        self._path = path if isinstance(path, list) else [path]
        self._key = key
        self._serial_number = self._peripheral["SerialNumber"]
        self._entity_category = entity_category
        self._enabled_default = enabled_default
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{self._serial_number}_{translation_key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._serial_number in self.coordinator.data
        )

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        if not self.available:
            return None

        # Look up the state using the state key in the data.
        data_source = self.coordinator.data.get(self._serial_number, {}).get("AirconSystem", {}).get(
            "Peripherals", []
        )
        for peripheral in data_source:
            if peripheral["LogicalAddress"] == self._logical_address:
                for key in self._path:
                    peripheral = peripheral.get(key, {})
                return peripheral.get(self._key, None)
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category."""
        return self._entity_category

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default


class PeripheralBatterySensor(BasePeripheralSensor):
    """Battery sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, logical_address) -> None:
        """Initialize the battery sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            logical_address,
            "battery",
            [],
            "RemainingBatteryCapacity_pc",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            entity_category=DIAGNOSTIC_CATEGORY,
            enabled_default=True,
        )


class PeripheralTemperatureSensor(BasePeripheralSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, logical_address) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            logical_address,
            "temperature",
            ["SensorInputs", "SHTC1"],
            "Temperature_oC",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS
        )


class PeripheralHumiditySensor(BasePeripheralSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, serial_number, zone, logical_address) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            logical_address,
            "humidity",
            ["SensorInputs", "SHTC1"],
            "RelativeHumidity_pc",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE
        )
