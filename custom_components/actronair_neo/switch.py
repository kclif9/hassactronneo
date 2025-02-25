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

    assert coordinator.systems is not None

    systems = coordinator.systems["_embedded"]["ac-system"]
    for system in systems:
        serial_number = system["serial"]
        entities.append(ContinuousFanSwitch(coordinator, serial_number))

    # Add all switches
    async_add_entities(entities)


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
        self._attr_name = "Continuous Fan"
        self._attr_unique_id = (
            f"{self._serial_number}_{self._attr_name}"
        )
        self._is_on = self.is_on
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
        }

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        fan_mode = self._status.get("UserAirconSettings", {}).get("FanMode", "")
        return fan_mode.endswith("+CONT")

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
            await self.coordinator.async_request_refresh()
