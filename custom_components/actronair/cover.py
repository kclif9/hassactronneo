"""Cover platform for Actron Air integration."""

from actron_neo_api import ActronAirZone

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ActronAirConfigEntry, ActronAirSystemCoordinator
from .entity import ActronAirZoneEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron Air cover entities."""
    system_coordinators = entry.runtime_data.system_coordinators
    async_add_entities(
        ActronAirZoneDamper(coordinator, zone)
        for coordinator in system_coordinators.values()
        for zone in coordinator.data.remote_zone_info
        if zone.exists
    )


class ActronAirZoneDamper(ActronAirZoneEntity, CoverEntity):
    """Damper position cover for an Actron Air zone."""

    _attr_device_class = CoverDeviceClass.DAMPER
    _attr_supported_features = CoverEntityFeature(0)
    _attr_translation_key = "zone_position"

    def __init__(
        self,
        coordinator: ActronAirSystemCoordinator,
        zone: ActronAirZone,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator, zone)
        self._attr_unique_id = f"{self._zone_identifier}_{self._attr_translation_key}"

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of the damper."""
        return self._zone.zone_position

    @property
    def is_closed(self) -> bool:
        """Return True if the damper is closed."""
        return self.current_cover_position == 0
