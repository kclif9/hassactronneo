"""Switch platform for Actron Neo integration."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Neo switches."""
    # Extract API and coordinator from hass.data
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]  # ActronNeoAPI instance
    serial_number = entry.data.get("serial_number")

    # Create a switch for the continuous fan
    async_add_entities([ActronNeoContinuousFanSwitch(api, serial_number)])


class ActronNeoContinuousFanSwitch(SwitchEntity):
    """Representation of the Actron Air Neo continuous fan switch."""

    def __init__(self, api, serial_number) -> None:
        """Initialize the continuous fan switch."""
        self._api = api
        self._serial_number = serial_number
        self._is_on = None
        self._name = "Actron Air Neo Continuous Fan"
        self._fan_mode = None

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"actron_neo_{self._name.replace(' ', '_').lower()}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._is_on

    @property
    def extra_state_attributes(self):
        """Extra state attributes."""
        return {"fan_mode": self._fan_mode}

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the continuous fan on."""
        if self._fan_mode:
            fan_mode = f"{self._fan_mode}+CONT"
            await self._api.set_fan_mode(
                serial_number=self._serial_number, fan_mode=fan_mode
            )
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the continuous fan off."""
        if self._fan_mode:
            await self._api.set_fan_mode(
                serial_number=self._serial_number, fan_mode=self._fan_mode
            )
            self._is_on = False
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state of the continuous fan."""
        status = await self._api.get_ac_status(self._serial_number)
        fan_mode = (
            status.get("lastKnownState", {})
            .get("UserAirconSettings", {})
            .get("FanMode")
        )
        self._is_on = fan_mode.endswith("+CONT")
        self._fan_mode = fan_mode.replace("+CONT", "")
