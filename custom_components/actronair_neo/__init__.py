"""The Actron Air Neo integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from actron_neo_api import ActronNeoAPI

from .const import DOMAIN, PLATFORMS
from .coordinator import ActronNeoDataUpdateCoordinator
from .device import ACUnit

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Actron Air Neo integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    pairing_token = entry.data.get("pairing_token")
    serial_number = entry.data.get("serial_number")

    if not pairing_token or not serial_number:
        _LOGGER.error("Missing either pairing token or serial number in config entry.")
        return False

    api = ActronNeoAPI(pairing_token=pairing_token)
    await api.refresh_token()

    # Initialize the data coordinator
    coordinator = ActronNeoDataUpdateCoordinator(hass, api, serial_number)
    await coordinator.async_config_entry_first_refresh()

    # Ensure coordinator data is not None
    if coordinator.data is None:
        _LOGGER.error("Failed to fetch initial data from the coordinator.")
        return False

    # Fetch system details and set up ACUnit
    system = await api.get_ac_systems()
    ac_unit = ACUnit(serial_number, system, coordinator.data)

    # Store objects in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "ac_unit": ac_unit,
        "serial_number": serial_number,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the Actron Air Neo integration."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle migration of a config entry."""
    if entry.version != 3:
        new_data = {**entry.data}

        if entry.version == 1:
            if "pairing_token" not in new_data:
                new_data["pairing_token"] = None
        if entry.version == 2:
            if "access_token" in new_data:
                new_data["access_token"] = None

        hass.config_entries.async_update_entry(entry, data=new_data, version=3)

    return True
