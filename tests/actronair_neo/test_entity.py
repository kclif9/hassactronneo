"""Tests for the Actron Neo entities."""

from unittest.mock import Mock, patch

import pytest

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.actronair.entity import (
    EntitySensor,
    BaseZoneSensor,
    ZoneTemperatureSensor,
    ZoneHumiditySensor,
    BasePeripheralSensor,
    PeripheralTemperatureSensor,
)
from custom_components.actronair.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {
        "123456": {
            "RemoteZoneInfo": [
                {
                    "ZonePosition": 50,
                    "LiveTemp_oC": 22.5,
                    "LiveHumidity_pc": 45,
                },
                {
                    "ZonePosition": 75,
                    "LiveTemp_oC": 23.0,
                    "LiveHumidity_pc": 40,
                },
            ],
            "AirconSystem": {
                "Peripherals": [
                    {
                        "LogicalAddress": "LA001",
                        "SerialNumber": "SN001",
                        "RemainingBatteryCapacity_pc": 80,
                        "SensorInputs": {
                            "SHTC1": {
                                "Temperature_oC": 24.5,
                                "RelativeHumidity_pc": 42,
                            }
                        },
                    }
                ]
            },
            "SystemStatus": {
                "FanSpeed": "High",
            },
        }
    }
    coordinator.last_update_success = True
    return coordinator


def test_entity_sensor_init(mock_coordinator):
    """Test initialization of entity sensor."""
    sensor = EntitySensor(
        mock_coordinator,
        "123456",
        "fan_speed",
        "SystemStatus",
        "FanSpeed",
        is_diagnostic=True,
    )

    assert sensor._path == ["SystemStatus"]
    assert sensor._key == "FanSpeed"
    assert sensor._serial_number == "123456"
    assert sensor._is_diagnostic is True
    assert sensor._attr_translation_key == "fan_speed"
    assert sensor._attr_unique_id == "fan_speed"
    assert sensor._attr_device_info == {
        "identifiers": {(DOMAIN, "123456")},
    }


def test_entity_sensor_state(mock_coordinator):
    """Test state property of entity sensor."""
    sensor = EntitySensor(
        mock_coordinator,
        "123456",
        "fan_speed",
        "SystemStatus",
        "FanSpeed",
    )

    assert sensor.state == "High"


def test_entity_sensor_unavailable(mock_coordinator):
    """Test unavailable state of entity sensor."""
    mock_coordinator.last_update_success = False

    sensor = EntitySensor(
        mock_coordinator,
        "123456",
        "fan_speed",
        "SystemStatus",
        "FanSpeed",
    )

    assert sensor.available is False
    assert sensor.state is None


def test_entity_sensor_missing_data(mock_coordinator):
    """Test entity sensor with missing data."""
    # Change coordinator data to not include the key
    mock_coordinator.data = {"123456": {"SystemStatus": {}}}

    sensor = EntitySensor(
        mock_coordinator,
        "123456",
        "fan_speed",
        "SystemStatus",
        "FanSpeed",
    )

    assert sensor.state is None


def test_zone_temperature_sensor(mock_coordinator):
    """Test zone temperature sensor."""
    sensor = ZoneTemperatureSensor(
        mock_coordinator,
        "123456",
        {"ZonePosition": 50, "LiveTemp_oC": 22.5, "LiveHumidity_pc": 45},
        0,
    )

    assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor._attr_translation_key == "temperature"
    assert sensor._zone_number == 0
    assert sensor.state == 22.5


def test_zone_humidity_sensor(mock_coordinator):
    """Test zone humidity sensor."""
    sensor = ZoneHumiditySensor(
        mock_coordinator,
        "123456",
        {"ZonePosition": 50, "LiveTemp_oC": 22.5, "LiveHumidity_pc": 45},
        0,
    )

    assert sensor._attr_device_class == SensorDeviceClass.HUMIDITY
    assert sensor._attr_unit_of_measurement == PERCENTAGE
    assert sensor._attr_translation_key == "humidity"
    assert sensor._zone_number == 0
    assert sensor.state == 45


def test_peripheral_temperature_sensor(mock_coordinator):
    """Test peripheral temperature sensor."""
    peripheral = {
        "LogicalAddress": "LA001",
        "SerialNumber": "SN001",
        "RemainingBatteryCapacity_pc": 80,
        "SensorInputs": {
            "SHTC1": {
                "Temperature_oC": 24.5,
                "RelativeHumidity_pc": 42,
            }
        },
    }

    sensor = PeripheralTemperatureSensor(
        mock_coordinator,
        "123456",
        0,
        peripheral,
    )

    assert sensor._attr_device_class == SensorDeviceClass.TEMPERATURE
    assert sensor._attr_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert sensor._attr_translation_key == "temperature"
    assert sensor._serial_number == "SN001"
    assert sensor.state == 24.5


def test_peripheral_sensor_unavailable(mock_coordinator):
    """Test unavailable state of peripheral sensor."""
    mock_coordinator.last_update_success = False

    peripheral = {
        "LogicalAddress": "LA001",
        "SerialNumber": "SN001",
    }

    sensor = PeripheralTemperatureSensor(
        mock_coordinator,
        "123456",
        0,
        peripheral,
    )

    assert sensor.available is False
    assert sensor.state is None
