from homeassistant.components.switch import SwitchEntity

class ActronNeoContinuousFanSwitch(SwitchEntity):
    """Representation of the continuous fan mode switch."""

    def __init__(self, coordinator, api, serial_number):
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._is_on = False

    @property
    def name(self):
        return "Continuous Fan Mode"

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self):
        await self._api.set_fan_mode(self._serial_number, self._api.get_current_fan_mode(), continuous=True)
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self):
        await self._api.set_fan_mode(self._serial_number, self._api.get_current_fan_mode(), continuous=False)
        self._is_on = False
        self.async_write_ha_state()
