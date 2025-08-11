"""Switch platform for Actron Air integration."""

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ActronNeoConfigEntry
from .entity import CONFIG_CATEGORY


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronNeoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air switches."""
    # Extract API and coordinator from hass.data
    system_coordinators = entry.runtime_data.system_coordinators

    # Fetch the status and create ZoneSwitches
    entities: list[SwitchEntity] = []

    for coordinator in system_coordinators.values():
        entities.append(AwayModeSwitch(coordinator))
        entities.append(ContinuousFanSwitch(coordinator))
        entities.append(QuietModeSwitch(coordinator))

        if coordinator.data.user_aircon_settings.turbo_supported:
            entities.append(TurboModeSwitch(coordinator))

    # Add all switches
    async_add_entities(entities)

class AwayModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air away mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "away_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number = coordinator.serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:home-export-outline"
        self.off_icon = "mdi:home-import-outline"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.user_aircon_settings.away_mode

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        await self.coordinator.data.user_aircon_settings.set_away_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        await self.coordinator.data.user_aircon_settings.set_away_mode(False)


class ContinuousFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air continuous fan switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "continuous_fan"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number = coordinator.serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:fan"
        self.off_icon = "mdi:fan-off"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.user_aircon_settings.continuous_fan_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        await self.coordinator.data.user_aircon_settings.set_continuous_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        await self.coordinator.data.user_aircon_settings.set_continuous_mode(False)


class QuietModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air quiet mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "quiet_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number = coordinator.serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:volume-low"
        self.off_icon = "mdi:volume-high"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.user_aircon_settings.quiet_mode_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the quiet mode setting on."""
        await self.coordinator.data.user_aircon_settings.set_quiet_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the quiet mode setting off."""
        await self.coordinator.data.user_aircon_settings.set_quiet_mode(False)


class TurboModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air turbo mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "turbo_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number = coordinator.serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:fan-plus"
        self.off_icon = "mdi:fan"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data.user_aircon_settings.turbo_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the turbo mode on."""
        await self.coordinator.data.user_aircon_settings.set_turbo_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the turbo mode off."""
        await self.coordinator.data.user_aircon_settings.set_turbo_mode(False)
