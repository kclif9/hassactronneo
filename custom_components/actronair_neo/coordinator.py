"""Coordinator for Actron Air Neo integration."""

from datetime import timedelta, datetime
import logging
from typing import Any

from actron_neo_api import ActronNeoAPI, ActronNeoAPIError, ActronNeoAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import _LOGGER, STALE_DEVICE_TIMEOUT

type ActronConfigEntry = ConfigEntry[ActronNeoDataUpdateCoordinator]

SCAN_INTERVAL = timedelta(seconds=30)
PARALLEL_UPDATES = 0


class ActronNeoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Custom coordinator for Actron Air Neo integration."""

    def __init__(
        self, hass: HomeAssistant, entry: ActronConfigEntry, pairing_token: str
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Actron Neo Status",
            update_interval=SCAN_INTERVAL,
        )
        self.api = ActronNeoAPI(pairing_token=pairing_token)
        self.entry = entry
        self.last_update_success = False
        self.last_seen = {}

    async def _async_setup(self) -> None:
        """Perform initial setup, including refreshing the token."""
        try:
            await self.api.refresh_token()
        except ActronNeoAuthError:
            _LOGGER.error("Authentication error while setting up Actron Neo integration")
            raise
        except ActronNeoAPIError as err:
            _LOGGER.error("API error while setting up Actron Neo integration: %s", err)
            raise

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch updates and merge incremental changes into the full state."""
        try:
            await self.api.update_status()
            self.last_update_success = True

            current_time = dt_util.utcnow()
            for system_id in self.api.status:
                self.last_seen[system_id] = current_time

            return self.api.status
        except ActronNeoAuthError:
            self.last_update_success = False
            _LOGGER.warning(
                "Authentication error while updating Actron Neo data. "
                "Device may be unavailable"
            )
            raise UpdateFailed("Authentication error")
        except ActronNeoAPIError as err:
            self.last_update_success = False
            _LOGGER.warning(
                "Error communicating with Actron Neo API: %s. "
                "Device may be unavailable", err
            )
            raise UpdateFailed(f"Error communicating with API: {err}")

    def is_device_stale(self, system_id: str) -> bool:
        """Check if a device is stale (not seen for a while)."""
        if system_id not in self.last_seen:
            return True

        last_seen_time = self.last_seen[system_id]
        current_time = dt_util.utcnow()

        # Check if device hasn't been seen for longer than the stale timeout
        return (current_time - last_seen_time) > STALE_DEVICE_TIMEOUT
