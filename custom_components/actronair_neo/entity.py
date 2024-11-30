"""Sensor platform for Actron Neo integration."""

from collections.abc import Mapping
from typing import Any

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class DiagnosticSensor(CoordinatorEntity, Entity):
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
        return f"Actron Air Neo {self._name}"

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
