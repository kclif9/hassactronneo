"""Constants used by Actron Air integration."""

from datetime import timedelta
import logging

from homeassistant.const import Platform

_LOGGER = logging.getLogger(__package__)
DOMAIN = "actron_air"
PLATFORM = [Platform.CLIMATE, Platform.COVER, Platform.SENSOR, Platform.SWITCH]
