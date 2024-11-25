from homeassistant.helpers.entity import Entity
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Actron Neo diagnostic sensors."""
    api = hass.data[DOMAIN][entry.entry_id]
    serial_number = entry.data.get("serial_number")

    diagnostic_sensors = [
        ActronNeoDiagnosticSensor(api, "Master WC Model", lambda: api.get_master_model(serial_number)),
        ActronNeoDiagnosticSensor(api, "Master Serial", lambda: api.get_master_serial(serial_number)),
        ActronNeoDiagnosticSensor(api, "Master WC Firmware Version", lambda: api.get_master_firmware(serial_number)),
        ActronNeoDiagnosticSensor(api, "Outdoor Unit Model", lambda: api.get_outdoor_unit_model(serial_number)),
    ]

    async_add_entities(diagnostic_sensors)

    """Set up Actron Neo zone sensors."""
    api = hass.data[DOMAIN][entry.entry_id]
    serial_number = entry.data.get("serial_number")

    zones = await api.get_zones(serial_number)
    sensors = [ActronZoneSensor(api, serial_number, zone) for zone in zones]
    async_add_entities(sensors)

class ActronNeoDiagnosticSensor(Entity):
    """Representation of a diagnostic sensor."""

    def __init__(self, api, name, value_getter):
        self._api = api
        self._name = name
        self._value_getter = value_getter
        self._value = None

    @property
    def name(self):
        return f"Actron Neo {self._name}"

    @property
    def state(self):
        return self._value

    async def async_update(self):
        """Fetch new state data for the sensor."""
        self._value = await self._value_getter()
    
class ActronZoneSensor(Entity):
    """Representation of a zone sensor."""

    def __init__(self, coordinator, api, serial_number):
        self._coordinator = coordinator
        self._api = api
        self._serial_number = serial_number
        self._zone = zone
        self._name = f"Zone {zone['zone_id']} - {zone['name']}"
        self._temperature = zone["temperature"]
        self._humidity = zone["humidity"]

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._temperature

    @property
    def extra_state_attributes(self):
        return {
            "humidity": self._humidity,
            "enabled": self._zone["enabled"],
            "common_zone": self._zone["common_zone"],
        }

    async def async_update(self):
        """Fetch new state data for the sensor."""
        zones = await self._api.get_zones(self._serial_number)
        for zone in zones:
            if zone["zone_id"] == self._zone["zone_id"]:
                self._temperature = zone["temperature"]
                self._humidity = zone["humidity"]
                self._zone = zone
                break
