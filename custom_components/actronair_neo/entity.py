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
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._path = path if isinstance(path, list) else [
            path]  # Ensure path is a list
        self._key = key
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._is_diagnostic = is_diagnostic
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = translation_key

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self._status
        if data:
            # Traverse the path dynamically
            for key in self._path:
                data = data.get(key, {})
            return data.get(self._key, None)
        return None

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category if the sensor is diagnostic."""
        return DIAGNOSTIC_CATEGORY if self._is_diagnostic else None


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
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._zone = zone
        self._zone_number = zone_number
        self._state_key = state_key
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"zone_{self._zone_number}_{translation_key}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"zone_{self._zone_number}")},
            "name": self._zone["NV_Title"],
            "manufacturer": "Actron Air",
            "model": "Zone",
            "suggested_area": self._zone["NV_Title"],
        }

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        zones = self._status.get("RemoteZoneInfo", [])
        for zone_number, zone in enumerate(zones, start=0):
            if zone_number == self._zone_number:
                return zone.get(self._state_key, None)
        return None


class ZonePostionSensor(BaseZoneSensor):
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
            UnitOfTemperature.CELSIUS,
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
            PERCENTAGE,
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
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._zone = zone
        self._peripheral = peripheral
        self._logical_address = peripheral["LogicalAddress"]
        self._path = path if isinstance(path, list) else [path]
        self._key = key
        self._serial_number = self._peripheral["SerialNumber"]
        self._attr_device_class = device_class
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_translation_key = translation_key
        self._attr_unique_id = (
            f"{self._serial_number}_{translation_key}"
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": f"{self._peripheral["DeviceType"]} {self._logical_address}",
            "manufacturer": "Actron Air",
            "model": self._peripheral["DeviceType"],
            "sw_version": self._peripheral["Firmware"]["InstalledVersion"]["NRF52"],
            "serial_number": self._serial_number,
            "suggested_area": self._zone["NV_Title"],
        }

    @property
    def state(self) -> str | None:
        """Return the state of the sensor."""
        # Look up the state using the state key in the data.
        data_source = self._status.get("AirconSystem", {}).get(
            "Peripherals", []
        )
        for peripheral in data_source:
            if peripheral["LogicalAddress"] == self._logical_address:
                for key in self._path:
                    peripheral = peripheral.get(key, {})
                return peripheral.get(self._key, None)
        return None


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
            UnitOfTemperature.CELSIUS,
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
            PERCENTAGE,
        )
