"""Cover platform for Actron Air Neo integration."""

from typing import Any

from actron_neo_api import ActronNeoAPI, ActronAirNeoZone, ActronAirNeoStatus

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ActronConfigEntry
from .const import DOMAIN
from .coordinator import ActronNeoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron Air Neo cover entities."""
    coordinator = entry.runtime_data
    entities: list[CoverEntity] = []

    for system in coordinator.systems:
        serial_number = system["serial"]
        status = coordinator.api.state_manager.get_status(serial_number)

        for zone in status.remote_zone_info:
            if zone.exists:
                entities.append(ZonePositionSensor(coordinator, serial_number, zone))

    async_add_entities(entities)


class ZonePositionSensor(CoordinatorEntity, CoverEntity):
    """Position sensor for Actron Air Neo zone."""

    _attr_has_entity_name: bool = True
    _attr_supported_features: CoverEntityFeature = None
    _attr_translation_key: str = "zone_position"
    _attr_device_class: CoverDeviceClass = CoverDeviceClass.DAMPER

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        zone: ActronAirNeoZone,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone: ActronAirNeoZone = zone
        self._attr_unique_id: str = f"{serial_number}_zone_{self._zone.zone_id}_position"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, f"{serial_number}_zone_{self._zone.zone_id}")},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        if not self.coordinator.last_update_success:
            return False
        return self.state is not None

    @property
    def current_cover_position(self) -> str | None:
        """Return the state of the sensor."""
        return self._zone.zone_position

    @property
    def is_closed(self) -> bool:
        """Return True if the cover is closed."""
        return self.current_cover_position == 0
