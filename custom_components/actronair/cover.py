"""Cover platform for Actron Air integration."""

from actron_neo_api import ActronAirNeoZone

from homeassistant.components.cover import CoverDeviceClass, CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ActronAirConfigEntry, ActronAirSystemCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Actron Air cover entities."""
    system_coordinators = entry.runtime_data.system_coordinators
    entities: list[CoverEntity] = []

    for coordinator in system_coordinators.values():
        status = coordinator.data
        entities.extend(
            ZonePositionSensor(coordinator, zone)
            for zone in status.remote_zone_info
            if zone.exists
        )

    async_add_entities(entities)


class ZonePositionSensor(CoordinatorEntity, CoverEntity):
    """Position sensor for Actron Air zone."""

    _attr_has_entity_name: bool = True
    _attr_supported_features: CoverEntityFeature = None
    _attr_translation_key: str = "zone_position"
    _attr_device_class: CoverDeviceClass = CoverDeviceClass.DAMPER

    def __init__(
        self,
        coordinator: ActronAirSystemCoordinator,
        zone: ActronAirNeoZone,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._serial_number: str = coordinator.serial_number
        self._zone: ActronAirNeoZone = zone
        self._attr_unique_id: str = f"{self._serial_number}_zone_{self._zone.zone_id}_position"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, f"{self._serial_number}_zone_{self._zone.zone_id}")},
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return not self.coordinator.is_device_stale()

    @property
    def current_cover_position(self) -> str | None:
        """Return the state of the sensor."""
        return self._zone.zone_position

    @property
    def is_closed(self) -> bool:
        """Return True if the cover is closed."""
        return self.current_cover_position == 0
