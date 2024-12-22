from datetime import timedelta
import logging
import re
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class ActronNeoDataUpdateCoordinator(DataUpdateCoordinator):
    """Custom coordinator for Actron Air Neo integration."""

    def __init__(self, hass, api, serial_number):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Actron Neo Status",
            update_interval=timedelta(seconds=10),
        )
        self.api = api
        self.serial_number = serial_number
        self.local_state = {"full_update": None, "last_event_id": None}

    async def _async_update_data(self):
        """Fetch updates and merge incremental changes into the full state."""
        try:
            # If no full update exists, fetch it
            if self.local_state["full_update"] is None:
                _LOGGER.debug("Fetching full-status-broadcast.")
                events = await self.api.get_ac_events(
                    self.serial_number, event_type="latest"
                )

                for event in events["events"]:
                    event_data = event["data"]
                    event_id = event["id"]
                    event_type = event["type"]

                    if event_type == "full-status-broadcast":
                        _LOGGER.debug(
                            "Received full-status-broadcast, updating full state."
                        )
                        self.local_state["full_update"] = event_data
                        self.local_state["last_event_id"] = event_id
                        self.async_set_updated_data(
                            self.local_state["full_update"])
                        return self.local_state["full_update"]

            # Fetch incremental updates since the last event
            _LOGGER.debug("Fetching incremental updates.")
            events = await self.api.get_ac_events(
                self.serial_number,
                event_type="newer",
                event_id=self.local_state["last_event_id"],
            )

            for event in reversed(events["events"]):
                event_data = event["data"]
                event_id = event["id"]
                event_type = event["type"]

                if event_type == "full-status-broadcast":
                    _LOGGER.debug(
                        "Received full-status-broadcast, updating full state."
                    )
                    self.local_state["full_update"] = event_data
                    self.local_state["last_event_id"] = event_id
                    self.async_set_updated_data(
                        self.local_state["full_update"])
                    return self.local_state["full_update"]

                if event_type == "status-change-broadcast":
                    _LOGGER.debug(
                        "Merging status-change-broadcast into full state.")
                    self._merge_incremental_update(
                        self.local_state["full_update"], event["data"]
                    )

                self.local_state["last_event_id"] = event_id

            if self.local_state["full_update"]:
                self.async_set_updated_data(self.local_state["full_update"])
                _LOGGER.debug(
                    "Coordinator data updated with the latest state.")
            return self.local_state["full_update"]

        except Exception as e:
            _LOGGER.error("Error fetching updates: %s", e)
            return self.local_state["full_update"]

    def _merge_incremental_update(self, full_state, incremental_data):
        """Merge incremental updates into the full state."""
        for key, value in incremental_data.items():
            if key.startswith("@"):
                continue

            match = re.match(r"(.+)\[(\d+)\]$", key)
            if match:
                array_key, index = match.groups()
                index = int(index)

                if array_key not in full_state:
                    full_state[array_key] = []

                while len(full_state[array_key]) <= index:
                    full_state[array_key].append(False)

                full_state[array_key][index] = value
            else:
                full_state[key] = value
