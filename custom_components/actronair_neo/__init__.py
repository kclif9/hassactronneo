from datetime import timedelta
import logging

from actron_neo_api import ActronNeoAPI

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS
from .device import ACUnit

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

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "serial_number": serial_number,
    }

    # Initialize local state for full update and event tracking
    local_state = {
        "full_update": None,
        "last_event_id": None,  # Track the most recent event ID
    }

    async def fetch_and_merge_status():
        """Fetch updates and merge incremental changes into the full state."""
        try:
            # If no full update exists, fetch it
            if local_state["full_update"] is None:
                _LOGGER.debug("Fetching full-status-broadcast.")
                full_update = await api.get_ac_status(serial_number)
                local_state["full_update"] = full_update
                return full_update

            # Fetch incremental updates since the last event
            _LOGGER.debug("Fetching incremental updates.")
            events = await api.get_ac_events(
                serial_number, event_type="latest", event_id=local_state["last_event_id"]
            )

            for event in events["events"]:
                event_id = event["id"]
                event_type = event["type"]

                if event_type == "full-status-broadcast":
                    _LOGGER.debug("Received full-status-broadcast, updating full state.")
                    local_state["full_update"] = event["data"]
                elif event_type == "status-change-broadcast":
                    _LOGGER.debug("Merging status-change-broadcast into full state.")
                    merge_incremental_update(local_state["full_update"], event["data"])

                # Update the most recent event ID
                local_state["last_event_id"] = event_id

            return local_state["full_update"]

        except Exception as e:
            _LOGGER.error("Error fetching updates: %s", e)
            return local_state["full_update"]

    def merge_incremental_update(full_state, incremental_data):
        """Merge incremental updates into the full state."""
        for key, value in incremental_data.items():
            if isinstance(value, dict) and key in full_state:
                merge_incremental_update(full_state[key], value)
            else:
                full_state[key] = value

    # Set up data update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Actron Neo Status",
        update_interval=timedelta(seconds=10),  # Frequent polling for incremental updates
        update_method=fetch_and_merge_status,
    )

    await coordinator.async_config_entry_first_refresh()

    system = await api.get_ac_systems()
    ac_unit = ACUnit(serial_number, system, coordinator.data)

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["ac_unit"] = ac_unit

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
