"""Sensor platform for Actron Neo integration."""

from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

DIAGNOSTIC_CATEGORY = EntityCategory.DIAGNOSTIC


class EntitySensor(CoordinatorEntity, Entity):
    """Representation of a diagnostic sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        ac_unit,
        translation_key,
        path,
        key,
        device_info,
        device_class=None,
        is_diagnostic=False,
    ) -> None:
        """Initialise diagnostic sensor."""
        super().__init__(coordinator)
        self._ac_unit = ac_unit
        self._path = path if isinstance(path, list) else [path]  # Ensure path is a list
        self._key = key
        self._device_info = device_info
        self._is_diagnostic = is_diagnostic
        self._attr_device_class = device_class
        self._attr_translation_key = translation_key
        self._attr_unique_id = "_".join(
            [
                DOMAIN,
                self._ac_unit._serial_number,
                "sensor",
                translation_key,
            ]
        )
        self._attr_device_info = self._ac_unit.device_info

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
    def device_info(self):
        """Return device information."""
        return self._device_info

    @property
    def entity_category(self) -> EntityCategory | None:
        """Return the entity category if the sensor is diagnostic."""
        return DIAGNOSTIC_CATEGORY if self._is_diagnostic else None
