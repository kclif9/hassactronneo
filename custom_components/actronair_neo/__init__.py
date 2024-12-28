from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORMS
from .coordinator import ActronNeoDataUpdateCoordinator
from .device import ACUnit
from actron_neo_api import ActronNeoAPI
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Actron Air Neo integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    access_token = entry.data.get("access_token")
    pairing_token = entry.data.get("pairing_token")
    serial_number = entry.data.get("serial_number")

    if not access_token or not pairing_token or not serial_number:
        _LOGGER.error(
            "Missing access token, pairing token, or serial number in config entry."
        )
        return False

    api = ActronNeoAPI(access_token=access_token, pairing_token=pairing_token)

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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Handle migration of a config entry."""
    if config_entry.version == 1:
        new_data = {**config_entry.data}

        # Add default value for pairing_token if missing
        if "pairing_token" not in new_data:
            new_data["pairing_token"] = None
        hass.config_entries.async_update_entry(config_entry, data=new_data, version=2)

    return True
