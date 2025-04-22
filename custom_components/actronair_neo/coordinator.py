"""Coordinator for Actron Air Neo integration."""

from datetime import timedelta
import logging
from typing import Any

from actron_neo_api import ActronNeoAPI, ActronNeoAPIError, ActronNeoAuthError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

type ActronConfigEntry = ConfigEntry[ActronNeoDataUpdateCoordinator]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)


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
