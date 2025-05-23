"""Constants used by Actron Air Neo integration."""

from datetime import timedelta
import logging

from homeassistant.const import Platform

logging.basicConfig(level=logging.DEBUG)
_LOGGER = logging.getLogger(__package__)
DOMAIN = "actronair_neo"
PLATFORM = [Platform.CLIMATE, Platform.COVER, Platform.SENSOR, Platform.SWITCH]

ERROR_API_ERROR = "api_error"
ERROR_INVALID_AUTH = "invalid_auth"
ERROR_NO_SYSTEMS_FOUND = "no_systems_found"
ERROR_UNKNOWN = "unknown_error"

STALE_DEVICE_TIMEOUT = timedelta(hours=24)
