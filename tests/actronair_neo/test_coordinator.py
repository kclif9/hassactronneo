"""Tests for the Actron Neo coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from actron_neo_api import ActronNeoAPIError, ActronNeoAuthError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util.dt import utcnow

from custom_components.actronair_neo.coordinator import (
    ActronNeoDataUpdateCoordinator,
    SCAN_INTERVAL,
)

from .const import DOMAIN


@pytest.fixture
def mock_actron_api():
    """Fixture to mock the ActronNeoAPI."""
    with patch("custom_components.actronair_neo.coordinator.ActronNeoAPI") as mock_api:
        mock_api_instance = mock_api.return_value
        mock_api_instance.status = {"12345": {"system_data": "test"}}
        mock_api_instance.update_status = AsyncMock()
        mock_api_instance.refresh_token = AsyncMock()
        yield mock_api_instance


async def test_coordinator_init(hass: HomeAssistant, mock_actron_api):
    """Test the coordinator initialization."""
    entry = Mock()
    entry.entry_id = "test_entry_id"

    coordinator = ActronNeoDataUpdateCoordinator(hass, entry, "test_pairing_token")

    assert coordinator.name == "Actron Neo Status"
    assert coordinator.update_interval == SCAN_INTERVAL
    assert coordinator.api.pairing_token == "test_pairing_token"
    assert coordinator.entry == entry
    assert coordinator.last_update_success is False


async def test_coordinator_setup(hass: HomeAssistant, mock_actron_api):
    """Test the coordinator setup process."""
    entry = Mock()
    entry.entry_id = "test_entry_id"

    coordinator = ActronNeoDataUpdateCoordinator(hass, entry, "test_pairing_token")
    await coordinator._async_setup()

    # Verify the token was refreshed during setup
    mock_actron_api.refresh_token.assert_called_once()


async def test_coordinator_update_success(hass: HomeAssistant, mock_actron_api):
    """Test successful data update from the coordinator."""
    entry = Mock()
    entry.entry_id = "test_entry_id"

    coordinator = ActronNeoDataUpdateCoordinator(hass, entry, "test_pairing_token")
    result = await coordinator._async_update_data()

    # Verify the update_status was called
    mock_actron_api.update_status.assert_called_once()

    # Verify the returned data
    assert result == {"12345": {"system_data": "test"}}
    assert coordinator.last_update_success is True


async def test_coordinator_update_auth_error(hass: HomeAssistant, mock_actron_api):
    """Test coordinator update with authentication error."""
    mock_actron_api.update_status.side_effect = ActronNeoAuthError

    entry = Mock()
    entry.entry_id = "test_entry_id"

    coordinator = ActronNeoDataUpdateCoordinator(hass, entry, "test_pairing_token")

    with pytest.raises(UpdateFailed, match="Authentication error"):
        await coordinator._async_update_data()

    assert coordinator.last_update_success is False


async def test_coordinator_update_api_error(hass: HomeAssistant, mock_actron_api):
    """Test coordinator update with API error."""
    mock_actron_api.update_status.side_effect = ActronNeoAPIError("API Error")

    entry = Mock()
    entry.entry_id = "test_entry_id"

    coordinator = ActronNeoDataUpdateCoordinator(hass, entry, "test_pairing_token")

    with pytest.raises(UpdateFailed, match="Error communicating with API: API Error"):
        await coordinator._async_update_data()

    assert coordinator.last_update_success is False
