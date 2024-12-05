"""Climate platform for Actron Air Neo integration."""

from typing import Any

from actron_neo_api import ActronNeoAPI

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN

FAN_MODE_MAPPING = {
    "auto": "AUTO",
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH",
}
HVAC_MODE_OFF = HVACMode.OFF
HVAC_MODE_COOL = HVACMode.COOL
HVAC_MODE_HEAT = HVACMode.HEAT
HVAC_MODE_AUTO = HVACMode.AUTO
HVAC_MODE_FAN = HVACMode.FAN_ONLY
HVAC_MODE_MAPPING = {
    "COOL": HVAC_MODE_COOL,
    "HEAT": HVAC_MODE_HEAT,
    "AUTO": HVAC_MODE_AUTO,
    "FAN": HVAC_MODE_FAN,
    "OFF": HVAC_MODE_OFF,
}
TEMP_CELSIUS = UnitOfTemperature.CELSIUS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air Neo climate entities."""
    # Get the API and coordinator from the integration
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    coordinator = data["coordinator"]
    ac_unit = data["ac_unit"]

    # Add system-wide climate entity
    async_add_entities(
        [ActronSystemClimate(coordinator, api, ac_unit, entry.data["serial_number"])]
    )


class ActronSystemClimate(ClimateEntity):
    """Representation of the Actron Air Neo system."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, api: ActronNeoAPI, ac_unit, serial_number: str
    ) -> None:
        """Initialise a Actron Air Neo unit."""
        super().__init__()
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._name = "Actron Neo"
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temperature = None
        self._fan_mode = "AUTO"
        self._continuous = False
        self._current_humidity = None
        self._current_temperature = None
        self._attr_fan_mode = "auto"
        self._attr_fan_modes = ["auto", "low", "medium", "high"]
        self._ac_unit = ac_unit

    @property
    def name(self) -> str:
        """Return the unit name."""
        return self._name

    @property
    def device_info(self):
        """Return the device information."""
        return self._ac_unit.device_info

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._ac_unit.unique_id}_{self._name.replace(' ', '_').lower()}"

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return HVAC Modes."""
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO]

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode."""
        return self._attr_fan_mode

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return list(FAN_MODE_MAPPING.keys())

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit."""
        return TEMP_CELSIUS

    @property
    def current_humidity(self) -> float:
        """Return the current humidity"""
        return self._current_humidity

    @property
    def current_temperature(self) -> float:
        """Return the current temperature"""
        return self._current_temperature

    @property
    def target_temperature(self) -> float:
        """Return the current temperature"""
        return self._target_temperature

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE 
            | ClimateEntityFeature.FAN_MODE 
            | ClimateEntityFeature.TURN_ON 
            | ClimateEntityFeature.TURN_OFF
        )

    @property
    def state(self) -> HVACMode:
        """Return the HVAC mode."""
        raw_mode = (
            self._coordinator.data.get("lastKnownState", {})
            .get("UserAirconSettings", {})
            .get("Mode", "")
        )
        
        # Map API modes to Home Assistant HVAC modes
        return HVAC_MODE_MAPPING.get(raw_mode, HVAC_MODE_OFF)

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature that can be set."""
        return 16.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature that can be set."""
        return 30.0

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set a new fan mode."""
        api_fan_mode = FAN_MODE_MAPPING.get(fan_mode.lower())
        if api_fan_mode is None:
            raise ValueError(f"Fan mode '{fan_mode}' is not valid. Valid modes are: {list(FAN_MODE_MAPPING.keys())}")
        
        await self._api.set_fan_mode(self._serial_number, fan_mode=api_fan_mode)
        self._attr_fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVAC_MODE_OFF:
            await self._api.set_system_mode(self._serial_number, is_on=False)
        else:
            await self._api.set_system_mode(
                self._serial_number, is_on=True, mode=hvac_mode
            )
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature."""
        temp = kwargs.get("temperature")
        mode = self._hvac_mode.lower()
        if mode == "cool":
            await self._api.set_temperature(
                self._serial_number, mode="COOL", temperature=temp
            )
        elif mode == "heat":
            await self._api.set_temperature(
                self._serial_number, mode="HEAT", temperature=temp
            )
        elif mode == "auto":
            await self._api.set_temperature(
                self._serial_number,
                mode="AUTO",
                temperature={"cool": temp, "heat": temp},
            )
        self._target_temperature = temp
        self.async_write_ha_state()

    async def async_turn_on_continuous(self, continuous: bool) -> None:
        """Set the continuous mode."""
        self._continuous = continuous
        await self._api.set_fan_mode(
            self._serial_number, fan_mode=self._fan_mode, continuous=continuous
        )
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for the climate entity."""
        await self._coordinator.async_request_refresh()
        status = self._coordinator.data

        raw_mode = (
            status.get("lastKnownState", {})
            .get("UserAirconSettings", {})
            .get("Mode", "OFF")
        )
        self._hvac_mode = HVAC_MODE_MAPPING.get(raw_mode, HVAC_MODE_OFF)
        self._target_temperature = (
            status.get("lastKnownState", {})
            .get("UserAirconSettings", {})
            .get("TemperatureSetpoint_Cool_oC", "")
        )
        self._current_humidity = (
            status.get("lastKnownState", {})
            .get("MasterInfo", {})
            .get("LiveHumidity_pc", "")
        )
        self._current_temperature = (
            status.get("lastKnownState", {})
            .get("MasterInfo", {})
            .get("LiveTemp_oC", "")
        )
        api_fan_mode = (
            status.get("lastKnownState", {})
            .get("UserAirconSettings", {})
            .get("FanMode", "").upper()
        )
        self._attr_fan_mode = {v: k for k, v in FAN_MODE_MAPPING.items()}.get(api_fan_mode, "auto")

