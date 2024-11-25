from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
)
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_AUTO,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS
from . import DOMAIN

class ActronSystemClimate(ClimateEntity):
    """Representation of the Actron Neo system."""

    def __init__(self, coordinator, api, serial_number):
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._name = "Actron Neo"
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temp = None
        self._fan_mode = "AUTO"
        self._continuous = False

    @property
    def name(self):
        return self._name

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO]

    @property
    def fan_modes(self):
        return ["AUTO", "LOW", "MED", "HIGH"]

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    @property
    def state(self):
        """Return the HVAC mode."""
        status = self._coordinator.data
        return status.get("AirconSystem", {}).get("Mode", "off").lower()

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVAC_MODE_OFF:
            await self._api.set_system_mode(self._serial_number, is_on=False)
        else:
            await self._api.set_system_mode(self._serial_number, is_on=True, mode=hvac_mode)
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        mode = self._hvac_mode.lower()
        if mode == "cool":
            await self._api.set_temperature(self._serial_number, mode="COOL", temperature=temp)
        elif mode == "heat":
            await self._api.set_temperature(self._serial_number, mode="HEAT", temperature=temp)
        elif mode == "auto":
            await self._api.set_temperature(self._serial_number, mode="AUTO", temperature={"cool": temp, "heat": temp})
        self._target_temp = temp
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        await self._api.set_fan_mode(self._serial_number, fan_mode=fan_mode, continuous=self._continuous)
        self._fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_turn_on_continuous(self, continuous: bool):
        self._continuous = continuous
        await self._api.set_fan_mode(self._serial_number, fan_mode=self._fan_mode, continuous=continuous)
        self.async_write_ha_state()
    
    async def async_update(self):
        """Fetch new state data for the climate entity."""
        status = self._coordinator.data
        self._hvac_mode = status.get("AirconSystem", {}).get("Mode", "off").lower()
        self._target_temp = status.get("AirconSystem", {}).get("UserAirconSettings.TemperatureSetpoint_Cool_oC")
        self._fan_mode = status.get("AirconSystem", {}).get("FanMode", "auto")
        self._current_temp = status.get("AirconSystem", {}).get("LiveTemp_oC", None)

class ActronZoneClimate(ClimateEntity):
    """Representation of an Actron Neo zone."""

    def __init__(self, coordinator, api, serial_number):
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._zone_id = zone_id
        self._name = f"Zone {zone_id}"
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temp = None

    @property
    def name(self):
        return self._name

    @property
    def hvac_modes(self):
        return [HVAC_MODE_OFF, HVAC_MODE_COOL, HVAC_MODE_HEAT, HVAC_MODE_AUTO]

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get("temperature")
        mode = self._hvac_mode.lower()
        await self._api.set_temperature(self._serial_number, mode=mode.upper(), temperature=temp, zone=self._zone_id)
        self._target_temp = temp
        self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for the climate entity."""
        status = self._coordinator.data
        self._hvac_mode = status.get("AirconSystem", {}).get("Mode", "off").lower()
        self._target_temp = status.get("AirconSystem", {}).get("UserAirconSettings.TemperatureSetpoint_Cool_oC")
        self._fan_mode = status.get("AirconSystem", {}).get("FanMode", "auto")
        self._current_temp = status.get("AirconSystem", {}).get("LiveTemp_oC", None)

