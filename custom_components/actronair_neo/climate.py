"""Climate platform for Actron Air Neo integration."""

from typing import Any

from actron_neo_api import ActronNeoAPI
from .device import ACUnit

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

DEFAULT_TEMPERATURE = None
DEFAULT_MODE = "OFF"
DEFAULT_HUMIDITY = None
DEFAULT_TEMP_MIN = 16.0
DEFAULT_TEMP_MAX = 32.0
FAN_MODE_MAPPING = {
    "auto": "AUTO",
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH",
}
FAN_MODE_MAPPING_REVERSE = {v: k for k, v in FAN_MODE_MAPPING.items()}
HVAC_MODE_OFF = HVACMode.OFF
HVAC_MODE_COOL = HVACMode.COOL
HVAC_MODE_HEAT = HVACMode.HEAT
HVAC_MODE_AUTO = HVACMode.AUTO
HVAC_MODE_FAN = HVACMode.FAN_ONLY
HVAC_MODE_MAPPING = {
    mode.value.upper(): mode
    for mode in [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO, HVACMode.FAN_ONLY]
}
SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)
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
    entity_prefix = data["entity_prefix"]

    # Add system-wide climate entity
    async_add_entities(
        [ActronSystemClimate(coordinator, api, ac_unit, entry.data["serial_number"], entity_prefix)]
    )


class ActronSystemClimate(ClimateEntity):
    """Representation of the Actron Air Neo system."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, api: ActronNeoAPI, ac_unit: ACUnit, serial_number: str, entity_prefix: str
    ) -> None:
        """Initialise a Actron Air Neo unit."""
        super().__init__()
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._entity_prefix = entity_prefix
        self._hvac_mode = DEFAULT_MODE
        api_fan_mode = (
            self._coordinator.data.get("UserAirconSettings", {})
            .get("FanMode", DEFAULT_MODE).upper()
        )
        self._attr_fan_mode = FAN_MODE_MAPPING_REVERSE.get(api_fan_mode, "auto")
        self._attr_fan_modes = ["auto", "low", "medium", "high"]
        self._ac_unit = ac_unit

    @property
    def _status(self):
        """Shortcut to coordinator data."""
        return self._coordinator.data

    @property
    def name(self) -> str:
        """Return the unit name."""
        return "AC Unit"

    @property
    def device_info(self):
        """Return the device information."""
        return self._ac_unit.device_info

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._entity_prefix}_ac_unit"

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
        return (
            self._status.get("MasterInfo", {})
            .get("LiveHumidity_pc", DEFAULT_HUMIDITY)
        )

    @property
    def current_temperature(self) -> float:
        """Return the current temperature"""
        return (
            self._status.get("MasterInfo", {})
            .get("LiveTemp_oC", DEFAULT_TEMPERATURE)
        )

    @property
    def target_temperature(self) -> float:
        """Return the current temperature"""
        return (
            self._status.get("UserAirconSettings", {})
            .get("TemperatureSetpoint_Cool_oC", DEFAULT_TEMPERATURE)
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        return SUPPORTED_FEATURES

    @property
    def state(self) -> HVACMode:
        """Return the HVAC mode."""
        raw_mode = (
            self._status.get("UserAirconSettings", {})
            .get("Mode", DEFAULT_MODE)
        )
        
        # Map API modes to Home Assistant HVAC modes
        return HVAC_MODE_MAPPING.get(raw_mode, HVAC_MODE_OFF)

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature that can be set."""
        return (
            self._coordinator.data.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Min", DEFAULT_TEMP_MIN)
        )

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature that can be set."""
        return (
            self._coordinator.data.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Max", DEFAULT_TEMP_MAX)
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set a new fan mode."""
        api_fan_mode = FAN_MODE_MAPPING.get(fan_mode.lower())
        await self._api.set_fan_mode(self._serial_number, fan_mode=api_fan_mode)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVAC_MODE_OFF:
            await self._api.set_system_mode(self._serial_number, is_on=False)
        else:
            await self._api.set_system_mode(
                self._serial_number, is_on=True, mode=hvac_mode
            )
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature."""
        temp = kwargs.get("temperature")
        mode = self._hvac_mode.lower()

        if not (self.min_temp <= temp <= self.max_temp):
            raise ValueError(f"Temperature {temp} is out of range ({self.min_temp}-{self.max_temp}).")

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
        self.async_write_ha_state()

    async def async_turn_on_continuous(self, continuous: bool) -> None:
        """Set the continuous mode."""
        await self._api.set_fan_mode(
            self._serial_number, fan_mode=self._attr_fan_mode, continuous=continuous
        )
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch new state data for the climate entity."""
        await self._coordinator.async_request_refresh()
        status = self._coordinator.data

        raw_mode = (
            self._status.get("UserAirconSettings", {})
            .get("Mode", DEFAULT_MODE)
        )
        self._hvac_mode = HVAC_MODE_MAPPING.get(raw_mode, HVAC_MODE_OFF)
        api_fan_mode = (
            self._status.get("UserAirconSettings", {})
            .get("FanMode", DEFAULT_MODE).upper()
        )
        self._attr_fan_mode = FAN_MODE_MAPPING_REVERSE.get(api_fan_mode, "auto")

