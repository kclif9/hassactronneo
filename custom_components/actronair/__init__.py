"""The Actron Air integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import _LOGGER
from .coordinator import (
    ActronAirApiClient,
    ActronAirConfigEntry,
    ActronAirRuntimeData,
    ActronAirSystemCoordinator,
)

PLATFORM = [Platform.CLIMATE]


async def async_setup_entry(hass: HomeAssistant, entry: ActronAirConfigEntry) -> bool:
    """Set up Actron Air integration from a config entry."""

    api_client = ActronAirApiClient(hass, entry)
    await api_client.async_setup()

    system_coordinators: dict[str, ActronAirSystemCoordinator] = {}
    for system in api_client.systems:
        coordinator = ActronAirSystemCoordinator(hass, entry, api_client, system)
        _LOGGER.debug("Setting up coordinator for system: %s", system["serial"])
        await coordinator.async_config_entry_first_refresh()
        system_coordinators[system["serial"]] = coordinator

    entry.runtime_data = ActronAirRuntimeData(
        api_client=api_client,
        system_coordinators=system_coordinators,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORM)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ActronAirConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORM)
