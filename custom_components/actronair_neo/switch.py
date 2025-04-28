"""Switch platform for Actron Neo integration."""

import logging
from typing import Any

from actron_neo_api import ActronAirNeoStatus

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ActronConfigEntry
from .const import _LOGGER, DOMAIN
from .entity import CONFIG_CATEGORY


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Neo switches."""
    # Extract API and coordinator from hass.data
    coordinator = entry.runtime_data

    # Fetch the status and create ZoneSwitches
    entities: list[SwitchEntity] = []

    for system in coordinator.systems:
        serial_number = system["serial"]
        status = coordinator.api.state_manager.get_status(serial_number)

        entities.append(AwayModeSwitch(coordinator, serial_number))
        entities.append(ContinuousFanSwitch(coordinator, serial_number))
        entities.append(QuietModeSwitch(coordinator, serial_number))

        if status.user_aircon_settings.turbo_supported:
            entities.append(TurboModeSwitch(coordinator, serial_number))

    # Add all switches
    async_add_entities(entities)

class AwayModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo away mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "away_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number: str = serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:home-export-outline"
        self.off_icon = "mdi:home-import-outline"

    @property
    def _status(self) -> ActronAirNeoStatus:
        """Get the current status from the coordinator."""
        return self.coordinator.get_status(self._serial_number)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.user_aircon_settings.away_mode

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        await self._status.user_aircon_settings.set_away_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        await self._status.user_aircon_settings.set_away_mode(False)


class ContinuousFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo continuous fan switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "continuous_fan"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number: str = serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:fan"
        self.off_icon = "mdi:fan-off"

    @property
    def _status(self) -> ActronAirNeoStatus:
        """Get the current status from the coordinator."""
        return self.coordinator.get_status(self._serial_number)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.user_aircon_settings.continuous_fan_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        await self._status.user_aircon_settings.set_continuous_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        await self._status.user_aircon_settings.set_continuous_mode(False)


class QuietModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo quiet mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "quiet_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number: str = serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:volume-low"
        self.off_icon = "mdi:volume-high"

    @property
    def _status(self) -> ActronAirNeoStatus:
        """Get the current status from the coordinator."""
        return self.coordinator.get_status(self._serial_number)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.user_aircon_settings.quiet_mode_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the quiet mode setting on."""
        await self._status.user_aircon_settings.set_quiet_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the quiet mode setting off."""
        await self._status.user_aircon_settings.set_quiet_mode(False)


class TurboModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo turbo mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "turbo_mode"
    _attr_entity_category = CONFIG_CATEGORY
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_entity_registry_enabled_default = True

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._serial_number: str = serial_number
        self._attr_unique_id: str = f"{self._serial_number}_{self._attr_translation_key}"
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
        )
        self.on_icon = "mdi:fan-plus"
        self.off_icon = "mdi:fan"

    @property
    def _status(self) -> ActronAirNeoStatus:
        """Get the current status from the coordinator."""
        return self.coordinator.get_status(self._serial_number)

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.user_aircon_settings.turbo_enabled

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return self.on_icon if self.is_on else self.off_icon

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the turbo mode on."""
        await self._status.user_aircon_settings.set_turbo_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the turbo mode off."""
        await self._status.user_aircon_settings.set_turbo_mode(False)
