"""Switch platform for Actron Neo integration."""

import asyncio
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import ACUnit

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Neo switches."""
    # Extract API and coordinator from hass.data
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]  # ActronNeoAPI instance
    coordinator = data["coordinator"]
    serial_number = entry.data.get("serial_number")
    device_info = data["ac_unit"]['device_info']

    # Create a switch for the continuous fan
    async_add_entities([ContinuousFanSwitch(api, coordinator, serial_number, device_info)])

class ContinuousFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo continuous fan switch."""

    def __init__(self, api, coordinator, serial_number, ac_unit) -> None:
        """Initialize the continuous fan switch."""
        super().__init__(coordinator)
        self._api = api
        self._serial_number = serial_number
        self._name = "Continuous Fan"
        self._ac_unit = ac_unit
        self._device_info = ac_unit.device_info

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._ac_unit.unique_id}_continuous_fan"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("lastKnownState", {})
                .get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            return fan_mode.endswith("+CONT")
        return False

    @property
    def extra_state_attributes(self):
        """Extra state attributes."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("lastKnownState", {})
                .get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            return {"fan_mode": fan_mode.replace("+CONT", "")}
        return {}

    @property
    def device_info(self):
        """Return the device information."""
        return self._device_info

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the continuous fan on."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("lastKnownState", {})
                .get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            if fan_mode:
                new_fan_mode = f"{fan_mode.replace('+CONT', '')}+CONT"
                await self._api.set_fan_mode(
                    serial_number=self._serial_number, fan_mode=new_fan_mode
                )
                await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the continuous fan off."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("lastKnownState", {})
                .get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            if fan_mode:
                new_fan_mode = fan_mode.replace("+CONT", "")
                await self._api.set_fan_mode(
                    serial_number=self._serial_number, fan_mode=new_fan_mode
                )
                await self.coordinator.async_request_refresh()