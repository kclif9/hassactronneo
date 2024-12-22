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
    serial_number = entry.data.get("serial_number")

    if not access_token or not serial_number:
        _LOGGER.error("Missing access token or serial number in config entry.")
        return False

    api = ActronNeoAPI(access_token=access_token)

    # Initialize the data coordinator
    coordinator = ActronNeoDataUpdateCoordinator(hass, api, serial_number)
    await coordinator.async_config_entry_first_refresh()

    # Fetch system details and set up ACUnit
    system = await api.get_ac_systems()
    ac_unit = ACUnit(serial_number, system, coordinator.data)

    # Store objects in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "ac_unit": ac_unit,
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
