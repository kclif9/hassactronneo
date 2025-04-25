"""Tests for the Actron Neo climate platform."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.components.climate import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant

from custom_components.actronair_neo.climate import (
    ActronSystemClimate,
    ActronZoneClimate,
    async_setup_entry,
    HVAC_MODE_MAPPING,
    FAN_MODE_MAPPING_REVERSE,
    FAN_MODE_MAPPING,
)
from custom_components.actronair_neo.const import DOMAIN


@pytest.fixture
def mock_coordinator():
    """Create mock coordinator with test data."""
    coordinator = Mock()
    coordinator.api = Mock()
    coordinator.api.systems = [
        {"description": "Living Room", "serial": "12345"},
        {"description": "Bedroom", "serial": "67890"},
    ]
    coordinator.api.set_fan_mode = AsyncMock()
    coordinator.api.set_system_mode = AsyncMock()
    coordinator.api.set_temperature = AsyncMock()
    coordinator.api.set_zone = AsyncMock()

    coordinator.data = {
        "12345": {
            "UserAirconSettings": {
                "isOn": True,
                "Mode": "COOL",
                "FanMode": "AUTO",
                "TemperatureSetpoint_Cool_oC": 22.0,
                "EnabledZones": [True, False, True],
                "ZoneTemperatureSetpointVariance_oC": 2.0,
            },
            "MasterInfo": {
                "LiveTemp_oC": 24.5,
                "LiveHumidity_pc": 45,
            },
            "NV_Limits": {
                "UserSetpoint_oC": {
                    "setCool_Min": 16.0,
                    "setCool_Max": 32.0,
                }
            },
            "RemoteZoneInfo": [
                {
                    "NV_Exists": True,
                    "NV_Title": "Zone 1",
                    "ZonePosition": 50,
                    "LiveTemp_oC": 23.0,
                    "LiveHumidity_pc": 48,
                    "TemperatureSetpoint_Cool_oC": 22.5,
                },
                {
                    "NV_Exists": True,
                    "NV_Title": "Zone 2",
                    "ZonePosition": 0,
                    "LiveTemp_oC": 25.0,
                    "LiveHumidity_pc": 50,
                    "TemperatureSetpoint_Cool_oC": 23.0,
                },
                {
                    "NV_Exists": True,
                    "NV_Title": "Zone 3",
                    "ZonePosition": 75,
                    "LiveTemp_oC": 22.0,
                    "LiveHumidity_pc": 40,
                    "TemperatureSetpoint_Cool_oC": 21.5,
                },
            ],
            "AirconSystem": {
                "MasterWCModel": "Neo System",
                "MasterWCFirmwareVersion": "1.2.3",
            },
        }
    }
    coordinator.last_update_success = True
    return coordinator


async def test_async_setup_entry(hass: HomeAssistant, mock_coordinator):
    """Test the climate platform setup."""
    entry = Mock()
    entry.runtime_data = mock_coordinator

    entities = []

    async def async_add_entities_mock(new_entities):
        nonlocal entities
        entities.extend(new_entities)

    await async_setup_entry(hass, entry, async_add_entities_mock)

    # Should create 1 system entity and 3 zone entities (for 3 zones)
    assert len(entities) == 4
    assert isinstance(entities[0], ActronSystemClimate)
    assert isinstance(entities[1], ActronZoneClimate)
    assert isinstance(entities[2], ActronZoneClimate)
    assert isinstance(entities[3], ActronZoneClimate)


def test_system_climate_init(mock_coordinator):
    """Test system climate entity initialization."""
    climate = ActronSystemClimate(mock_coordinator, "12345", "Living Room")

    assert climate._serial_number == "12345"
    assert climate.temperature_unit == UnitOfTemperature.CELSIUS
    assert climate.supported_features == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    assert climate.fan_modes == ["auto", "low", "medium", "high"]
    assert climate.unique_id == "12345"
    assert climate.device_info == {
        "identifiers": {(DOMAIN, "12345")},
        "name": "Living Room",
        "manufacturer": "Actron Air",
        "model": "Neo System",
        "sw_version": "1.2.3",
        "serial_number": "12345",
    }


def test_system_climate_properties(mock_coordinator):
    """Test system climate entity properties."""
    climate = ActronSystemClimate(mock_coordinator, "12345", "Living Room")

    assert climate.hvac_mode == HVACMode.COOL
    assert climate.hvac_modes == [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO]
    assert climate.fan_mode == "auto"
    assert climate.current_humidity == 45
    assert climate.current_temperature == 24.5
    assert climate.target_temperature == 22.0
    assert climate.min_temp == 16.0
    assert climate.max_temp == 32.0


async def test_system_climate_set_fan_mode(mock_coordinator):
    """Test setting fan mode."""
    climate = ActronSystemClimate(mock_coordinator, "12345", "Living Room")

    await climate.async_set_fan_mode("medium")

    mock_coordinator.api.set_fan_mode.assert_called_once_with("12345", fan_mode="MED")
    assert climate._status["UserAirconSettings"]["FanMode"] == "MED"


async def test_system_climate_set_hvac_mode(mock_coordinator):
    """Test setting HVAC mode."""
    climate = ActronSystemClimate(mock_coordinator, "12345", "Living Room")

    # Test turning off
    await climate.async_set_hvac_mode(HVACMode.OFF)
    mock_coordinator.api.set_system_mode.assert_called_once_with("12345", is_on=False)

    mock_coordinator.api.set_system_mode.reset_mock()

    # Test setting to cool
    await climate.async_set_hvac_mode(HVACMode.COOL)
    mock_coordinator.api.set_system_mode.assert_called_once_with("12345", is_on=True, mode="COOL")


async def test_system_climate_set_temperature(mock_coordinator):
    """Test setting temperature."""
    climate = ActronSystemClimate(mock_coordinator, "12345", "Living Room")
    climate._status["UserAirconSettings"]["Mode"] = "COOL"

    await climate.async_set_temperature(temperature=23.0)

    mock_coordinator.api.set_temperature.assert_called_once_with(
        "12345", mode="COOL", temperature=23.0
    )
    assert climate._status["MasterInfo"]["LiveTemp_oC"] == 23.0


def test_zone_climate_init(mock_coordinator):
    """Test zone climate entity initialization."""
    climate = ActronZoneClimate(mock_coordinator, "12345", "Zone 1", 0)

    assert climate._serial_number == "12345"
    assert climate._zone_number == 0
    assert climate.temperature_unit == UnitOfTemperature.CELSIUS
    assert climate.supported_features == (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    assert climate.unique_id == "12345_zone_0"
    assert climate.device_info == {
        "identifiers": {(DOMAIN, "12345_zone_0")},
        "name": "Zone 1",
        "manufacturer": "Actron Air",
        "model": "Zone",
        "suggested_area": "Zone 1",
    }


def test_zone_climate_properties(mock_coordinator):
    """Test zone climate entity properties."""
    climate = ActronZoneClimate(mock_coordinator, "12345", "Zone 1", 0)

    assert climate.hvac_mode == HVACMode.COOL  # Zone 0 is enabled
    assert climate.hvac_modes == [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO]
    assert climate.current_humidity == 48
    assert climate.current_temperature == 23.0
    assert climate.target_temperature == 22.5
    assert climate.min_temp == 20.0  # System setpoint (22) - variance (2)
    assert climate.max_temp == 24.0  # System setpoint (22) + variance (2)

    # Test for disabled zone
    climate2 = ActronZoneClimate(mock_coordinator, "12345", "Zone 2", 1)
    assert climate2.hvac_mode == HVACMode.OFF  # Zone 1 is disabled


async def test_zone_climate_set_hvac_mode(mock_coordinator):
    """Test setting HVAC mode for a zone."""
    climate = ActronZoneClimate(mock_coordinator, "12345", "Zone 1", 0)

    # Test turning off
    await climate.async_set_hvac_mode(HVACMode.OFF)
    mock_coordinator.api.set_zone.assert_called_once_with(
        serial_number="12345", zone_number=0, is_enabled=False
    )

    mock_coordinator.api.set_zone.reset_mock()

    # Test turning on
    await climate.async_set_hvac_mode(HVACMode.COOL)
    mock_coordinator.api.set_zone.assert_called_once_with(
        serial_number="12345", zone_number=0, is_enabled=True
    )


async def test_zone_climate_set_temperature(mock_coordinator):
    """Test setting temperature for a zone."""
    climate = ActronZoneClimate(mock_coordinator, "12345", "Zone 1", 0)

    await climate.async_set_temperature(temperature=23.0)

    mock_coordinator.api.set_temperature.assert_called_once_with(
        serial_number="12345", mode="COOL", temperature=23.0, zone=0
    )
    assert climate._ac_status["RemoteZoneInfo"][0]["LiveTemp_oC"] == 23.0
