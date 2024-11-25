import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .api import ActronNeoAPI

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Actron Neo integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = ActronNeoAPI(
        username=entry.data["username"],
        password=entry.data["password"]
    )

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Actron Neo Status",
        update_interval=timedelta(seconds=30),  # Fetch data every 30 seconds
        update_method=lambda: api.get_ac_status(entry.data["serial_number"]),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator
    }

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
