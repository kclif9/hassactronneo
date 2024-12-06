"""Switch platform for Actron Neo integration."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import ACZone

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
    ac_unit = data["ac_unit"]

    # Fetch the status and create ZoneSwitches
    status = coordinator.data
    zones = status.get("RemoteZoneInfo", [])
    entities = []

    for zone_number, zone in enumerate(zones, start=1):
        if zone["NV_Exists"]:
            zone_name = zone["NV_Title"]
            ac_zone = ACZone(ac_unit, zone_number, zone_name)
            entities.append(ZoneSwitch(api, coordinator, serial_number, ac_zone))

    # Create a switch for the continuous fan
    entities.append(ContinuousFanSwitch(api, coordinator, serial_number, ac_unit))

    # Add all switches
    async_add_entities(entities)


class ContinuousFanSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Actron Air Neo continuous fan switch."""

    def __init__(self, api, coordinator, serial_number, ac_unit) -> None:
        """Initialize the continuous fan switch."""
        super().__init__(coordinator)
        self._api = api
        self._serial_number = serial_number
        self._name = "Continuous Fan"
        self._ac_unit = ac_unit

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._ac_unit.unique_id}_{self._name.replace(' ', '_').lower()}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("UserAirconSettings", {})
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
                status.get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            return {"fan_mode": fan_mode.replace("+CONT", "")}
        return {}

    @property
    def device_info(self):
        """Return the device information."""
        return self._ac_unit.device_info

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the continuous fan on."""
        status = self.coordinator.data
        if status:
            fan_mode = (
                status.get("UserAirconSettings", {})
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
                status.get("UserAirconSettings", {})
                .get("FanMode", "")
            )
            if fan_mode:
                new_fan_mode = fan_mode.replace("+CONT", "")
                await self._api.set_fan_mode(
                    serial_number=self._serial_number, fan_mode=new_fan_mode
                )
                await self.coordinator.async_request_refresh()


class ZoneSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a zone switch."""

    def __init__(self, api, coordinator, serial_number, ac_zone) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._api = api
        self._ac_zone = ac_zone
        self._serial_number = serial_number
        self._zone_number = ac_zone.zone_number()
        self._name = f"Zone {self._zone_number} Enabled"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._ac_zone.unique_id}_{self._name.replace(' ', '_').lower()}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        status = self.coordinator.data
        if status:
            enabled_zones = (
                status.get("UserAirconSettings", {})
                .get("EnabledZones", "")
            )
            zone_state = enabled_zones[self._zone_number - 1]
            return zone_state
        return False

    @property
    def device_info(self):
        """Return the device information."""
        return self._ac_zone.device_info

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the zone on."""
        await self._api.set_zone(
            serial_number=self._serial_number,
            zone_number=self._zone_number,
            is_enabled=True,
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the zone off."""
        await self._api.set_zone(
            serial_number=self._serial_number,
            zone_number=self._zone_number,
            is_enabled=False,
        )
        await self.coordinator.async_request_refresh()
