"""Climate platform for Actron Air Neo integration."""

from typing import Any

from actron_neo_api import ActronNeoAPI

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ActronConfigEntry
from .const import DOMAIN
from .coordinator import ActronNeoDataUpdateCoordinator

DEFAULT_TEMP_MIN = 16.0
DEFAULT_TEMP_MAX = 32.0
FAN_MODE_MAPPING = {
    "auto": "AUTO",
    "low": "LOW",
    "medium": "MED",
    "high": "HIGH",
}
FAN_MODE_MAPPING_REVERSE = {v: k for k, v in FAN_MODE_MAPPING.items()}
HVAC_MODE_MAPPING = {
    "COOL": HVACMode.COOL,
    "HEAT": HVACMode.HEAT,
    "FAN": HVACMode.FAN_ONLY,
    "AUTO": HVACMode.AUTO,
    "OFF": HVACMode.OFF,
}
HVAC_MODE_MAPPING_REVERSE = {v: k for k, v in HVAC_MODE_MAPPING.items()}
AC_UNIT_SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.FAN_MODE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)
AC_ZONE_SUPPORTED_FEATURES = (
    ClimateEntityFeature.TARGET_TEMPERATURE
    | ClimateEntityFeature.TURN_ON
    | ClimateEntityFeature.TURN_OFF
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ActronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Actron Air Neo climate entities."""
    # Get the API and coordinator from the integration
    coordinator = entry.runtime_data

    # Add system-wide climate entity
    entities: list[ClimateEntity] = []

    assert coordinator.systems is not None

    systems = coordinator.systems["_embedded"]["ac-system"]
    for system in systems:
        description = system["description"]
        serial_number = system["serial"]
        entities.append(ActronSystemClimate(coordinator, serial_number, description))

        # Fetch Zones
        zones = coordinator.data[serial_number].get("RemoteZoneInfo", [])

        # Create zones & sensors
        for zone_number, zone in enumerate(zones, start=0):
            if zone["NV_Exists"]:
                # Create zone device
                zone_name = zone["NV_Title"]
                entities.append(ActronZoneClimate(coordinator, serial_number, zone_name, zone_number))

    # Add all switches
    async_add_entities(entities)


class ActronSystemClimate(
    CoordinatorEntity[ActronNeoDataUpdateCoordinator], ClimateEntity
):
    """Representation of the Actron Air Neo system."""

    _attr_has_entity_name = True
    _attr_fan_modes = ["auto", "low", "medium", "high"]

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        description: str,
    ) -> None:
        """Initialize an Actron Air Neo unit."""
        super().__init__(coordinator)
        self._coordinator: ActronNeoDataUpdateCoordinator = coordinator
        self._api: ActronNeoAPI = coordinator.api
        self._serial_number: str = serial_number
        self._status = coordinator.data[self._serial_number]
        self._attr_unique_id: str = self._serial_number
        self._manufacturer: str = "Actron Air"
        self._name: str = description
        self._attr_name: str = "AC Unit"
        self._firmware_version: str = self._status.get("AirconSystem", {}).get(
            "MasterWCFirmwareVersion"
        )
        self._model_name: str = self._status.get("AirconSystem", {}).get(
            "MasterWCModel"
        )
        self.attr_device_info = {
            "identifiers": {(DOMAIN, self._serial_number)},
            "name": self._name,
            "manufacturer": self._manufacturer,
            "model": self._model_name,
            "sw_version": self._firmware_version,
            "serial_number": self._serial_number,
        }

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        system_state = self._status.get("UserAirconSettings", {}).get("isOn")
        if not system_state:
            return HVACMode.OFF

        hvac_mode = self._status.get("UserAirconSettings", {}).get("Mode")
        return HVAC_MODE_MAPPING.get(hvac_mode, HVACMode.OFF)

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return HVAC Modes."""
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO]

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode."""
        api_fan_mode = (
            self._status.get("UserAirconSettings", {}).get("FanMode").upper()
        )
        fan_mode_without_cont = api_fan_mode.split("+")[0]
        return FAN_MODE_MAPPING_REVERSE.get(fan_mode_without_cont, "AUTO")

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return list(FAN_MODE_MAPPING.keys())

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_humidity(self) -> float:
        """Return the current humidity."""
        return self._status.get("MasterInfo", {}).get("LiveHumidity_pc")

    @property
    def current_temperature(self) -> float:
        """Return the current temperature."""
        return self._status.get("MasterInfo", {}).get("LiveTemp_oC")

    @property
    def target_temperature(self) -> float:
        """Return the target temperature."""
        return self._status.get("UserAirconSettings", {}).get(
            "TemperatureSetpoint_Cool_oC"
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        return AC_UNIT_SUPPORTED_FEATURES

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature that can be set."""
        return (
            self._status.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Min", DEFAULT_TEMP_MIN)
        )

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature that can be set."""
        return (
            self._status.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Max", DEFAULT_TEMP_MAX)
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set a new fan mode."""
        api_fan_mode = FAN_MODE_MAPPING.get(fan_mode.lower())
        await self._api.set_fan_mode(self._serial_number, fan_mode=api_fan_mode)
        self._attr_fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        ac_mode = HVAC_MODE_MAPPING_REVERSE.get(hvac_mode)
        if not ac_mode:
            raise ValueError(f"Unsupported HVAC mode: {hvac_mode}")

        if hvac_mode == HVACMode.OFF:
            await self._api.set_system_mode(self._serial_number, is_on=False)
        else:
            await self._api.set_system_mode(
                self._serial_number, is_on=True, mode=ac_mode
            )

        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature."""
        temp = kwargs.get("temperature")
        hvac_mode = self.hvac_mode.lower()

        if hvac_mode == HVACMode.COOL:
            await self._api.set_temperature(
                self._serial_number,
                mode="COOL",
                temperature=temp,
            )
        elif hvac_mode == HVACMode.HEAT:
            await self._api.set_temperature(
                self._serial_number,
                mode="HEAT",
                temperature=temp,
            )
        elif hvac_mode == HVACMode.AUTO:
            await self._api.set_temperature(
                self._serial_number,
                mode="AUTO",
                temperature={"cool": temp, "heat": temp},
            )
        else:
            raise ValueError(f"Mode {hvac_mode} is invalid.")
        self._attr_target_temperature = temp
        self.async_write_ha_state()

    async def async_turn_on_continuous(self, continuous: bool) -> None:
        """Set the continuous mode."""
        await self._api.set_fan_mode(
            self._serial_number, fan_mode=self._attr_fan_mode, continuous=continuous
        )
        self.async_write_ha_state()


class ActronZoneClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a zone within the Actron Air system."""

    _attr_has_entity_name = True
    _attr_translation_key = "ac_zone"

    def __init__(
        self,
        coordinator: ActronNeoDataUpdateCoordinator,
        serial_number: str,
        zone_name: str,
        zone_number: int,
    ) -> None:
        """Initialize an Actron Air Neo unit."""
        super().__init__(coordinator)
        self._coordinator: ActronNeoDataUpdateCoordinator = coordinator
        self._api: ActronNeoAPI = coordinator.api
        self._serial_number: str = serial_number
        self._ac_status = coordinator.data[self._serial_number]
        self._zone_number = zone_number
        self._zone_name = zone_name
        self._attr_unique_id = "_".join(
            [
                self._serial_number,
                "zone",
                str(self._zone_number),
            ]
        )
        self.attr_device_info = {
            "identifiers": {(DOMAIN, f"zone_{self._zone_number}")},
            "name": self._zone_name,
            "manufacturer": "Actron Air",
            "model": "Zone",
            "suggested_area": self._zone_name,
        }

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        system_state = self._ac_status.get("UserAirconSettings", {}).get("isOn")
        if not system_state:
            return HVACMode.OFF

        enabled_zones = self._ac_status.get(
            "UserAirconSettings", {}).get("EnabledZones", [])
        if isinstance(enabled_zones, list):
            zone_state = enabled_zones[self._zone_number]
            if zone_state:
                hvac_mode = self._ac_status.get(
                    "UserAirconSettings", {}).get("Mode")
                return HVAC_MODE_MAPPING.get(hvac_mode, HVACMode.OFF)
        return HVACMode.OFF

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return HVAC Modes."""
        return [HVACMode.OFF, HVACMode.COOL, HVACMode.HEAT, HVACMode.AUTO]

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_humidity(self) -> float | None:
        """Return the current humidity."""
        zones = self._ac_status.get("RemoteZoneInfo", [])
        for zone_number, zone in enumerate(zones, start=0):
            if zone_number == self._zone_number:
                return zone.get("LiveHumidity_pc")
        return None

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        zones = self._ac_status.get("RemoteZoneInfo", [])
        for zone_number, zone in enumerate(zones, start=0):
            if zone_number == self._zone_number:
                return zone.get("LiveTemp_oC")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        zones = self._ac_status.get("RemoteZoneInfo", [])
        for zone_number, zone in enumerate(zones, start=0):
            if zone_number == self._zone_number:
                return zone.get("TemperatureSetpoint_Cool_oC")
        return None

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return supported features."""
        return AC_ZONE_SUPPORTED_FEATURES

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature that can be set."""
        min_setpoint = (
            self._ac_status.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Min")
        )
        target_setpoint = self._ac_status.get("UserAirconSettings", {}).get(
            "TemperatureSetpoint_Cool_oC"
        )
        temp_variance = self._ac_status.get("UserAirconSettings", {}).get(
            "ZoneTemperatureSetpointVariance_oC"
        )
        if min_setpoint > target_setpoint - temp_variance:
            return min_setpoint
        return target_setpoint - temp_variance

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature that can be set."""
        max_setpoint = (
            self._ac_status.get("NV_Limits", {})
            .get("UserSetpoint_oC", {})
            .get("setCool_Max")
        )
        target_setpoint = self._ac_status.get("UserAirconSettings", {}).get(
            "TemperatureSetpoint_Cool_oC"
        )
        temp_variance = self._ac_status.get("UserAirconSettings", {}).get(
            "ZoneTemperatureSetpointVariance_oC"
        )
        if max_setpoint < target_setpoint + temp_variance:
            return max_setpoint
        return target_setpoint + temp_variance

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self._api.set_zone(
                serial_number=self._serial_number,
                zone_number=self._zone_number,
                is_enabled=False,
            )
        else:
            await self._api.set_zone(
                serial_number=self._serial_number,
                zone_number=self._zone_number,
                is_enabled=True,
            )
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature."""
        temp = kwargs.get("temperature")
        hvac_mode = self.hvac_mode

        if temp is None or not (self.min_temp <= temp <= self.max_temp):
            raise ValueError(
                f"Temperature {temp} is out of range ({self.min_temp}-{self.max_temp})."
            )

        if hvac_mode == HVACMode.COOL:
            await self._api.set_temperature(
                self._serial_number,
                mode="COOL",
                temperature=temp,
                zone=self._zone_number,
            )
        elif hvac_mode == HVACMode.HEAT:
            await self._api.set_temperature(
                self._serial_number,
                mode="HEAT",
                temperature=temp,
                zone=self._zone_number,
            )
        elif hvac_mode == HVACMode.AUTO:
            await self._api.set_temperature(
                self._serial_number,
                mode="AUTO",
                temperature={"cool": temp, "heat": temp},
                zone=self._zone_number,
            )
        else:
            raise ValueError(f"Mode {hvac_mode} is invalid.")
        self._attr_target_temperature = temp
        self.async_write_ha_state()
