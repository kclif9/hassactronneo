"""Actron Neo climate integration."""

from datetime import timedelta
import logging

from actron_neo_api import ActronNeoAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Actron Neo integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Retrieve stored access_token and serial_number from the config entry
    access_token = entry.data.get("access_token")
    serial_number = entry.data.get("serial_number")

    # Validate that the required information is present
    if not access_token or not serial_number:
        _LOGGER.error("Missing access token or serial number in config entry.")
        return False

    # Initialize the API client with the access_token
    api = ActronNeoAPI(access_token=access_token)

    # Store the API instance and serial number in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "serial_number": serial_number,
    }

    # Set up data update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Actron Neo Status",
        update_interval=timedelta(seconds=30),
        update_method=lambda: api.get_ac_status(serial_number),
    )

    # Perform the first data fetch
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)

    # Remove integration data if unloading was successful
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
