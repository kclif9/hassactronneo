"""The Actron Air integration."""

from actron_neo_api import ActronAirAPI, ActronAirAPIError, ActronAirAuthError
from actron_neo_api.models.system import ActronAirSystemInfo

from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import _LOGGER, DOMAIN
from .coordinator import (
    ActronAirConfigEntry,
    ActronAirRuntimeData,
    ActronAirSystemCoordinator,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.COVER, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ActronAirConfigEntry) -> bool:
    """Set up Actron Air integration from a config entry."""

    api = ActronAirAPI(refresh_token=entry.data[CONF_API_TOKEN])
    systems: list[ActronAirSystemInfo] = []

    try:
        systems = await api.get_ac_systems()
        await api.update_status()
    except ActronAirAuthError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="auth_error",
        ) from err
    except ActronAirAPIError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="setup_connection_error",
        ) from err

    serial_numbers = [system.serial for system in systems if system.serial]
    push_updates_enabled = False
    if serial_numbers:
        push_updates_enabled = await api.start_push(serial_numbers)
        if push_updates_enabled:
            _LOGGER.debug("Realtime push updates enabled for %s systems", len(serial_numbers))
        else:
            _LOGGER.info("Realtime push unavailable, using polling fallback")

    system_coordinators: dict[str, ActronAirSystemCoordinator] = {}
    for system in systems:
        if api.state_manager.get_status(system.serial) is None:
            await api.update_status(system.serial)

        coordinator = ActronAirSystemCoordinator(
            hass,
            entry,
            api,
            system,
            push_updates_enabled=push_updates_enabled,
        )
        _LOGGER.debug("Setting up coordinator for system: %s", system.serial)
        if push_updates_enabled:
            api.subscribe_system_updates(system.serial, coordinator.handle_push_update)
        system_coordinators[system.serial] = coordinator

    entry.runtime_data = ActronAirRuntimeData(
        api=api,
        system_coordinators=system_coordinators,
        push_updates_enabled=push_updates_enabled,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ActronAirConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    try:
        await entry.runtime_data.api.stop_push()
    except Exception:
        _LOGGER.warning("Failed to stop realtime push during unload", exc_info=True)

    return unload_ok
