"""The Actron Air integration."""

from actron_neo_api import ActronAirAPI, ActronAirAPIError, ActronAirAuthError
from actron_neo_api.models.system import ActronAirSystemInfo

from homeassistant.const import CONF_API_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import entity_registry as er

from .const import _LOGGER, DOMAIN
from .coordinator import (
    ActronAirConfigEntry,
    ActronAirRuntimeData,
    ActronAirSystemCoordinator,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.CLIMATE, Platform.COVER, Platform.SENSOR, Platform.SWITCH]

# Sensors whose unique_id was a bare translation_key (no serial prefix).
# These need to be prefixed with the system serial number.
_SENSOR_UID_MIGRATE = {
    "compressor_chasing_temperature",
    "compressor_live_temperature",
    "compressor_mode",
    "compressor_speed",
    "compressor_power",
    "outdoor_temperature",
}

# Sensors that moved from the sensor platform to binary_sensor.
# Old unique_id was a bare translation_key; new unique_id is {serial}_{key}.
_SENSOR_TO_BINARY_SENSOR = {"clean_filter", "defrost_mode"}

# Peripheral sensor key renames (old suffix → new suffix).
_PERIPHERAL_KEY_RENAMES = {
    "battery": "peripheral_battery",
    "temperature": "peripheral_temperature",
    "humidity": "peripheral_humidity",
}


async def _async_migrate_entities(
    hass: HomeAssistant,
    entry: ActronAirConfigEntry,
    serials: set[str],
) -> None:
    """Migrate entity unique IDs from pre-0.11 format.

    Handles:
    - Main sensor unique_id: bare key → {serial}_{key}
    - clean_filter / defrost_mode: sensor platform → binary_sensor platform
    - Cover unique_id: *_position → *_zone_position
    - Peripheral sensor key renames: {periph_serial}_{old} → {periph_serial}_{new}
    """
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    if not entries:
        return

    # For main sensors that had no serial prefix, we can only safely migrate
    # when there is exactly one system (multi-system was already broken).
    single_serial = next(iter(serials)) if len(serials) == 1 else None

    for entity_entry in entries:
        new_uid: str | None = None

        if entity_entry.domain == "sensor":
            uid = entity_entry.unique_id

            # Main sensors → prefix with serial
            if uid in _SENSOR_UID_MIGRATE and single_serial:
                new_uid = f"{single_serial}_{uid}"

            # Sensors migrated to binary_sensor: remove so the new platform
            # can recreate them.
            elif uid in _SENSOR_TO_BINARY_SENSOR:
                _LOGGER.info(
                    "Removing %s (migrated to binary_sensor platform)",
                    entity_entry.entity_id,
                )
                registry.async_remove(entity_entry.entity_id)
                continue

            # Peripheral key renames: {periph_serial}_{old} → {periph_serial}_{new}
            elif "_zone_" not in uid:
                for old_suffix, new_suffix in _PERIPHERAL_KEY_RENAMES.items():
                    if uid.endswith(f"_{old_suffix}"):
                        prefix = uid[: -(len(old_suffix) + 1)]
                        if prefix and prefix not in serials:
                            new_uid = f"{prefix}_{new_suffix}"
                        break

        elif entity_entry.domain == "cover":
            # Cover: {serial}_zone_{id}_position → {serial}_zone_{id}_zone_position
            if (
                entity_entry.unique_id.endswith("_position")
                and "_zone_" in entity_entry.unique_id
            ):
                new_uid = entity_entry.unique_id.replace(
                    "_position", "_zone_position"
                )

        if new_uid and new_uid != entity_entry.unique_id:
            _LOGGER.info(
                "Migrating %s unique_id: %s → %s",
                entity_entry.entity_id,
                entity_entry.unique_id,
                new_uid,
            )
            registry.async_update_entity(
                entity_entry.entity_id, new_unique_id=new_uid
            )


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

    system_coordinators: dict[str, ActronAirSystemCoordinator] = {}
    for system in systems:
        coordinator = ActronAirSystemCoordinator(hass, entry, api, system)
        _LOGGER.debug("Setting up coordinator for system: %s", system.serial)
        await coordinator.async_config_entry_first_refresh()
        system_coordinators[system.serial] = coordinator

    entry.runtime_data = ActronAirRuntimeData(
        api=api,
        system_coordinators=system_coordinators,
    )

    await _async_migrate_entities(
        hass, entry, {s.serial for s in systems}
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ActronAirConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
