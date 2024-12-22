"""Sensor platform for Actron Air Neo integration."""

from homeassistant.components.sensor import (
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .device import ACZone, ZonePeripheral
from .entity import EntitySensor
from .switch import ZoneSwitch


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Actron Air Neo sensors."""
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    coordinator = data["coordinator"]
    serial_number = data["serial_number"]
    ac_unit = data["ac_unit"]

    # Obtain AC Units
    status = coordinator.data

    # Diagnostic sensor configurations
    diagnostic_configs = [
        (
            ac_unit,
            "clean_filter",
            ["Alerts"],
            "CleanFilter",
            None,
            False,
        ),
        (
            ac_unit,
            "defrost_mode",
            ["Alerts"],
            "Defrosting",
            None,
            False,
        ),
        (
            ac_unit,
            "compressor_chasing_temperature",
            ["LiveAircon"],
            "CompressorChasingTemperature",
            SensorDeviceClass.TEMPERATURE,
            True,
        ),
        (
            ac_unit,
            "compressor_live_temperature",
            ["LiveAircon"],
            "CompressorLiveTemperature",
            SensorDeviceClass.TEMPERATURE,
            True,
        ),
        (
            ac_unit,
            "compressor_mode",
            ["LiveAircon"],
            "CompressorMode",
            None,
            True,
        ),
        (
            ac_unit,
            "system_on",
            ["LiveAircon"],
            "SystemOn",
            None,
            False,
        ),
        (
            ac_unit,
            "compressor_speed",
            ["LiveAircon", "OutdoorUnit"],
            "CompSpeed",
            SensorDeviceClass.SPEED,
            True,
        ),
        (
            ac_unit,
            "compressor_power",
            ["LiveAircon", "OutdoorUnit"],
            "CompPower",
            SensorDeviceClass.POWER,
            True,
        ),
        (
            ac_unit,
            "outdoor_temperature",
            ["MasterInfo"],
            "LiveOutdoorTemp_oC",
            SensorDeviceClass.TEMPERATURE,
            False,
        ),
        (
            ac_unit,
            "humidity",
            ["MasterInfo"],
            "LiveHumidity_pc",
            SensorDeviceClass.HUMIDITY,
            False,
        ),
    ]

    # Create diagnostic sensors
    ac_unit_sensors = []
    for (
        ac_unit,
        translation_key,
        path,
        key,
        unit,
        diagnostic_sensor,
    ) in diagnostic_configs:
        ac_unit_sensors.append(
            EntitySensor(
                coordinator,
                ac_unit,
                translation_key,
                path,
                key,
                ac_unit.device_info,
                unit,
                diagnostic_sensor,
            )
        )

    # Fetch Zones
    zones = status.get("RemoteZoneInfo", [])

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
    peripherals = status.get("AirconSystem", {}).get("Peripherals", [])

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
    async_add_entities(ac_unit_sensors + zone_sensors)


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


class BaseZoneSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator, ac_zone, translation_key, state_key, unit_of_measurement=None
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._ac_zone = ac_zone
        self._attr_translation_key = translation_key
        self._zone_number = ac_zone.zone_number
        self._state_key = state_key
        self._unit_of_measurement = unit_of_measurement
        self._attr_unique_id = "_".join(
            [
                DOMAIN,
                self._ac_zone._serial,
                "sensor",
                translation_key,
                str(ac_zone.zone_number),
            ]
        )
        self._attr_device_info = self._ac_zone.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        zones = self.coordinator.data.get("RemoteZoneInfo", [])
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
        super().__init__(coordinator, ac_zone, "damper_position", "ZonePosition", "%")


class ZoneTemperatureSensor(BaseZoneSensor):
    """Temperature sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, ac_zone) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, ac_zone, "temperature", "LiveTemp_oC", "°C")


class ZoneHumiditySensor(BaseZoneSensor):
    """Humidity sensor for Actron Air Neo zone."""

    def __init__(self, coordinator, ac_zone) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, ac_zone, "humidity", "LiveHumidity_pc", "%")


class BasePeripheralSensor(CoordinatorEntity, Entity):
    """Base class for Actron Air Neo sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        zone_peripheral,
        translation_key,
        path,
        key,
        unit_of_measurement=None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._zone_peripheral = zone_peripheral
        self._attr_translation_key = translation_key
        self._path = path if isinstance(path, list) else [path]
        self._key = key
        self._unit_of_measurement = unit_of_measurement
        self._attr_unique_id = "_".join(
            [
                DOMAIN,
                "sensor",
                translation_key,
                zone_peripheral._serial,
            ]
        )

    @property
    def device_info(self):
        """Return the device information."""
        return self._zone_peripheral.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        # Look up the state using the state key in the data.
        data_source = self.coordinator.data.get("AirconSystem", {}).get(
            "Peripherals", []
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
            "battery",
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
            "temperature",
            ["SensorInputs", "SHTC1"],
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
            "humidity",
            ["SensorInputs", "SHTC1"],
            "RelativeHumidity_pc",
            "%",
        )
