"""Sensor platform for Actron Air Neo integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .entity import DiagnosticSensor


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

    # Obtain AC Units
    system = await api.get_ac_systems()[0]
    status = await api.get_ac_status(serial_number)

    # Create the aircon device
    ac_unit = ACUnit(serial_number, system, status)

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
        DiagnosticSensor(
            coordinator, name, path, key, ac_unit.device_info, unit
        )
        for name, path, key, unit in diagnostic_configs
    ]

    # Fetch Zones
    zones = status.get("lastKnownState", {}).get("RemoteZoneInfo", [])

    zone_sensors = []
    ac_zones = []

    # Create zones & sensors
    for zone_number, zone in enumerate(zones, start=1):
        if zone["NV_Exists"]:
            # Create zone device
            zone_name = zone["NV_Title"]
            ac_zone = ACZone(ac_unit, zone_number, zone_name)
            ac_zones.append(ac_zone)
            zone_sensors.extend(create_zone_sensors(coordinator, ac_zone))

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
        zone_assignment = ac_zones[zone_id - 1]
        zone_peripheral = ZonePeripheral(
            ac_unit,
            logical_address,
            zone_serial,
            mac_address,
            zone_assignment,
            device_type,
            software_version,
        )
        zone_sensors.extend(create_peripheral_sensors(coordinator, zone_peripheral))

    # Add all sensors
    async_add_entities(diagnostic_sensors + zone_sensors)


def create_zone_sensors(coordinator, ac_zone):
    """Create all sensors for a given zone device."""
    return [
        ZonePostionSensor(coordinator, ac_zone),
        ZoneTemperatureSensor(coordinator, ac_zone),
        ZoneHumiditySensor(coordinator, ac_zone),
    ]


def create_peripheral_sensors(coordinator, zone_peripheral):
    """Create all sensors for a given peripheral zone device."""
    return [
        PeripheralBatterySensor(coordinator, zone_peripheral),
        PeripheralTemperatureSensor(coordinator, zone_peripheral),
        PeripheralHumiditySensor(coordinator, zone_peripheral),
    ]


class ACUnit:
    """Representation of an Actron Neo Air Conditioner device."""

    def __init__(self, serial_number, system, status) -> None:
        """Initialize the air conditioner device."""
        self._serial_number = serial_number
        self._status = status
        self._manufacturer = "Actron Air"
        self._name = system["_embedded"]["ac-system"][0]["description"]
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
        return f"actronair_neo_{self._serial_number}"
    
    def manufacturer(self) -> str:
        """Return the manufacturer name"""
        return self._manufacturer


class ACZone:
    """Representation of an Air Conditioner Zone."""

    def __init__(self, ac_unit, zone_number, name) -> None:
        """Initialize the zone device."""
        self._ac_unit = ac_unit
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
            "manufacturer": self._ac_unit.manufacturer,
            "model": self._device_type,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        ac_unit_entity_id = self._ac_unit.unique_id()
        return f"{ac_unit_entity_id}_{self._name.replace(' ', '_').lower()}"

    def zone_number(self) -> int:
        """Return the zone number."""
        return self._zone_number


class ZonePeripheral:
    """Representation of an Actron Air Zone Peripheral."""

    def __init__(
        self,
        ac_unit,
        logical_address,
        serial,
        mac_address,
        zone_assignment,
        device_type,
        software_version,
    ) -> None:
        """Initialize the zone device."""
        self._ac_unit = ac_unit
        self._logical_address = logical_address
        self._serial = serial
        self._mac_address = mac_address
        self._zone_assignment = zone_assignment
        self._device_type = device_type
        self._software_version = software_version
        self._name = f"{self._device_type} {self._logical_address}"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._serial)},
            "name": self._name,
            "manufacturer": self._ac_unit.manufacturer,
            "model": self._device_type,
            "connections": {("mac", self._mac_address)},  # MAC address
            "serial_number": self._serial,
            "sw_version": self._software_version,
            "via_device": (DOMAIN, self._zone_assignment),
        }

    def logical_address(self) -> str:
        """Return the logical address."""
        return self._logical_address

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        ac_unit_entity_id = self._ac_unit.unique_id()
        return f"{ac_unit_entity_id}_{self._name.replace(' ', '_').lower()}"


class BaseZoneSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    def __init__(
        self, coordinator, ac_zone, name, state_key, unit_of_measurement=None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ac_zone = ac_zone
        self._zone_number = ac_zone.zone_number()
        self._name = name
        self._state_key = state_key
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._ac_zone.device_info['name']} {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._ac_zone.unique_id}_{self._name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        """Return the device information."""
        return self._ac_zone.device_info

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

    def __init__(self, coordinator, ac_zone) -> None:
        """Initialize the position sensor."""
        super().__init__(coordinator, ac_zone, "Position", "ZonePosition", "%")


class ZoneTemperatureSensor(BaseZoneSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, ac_zone) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, ac_zone, "Temperature", "LiveTemp_oC", "°C")


class ZoneHumiditySensor(BaseZoneSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, ac_zone) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, ac_zone, "Humidity", "LiveHumidity_pc", "%")


class BasePeripheralSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    def __init__(
        self, coordinator, zone_peripheral, name, path, key, unit_of_measurement=None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_peripheral = zone_peripheral
        self._name = name
        self._path = path if isinstance(path, list) else [path]  # Ensure path is a list
        self._key = key
        self._unit_of_measurement = unit_of_measurement

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._zone_peripheral.device_info['name']} {self._name}"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._zone_peripheral.unique_id}_{self._name.lower().replace(' ', '_')}"

    @property
    def device_info(self):
        """Return the device information."""
        return self._zone_peripheral.device_info

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
            if peripheral["LogicalAddress"] == self._zone_peripheral.logical_address():
                for key in self._path:
                    peripheral = peripheral.get(key, {})
                return peripheral.get(self._key, None)
        return None

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement


class PeripheralBatterySensor(BasePeripheralSensor):
    """Battery sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_peripheral) -> None:
        """Initialize the battery sensor."""
        super().__init__(
            coordinator,
            zone_peripheral,
            [],
            "RemainingBatteryCapacity_pc",
            "%",
        )


class PeripheralTemperatureSensor(BasePeripheralSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_peripheral) -> None:
        """Initialize the temperature sensor."""
        super().__init__(
            coordinator,
            zone_peripheral,
            ["SHTC1"],
            "Temperature_oC",
            "°C",
        )


class PeripheralHumiditySensor(BasePeripheralSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, zone_peripheral) -> None:
        """Initialize the humidity sensor."""
        super().__init__(
            coordinator,
            zone_peripheral,
            ["lastKnownState", "AirconSystem", "Peripherals", "SHTC1"],
            "RelativeHumidity_pc",
            "%",
        )
