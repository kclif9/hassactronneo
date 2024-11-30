"""Sensor platform for Actron Air Neo integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import ActronNeoDiagnosticSensor


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Actron Air Neo sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    serial_number = data["serial_number"]

    # Setup the coordinator
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    # Obtain status data
    status = await api.get_ac_status(serial_number)

    # Create the aircon device
    aircon_device = AirconDevice(serial_number, status)

    # Diagnostic sensor configurations
    diagnostic_configs = [
        ("Clean Filter", ["lastKnownState", "Alerts"], "CleanFilter", None),
        ("Defrost Mode", ["lastKnownState", "Alerts"], "Defrosting", None),
        (
            "Compressor Chasing Temperature",
            ["lastKnownState", "LiveAircon"],
            "CompressorChasingTemperature",
            "°C",
        ),
        (
            "Compressor Live Temperature",
            ["lastKnownState", "LiveAircon"],
            "CompressorLiveTemperature",
            "°C",
        ),
        ("Compressor Mode", ["lastKnownState", "LiveAircon"], "CompressorMode", None),
        ("System On", ["lastKnownState", "LiveAircon"], "SystemOn", None),
        (
            "Compressor Speed",
            ["lastKnownState", "LiveAircon", "OutdoorUnit"],
            "CompSpeed",
            "rpm",
        ),
        (
            "Compressor Power",
            ["lastKnownState", "LiveAircon", "OutdoorUnit"],
            "CompPower",
            "W",
        ),
        (
            "Outdoor Temperature",
            ["lastKnownState", "MasterInfo"],
            "LiveOutdoorTemp_oC",
            "°C",
        ),
        ("Humidity", ["lastKnownState", "MasterInfo"], "LiveHumidity_pc", "%"),
    ]

    # Create diagnostic sensors
    diagnostic_sensors = [
        ActronNeoDiagnosticSensor(
            coordinator, name, path, key, aircon_device.device_info, unit
        )
        for name, path, key, unit in diagnostic_configs
    ]

    # Fetch Zones
    zones = status.get("lastKnownState", {}).get("RemoteZoneInfo", [])

    zone_sensors = []
    zone_devices = []

    # Create zone sensors
    for zone_number, zone in enumerate(zones, start=1):
        if zone["NV_Exists"]:
            # Create zone device
            zone_name = zone["NV_Title"]
            zone_device = ActronZone(zone_number, zone_name)
            zone_devices.append(zone_device)
            zone_sensors.extend(create_zone_sensors(coordinator, zone_device))

    # Fetch Peripherals
    peripherals = (
        status.get("lastKnownState", {}).get("AirconSystem", {}).get("Peripherals", [])
    )

    for peripheral in peripherals:
        # Create zone sensor device
        logical_address = peripheral["LogicalAddress"]
        device_type = peripheral.get("DeviceType", None)
        zone_serial = peripheral["SerialNumber"]
        mac_address = peripheral["MACAddress"]
        zone_id = peripheral.get("ZoneAssignment")[0]
        firmware = peripheral.get("Firmware", {})
        installed_version = firmware.get("InstalledVersion", {})
        software_version = installed_version.get("NRF52", {})
        zone_assignment = zone_devices[zone_id - 1]
        zone_device = ActronZoneDevice(
            logical_address,
            zone_serial,
            mac_address,
            zone_assignment,
            device_type,
            software_version,
        )
        zone_sensors.extend(create_peripheral_sensors(coordinator, zone_device))

    # Add all sensors
    async_add_entities(diagnostic_sensors + zone_sensors)


def create_zone_sensors(coordinator, zone_device):
    """Create all sensors for a given zone device."""
    return [
        ZonePostionSensor(coordinator, zone_device),
        ZoneTemperatureSensor(coordinator, zone_device),
        ZoneHumiditySensor(coordinator, zone_device),
    ]


def create_peripheral_sensors(coordinator, zone_device):
    """Create all sensors for a given peripheral zone device."""
    return [
        ZoneSensorBatterySensor(coordinator, zone_device),
        ZoneSensorTemperatureSensor(coordinator, zone_device),
        ZoneSensorHumiditySensor(coordinator, zone_device),
    ]


class AirconDevice:
    """Representation of an Actron Neo Air Conditioner device."""

    def __init__(self, serial_number, status) -> None:
        """Initialize the air conditioner device."""
        self._serial_number = serial_number
        self._status = status
        self._manufacturer = "Actron Air"
        self._name = "Actron Air Neo Controller"
        self._firmware_version = (
            self._status.get("lastKnownState", {})
            .get("AirconSystem", {})
            .get("MasterWCFirmwareVersion", "Unknown")
        )
        self._model_name = (
            self._status.get("lastKnownState", {})
            .get("AirconSystem", {})
            .get("MasterWCModel", "Unknown")
        )

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": self._name,
            "manufacturer": self._manufacturer,
            "model": self._model_name,
            "sw_version": self._firmware_version,
            "serial_number": self._serial_number,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"actron_neo_zone_{self._name.replace(' ', '_').lower()}"


class ActronZone:
    """Representation of an Actron Air Zone."""

    def __init__(self, zone_number, name) -> None:
        """Initialize the zone device."""
        self._zone_number = zone_number
        self._serial = f"zone_{self._zone_number}"
        self._device_type = "Zone"
        self._name = f"Zone {name}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._zone_number)},
            "name": self._name,
            "manufacturer": "Actron",
            "model": self._device_type,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"actron_neo_zone_{self._name.replace(' ', '_').lower()}"

    def zone_number(self) -> int:
        """Return the zone number."""
        return self._zone_number


class ActronZoneDevice:
    """Representation of an Actron Air Zone Device."""

    def __init__(
        self,
        logical_address,
        serial,
        mac_address,
        zone_assignment,
        device_type,
        software_version,
    ) -> None:
        """Initialize the zone device."""
        self._logical_address = logical_address
        self._serial = serial
        self._mac_address = mac_address
        self._zone_assignment = zone_assignment
        self._device_type = device_type
        self._software_version = software_version

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial)},
            "name": f"{self._device_type} {self._logical_address}",
            "manufacturer": "Actron",
            "model": self._device_type,
            "connections": {("mac", self._mac_address)},  # MAC address
            "serial_number": self._serial,
            "sw_version": self._software_version,
            "via_device": (DOMAIN, self._zone_assignment),
        }

    def logical_address(self) -> str:
        """Return the logical address."""
        return self._logical_address


class BaseZoneSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    def __init__(
        self, coordinator, zone_device, name, state_key, unit_of_measurement=None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_device = zone_device
        self._zone_number = zone_device.zone_number()
        self._name = name
        self._state_key = state_key
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._zone_device.device_info['name']} {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._zone_device.device_info['identifiers']}_{self._name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        """Return the device information."""
        return self._zone_device.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        zones = self.coordinator.data.get("lastKnownState", {}).get(
            "RemoteZoneInfo", []
        )
        for zone_number, zone in enumerate(zones, start=1):
            if zone_number == self._zone_number:
                return zone.get(self._state_key, None)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement


class ZonePostionSensor(BaseZoneSensor):
    """Position sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the position sensor."""
        super().__init__(coordinator, zone_device, "Position", "ZonePosition", "%")


class ZoneTemperatureSensor(BaseZoneSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, zone_device, "Temperature", "LiveTemp_oC", "°C")


class ZoneHumiditySensor(BaseZoneSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, zone_device, "Humidity", "LiveHumidity_pc", "%")


class BasePeripheralSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    def __init__(
        self, coordinator, zone_device, name, path, key, unit_of_measurement=None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_device = zone_device
        self._name = name
        self._path = path if isinstance(path, list) else [path]  # Ensure path is a list
        self._key = key
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._zone_device.device_info['name']} {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._zone_device.device_info['identifiers']}_{self._name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        """Return the device information."""
        return self._zone_device.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        # Look up the state using the state key in the data.
        data_source = (
            self.coordinator.data.get("lastKnownState", {})
            .get("AirconSystem", {})
            .get("Peripherals", [])
        )
        for peripheral in data_source:
            if peripheral["LogicalAddress"] == self._zone_device.logical_address():
                for key in self._path:
                    peripheral = peripheral.get(key, {})
                return peripheral.get(self._key, None)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement


class ZoneSensorBatterySensor(BasePeripheralSensor):
    """Battery sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the battery sensor."""
        super().__init__(
            coordinator,
            zone_device,
            [],
            "RemainingBatteryCapacity_pc",
            "%",
        )


class ZoneSensorTemperatureSensor(BasePeripheralSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            zone_device,
            ["SHTC1"],
            "Temperature_oC",
            "°C",
        )


class ZoneSensorHumiditySensor(BasePeripheralSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_device) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            zone_device,
            ["lastKnownState", "AirconSystem", "Peripherals", "SHTC1"],
            "RelativeHumidity_pc",
            "%",
        )
