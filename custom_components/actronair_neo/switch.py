"""Switch platform for Actron Neo integration."""

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ActronConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


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

    for system in coordinator.api.systems:
        serial_number = system["serial"]
        entities.append(AwayModeSwitch(coordinator, serial_number))
        entities.append(ContinuousFanSwitch(coordinator, serial_number))
        entities.append(QuietModeSwitch(coordinator, serial_number))

        if coordinator.data[serial_number].get("UserAirconSettings", {}).get("TurboMode").get("Supported"):
            entities.append(TurboModeSwitch(coordinator, serial_number))

    # Add all switches
    async_add_entities(entities)


class AwayModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo away mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "away_mode"

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the away mode switch."""
        super().__init__(coordinator)
        self._api = coordinator.api
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._attr_unique_id = (
            f"{self._serial_number}_{self._attr_translation_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.get("UserAirconSettings", {}).get("AwayMode")

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return "mdi:home-export-outline" if self.is_on else "mdi:home-import-outline"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        await self._api.set_away_mode(
            serial_number=self._serial_number, mode=True
        )
        self._status["UserAirconSettings"]["AwayMode"] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        await self._api.set_away_mode(
            serial_number=self._serial_number, mode=False
        )
        self._status["UserAirconSettings"]["AwayMode"] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class ContinuousFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo continuous fan switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "continuous_fan"

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the continuous fan switch."""
        super().__init__(coordinator)
        self._api = coordinator.api
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._attr_unique_id = (
            f"{self._serial_number}_{self._attr_translation_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        fan_mode = self._status.get("UserAirconSettings", {}).get("FanMode", "")
        return fan_mode.endswith("+CONT")

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return "mdi:fan" if self.is_on else "mdi:fan-off"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        self._is_on = True
        self.async_write_ha_state()

        fan_mode = self._status.get("UserAirconSettings", {}).get("FanMode", "")
        if fan_mode:
            new_fan_mode = f"{fan_mode.replace('+CONT', '')}+CONT"
            await self._api.set_fan_mode(
                serial_number=self._serial_number, fan_mode=new_fan_mode
            )
            self._status["UserAirconSettings"]["FanMode"] = new_fan_mode
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        self._is_on = False
        self.async_write_ha_state()

        fan_mode = self._status.get("UserAirconSettings", {}).get("FanMode", "")
        if fan_mode:
            new_fan_mode = fan_mode.replace("+CONT", "")
            await self._api.set_fan_mode(
                serial_number=self._serial_number, fan_mode=new_fan_mode
            )
            self._status["UserAirconSettings"]["FanMode"] = new_fan_mode
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()


class QuietModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo quiet mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "quiet_mode"

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the quiet mode switch."""
        super().__init__(coordinator)
        self._api = coordinator.api
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._attr_unique_id = (
            f"{self._serial_number}_{self._attr_translation_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.get("UserAirconSettings", {}).get("QuietModeEnabled")

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return "mdi:volume-low" if self.is_on else "mdi:volume-high"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        self._is_on = True
        self.async_write_ha_state()

        await self._api.set_quiet_mode(
            serial_number=self._serial_number, mode=True
        )
        self._status["UserAirconSettings"]["QuietModeEnabled"] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        self._is_on = False
        self.async_write_ha_state()

        await self._api.set_quiet_mode(
            serial_number=self._serial_number, mode=False
        )
        self._status["UserAirconSettings"]["QuietModeEnabled"] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()


class TurboModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo turbo mode switch."""

    _attr_has_entity_name = True
    _attr_translation_key = "turbo_mode"

    def __init__(self, coordinator, serial_number) -> None:
        """Initialize the turbo mode switch."""
        super().__init__(coordinator)
        self._api = coordinator.api
        self._serial_number = serial_number
        self._status = coordinator.data[self._serial_number]
        self._attr_unique_id = (
            f"{self._serial_number}_{self._attr_translation_key}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._status.get("UserAirconSettings", {}).get("TurboMode").get("Enabled")

    @property
    def icon(self) -> str:
        """Return the icon based on the state."""
        return "mdi:fan-plus" if self.is_on else "mdi:fan"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the continuous fan on."""
        self._is_on = True
        self.async_write_ha_state()

        await self._api.set_turbo_mode(
            serial_number=self._serial_number, mode=True
        )
        self._status["UserAirconSettings"]["TurboMode"]["Enabled"] = True
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the continuous fan off."""
        self._is_on = False
        self.async_write_ha_state()

        await self._api.set_turbo_mode(
            serial_number=self._serial_number, mode=False
        )
        self._status["UserAirconSettings"]["TurboMode"]["Enabled"] = False
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
