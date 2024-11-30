"""Sensor platform for Actron Neo integration."""


from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class BaseSensor(CoordinatorEntity, Entity):
    """Representation of a diagnostic sensor."""

    def __init__(
        self, coordinator, ac_unit, name, path, key, device_info, unit_of_measurement=None
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._ac_unit = ac_unit
        self._name = name
        self._path = path if isinstance(path, list) else [path]  # Ensure path is a list
        self._key = key
        self._device_info = device_info
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self) -> str:
        """Set the name of the diagnostic sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        ac_unit_entity_id = self._ac_unit.unique_id
        return f"{ac_unit_entity_id}_{self._name.replace(' ', '_').lower()}"

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


class EntitySensor(BaseSensor):
    """Entity sensor inheriting BaseSensor."""

    def __init__(self, coordinator, ac_unit, name, path, key, device_info, unit_of_measurement) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            ac_unit,
            name,
            path,
            key,
            device_info,
            unit_of_measurement
        )


class DiagnosticSensor(BaseSensor):
    """Diagnostic sensor inheriting BaseSensor."""

    def __init__(self, coordinator, ac_unit, name, path, key, device_info, unit_of_measurement) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            ac_unit,
            name,
            path,
            key,
            device_info,
            unit_of_measurement
        )

    @property
    def entity_category(self) -> EntityCategory:
        """Return the entity category as diagnostic."""
        return EntityCategory.DIAGNOSTIC
