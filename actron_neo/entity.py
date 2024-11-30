"""Sensor platform for Actron Neo integration."""

from collections.abc import Mapping
from typing import Any

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class ActronNeoDiagnosticSensor(CoordinatorEntity, Entity):
    """Representation of a diagnostic sensor."""

    def __init__(
        self, coordinator, name, path, key, device_info, unit_of_measurement=None
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._name = name
        self._path = path if isinstance(path, list) else [path]  # Ensure path is a list
        self._key = key
        self._device_info = device_info
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self) -> str:
        """Set the name of the diagnostic sensor."""
        return f"Actron Neo {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"actron_neo_{self._name.replace(' ', '_').lower()}"

    @property
    def state(self):
        """Return the state of the sensor."""
        data = self.coordinator.data
        if data:
            # Traverse the path dynamically
            for key in self._path:
                data = data.get(key, {})
            return data.get(self._key, None)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def device_info(self):
        """Return device information."""
        return self._device_info


class ActronZoneSensor(Entity):
    """Representation of a zone sensor."""

    def __init__(self, coordinator, api, serial_number, zone) -> None:
        """Initalise a zone sensor."""
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._zone = zone
        self._name = f"Zone {zone['zone_id']} - {zone['name']}"
        self._temperature = zone["temperature"]
        self._humidity = zone["humidity"]

    @property
    def name(self) -> str:
        """Set the zone sensor name."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"actron_neo_{self._name.replace(' ', '_').lower()}"

    @property
    def state(self) -> str:
        """Set the zone sensor state."""
        return self._temperature

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Set the zone sensor's extra attributes."""
        return {
            "humidity": self._humidity,
            "enabled": self._zone["enabled"],
            "common_zone": self._zone["common_zone"],
        }

    async def async_update(self) -> None:
        """Fetch new state data for the sensor."""
        zones = await self._api.get_zones(self._serial_number)
        for zone in zones:
            if zone["zone_id"] == self._zone["zone_id"]:
                self._temperature = zone["temperature"]
                self._humidity = zone["humidity"]
                self._zone = zone
                break
