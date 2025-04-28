"""Sensor platform for Actron Neo integration."""

from actron_neo_api import ActronAirNeoPeripheral, ActronAirNeoZone

from homeassistant.components.sensor import (
    SensorDeviceClass,
)
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .coordinator import ActronNeoDataUpdateCoordinator
from .const import DOMAIN

DIAGNOSTIC_CATEGORY = EntityCategory.DIAGNOSTIC
CONFIG_CATEGORY = EntityCategory.CONFIG


class EntitySensor(CoordinatorEntity, Entity):
    """Representation of a diagnostic sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        status,
        translation_key: str,
        sensor_name: str,
        device_class=None,
        unit_of_measurement=None,
        is_diagnostic=False,
        entity_category=None,
        state_class=None,
        enabled_default=True,
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._sensor_name = sensor_name
        self._is_diagnostic = is_diagnostic
        self._entity_category = entity_category
        self._enabled_default = enabled_default
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_state_class = state_class
        self._attr_unique_id = translation_key
        self._serial_number = serial_number
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )

    @property
    def _status(self):
        """Get the current status from the coordinator."""
        return self.coordinator.get_status(self._serial_number)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.state is not None

    @property
    def state(self):
        """Return the state of the sensor."""
        return getattr(self._status, self._sensor_name, None)

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
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        zone: ActronAirNeoZone,
        translation_key: str,
        state_key: str,
        device_class: SensorDeviceClass,
        unit_of_measurement,
        entity_category=None,
        enabled_default: bool = True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number: str = serial_number
        self._zone_id: int = zone.zone_id
        self._state_key: str = state_key
        self._entity_category = entity_category
        self._enabled_default: bool = enabled_default
        self._attr_device_class: SensorDeviceClass = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id: str = f"{self._serial_number}_zone_{zone.zone_id}_{translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, f"{self._serial_number}_zone_{zone.zone_id}")},
        )

    @property
    def _zone(self) -> ActronAirNeoZone:
        """Get the current zone data from the coordinator."""
        status = self.coordinator.get_status(self._serial_number)
        for zone in status.remote_zone_info:
            if zone.zone_id == self._zone_id:
                return zone
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.state is not None

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        return getattr(self._zone, self._state_key, None)

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category."""
        return self._entity_category

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return self._enabled_default


class ZoneTemperatureSensor(BaseZoneSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator: ActronNeoDataUpdateCoordinator, serial_number: str, zone) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            "temperature",
            "live_temp_c",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS
        )


class ZoneHumiditySensor(BaseZoneSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator: ActronNeoDataUpdateCoordinator, serial_number: str, zone) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            serial_number,
            zone,
            "humidity",
            "live_humidity_pc",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE
        )


class BasePeripheralSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        ac_serial_number: str,
        peripheral: ActronAirNeoPeripheral,
        translation_key: str,
        state_key: str,
        device_class: SensorDeviceClass,
        unit_of_measurement,
        entity_category=None,
        enabled_default=True,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ac_serial = ac_serial_number
        self._peripheral_id = peripheral.logical_address
        self._state_key = state_key
        self._serial_number = peripheral.serial_number
        self._entity_category = entity_category
        self._enabled_default = enabled_default
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id: str = (
            f"{self._serial_number}_{translation_key}"
        )

        suggested_area = None
        if hasattr(peripheral, 'zones') and len(peripheral.zones) == 1:
            zone = peripheral.zones[0]
            if hasattr(zone, 'title') and zone.title:
                suggested_area = zone.title

        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            name=f"{peripheral.device_type} {peripheral.logical_address}",
            manufacturer="Actron Air",
            model=peripheral.device_type,
            suggested_area=suggested_area,
        )

    @property
    def _peripheral(self) -> ActronAirNeoPeripheral:
        """Get the current peripheral data from the coordinator."""
        status = self.coordinator.get_status(self._ac_serial)
        for peripheral in status.peripherals:
            if peripheral.logical_address == self._peripheral_id:
                return peripheral
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.state is not None

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        return getattr(self._peripheral, self._state_key, None)

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

    def __init__(self, coordinator: ActronNeoDataUpdateCoordinator, ac_serial: str, peripheral: ActronAirNeoPeripheral) -> None:
        """Initialize the battery sensor."""
        super().__init__(
            coordinator,
            ac_serial,
            peripheral,
            "battery",
            "battery_level",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            entity_category=DIAGNOSTIC_CATEGORY,
            enabled_default=True,
        )


class PeripheralTemperatureSensor(BasePeripheralSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator: ActronNeoDataUpdateCoordinator, ac_serial: str, peripheral: ActronAirNeoPeripheral) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            ac_serial,
            peripheral,
            "temperature",
            "temperature",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS
        )


class PeripheralHumiditySensor(BasePeripheralSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator: ActronNeoDataUpdateCoordinator, ac_serial: str, peripheral: ActronAirNeoPeripheral) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            ac_serial,
            peripheral,
            "humidity",
            "humidity",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE
        )
