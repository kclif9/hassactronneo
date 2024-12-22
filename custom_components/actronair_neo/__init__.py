from datetime import timedelta
import logging
import re

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
        "entity_prefix": f"actronair_neo_{serial_number}",
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
                events = await api.get_ac_events(serial_number, event_type="latest")

                for event in events["events"]:
                    event_data = event["data"]
                    event_id = event["id"]
                    event_type = event["type"]

                    if event_type == "full-status-broadcast":
                        _LOGGER.debug(
                            "Received full-status-broadcast, updating full state."
                        )
                        local_state["full_update"] = event_data
                        local_state["last_event_id"] = event_id
                        # Save the new state to the coordinator
                        coordinator.async_set_updated_data(local_state["full_update"])
                        _LOGGER.debug(
                            f"Coordinator data after update: {coordinator.data}"
                        )
                        return local_state["full_update"]

            # Fetch incremental updates since the last event
            _LOGGER.debug("Fetching incremental updates.")
            events = await api.get_ac_events(
                serial_number, event_type="newer", event_id=local_state["last_event_id"]
            )

            for event in reversed(events["events"]):
                event_data = event["data"]
                event_id = event["id"]
                event_type = event["type"]

                if event_type == "full-status-broadcast":
                    _LOGGER.debug(
                        "Received full-status-broadcast, updating full state."
                    )
                    local_state["full_update"] = event_data
                    local_state["last_event_id"] = event_id
                    coordinator.async_set_updated_data(local_state["full_update"])
                    _LOGGER.debug(f"Coordinator data after update: {coordinator.data}")
                    return local_state["full_update"]

                if event_type == "status-change-broadcast":
                    _LOGGER.debug("Merging status-change-broadcast into full state.")
                    # Merge 'data' from incremental updates into the current state
                    merge_incremental_update(local_state["full_update"], event["data"])

                # Update the most recent event ID
                local_state["last_event_id"] = event_id

            # After processing all events, update the coordinator
            if local_state["full_update"]:
                coordinator.async_set_updated_data(local_state["full_update"])
                _LOGGER.debug(f"Coordinator data after update: {coordinator.data}")
                _LOGGER.debug("Coordinator data updated with the latest state.")
            return local_state["full_update"]

        except Exception as e:
            _LOGGER.error("Error fetching updates: %s", e)
            return local_state["full_update"]

    def merge_incremental_update(full_state, incremental_data):
        """Merge incremental updates into the full state."""
        for key, value in incremental_data.items():
            # Skip metadata keys
            if key.startswith("@"):
                continue

            # Log the current state of the specific key before merging
            if key in full_state:
                _LOGGER.debug(
                    f"Before merging: key='{key}', current_value='{full_state[key]}', new_value='{value}'"
                )
            else:
                _LOGGER.debug(
                    f"Before merging: key='{key}' does not exist in full_state, new_value='{value}'"
                )

            # Handle array-like paths
            match = re.match(r"(.+)\[(\d+)\]$", key)
            if match:
                array_key, index = match.groups()
                index = int(index)

                if array_key not in full_state:
                    full_state[array_key] = []

                # Extend the array if the index is out of range
                while len(full_state[array_key]) <= index:
                    full_state[array_key].append(False)

                # Update the specific index in the array
                full_state[array_key][index] = value

                # Log the updated state of the array
                _LOGGER.debug(
                    f"After merging: key='{array_key}', updated_value='{full_state[array_key]}'"
                )
            else:
                # Replace or add the value to the dictionary
                full_state[key] = value

                # Log the updated state of the key
                _LOGGER.debug(
                    f"After merging: key='{key}', updated_value='{full_state[key]}'"
                )

    # Set up data update coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Actron Neo Status",
        update_interval=timedelta(
            seconds=10
        ),  # Frequent polling for incremental updates
        update_method=fetch_and_merge_status,
    )

    await coordinator.async_config_entry_first_refresh()

    system = await api.get_ac_systems()
    ac_unit = ACUnit(serial_number, system, coordinator.data)

    hass.data[DOMAIN][entry.entry_id]["coordinator"] = coordinator
    hass.data[DOMAIN][entry.entry_id]["ac_unit"] = ac_unit

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
