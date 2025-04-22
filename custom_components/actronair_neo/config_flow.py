"""Setup config flow for Actron Neo integration."""

import logging
from typing import Any

from actron_neo_api import ActronNeoAPI, ActronNeoAPIError, ActronNeoAuthError
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow, OptionsFlowWithConfigEntry
from homeassistant.const import CONF_API_TOKEN, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.helpers import instance_id

from .const import _LOGGER, DOMAIN, ERROR_API_ERROR, ERROR_INVALID_AUTH

ACTRON_AIR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ActronNeoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Actron Air Neo."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ActronNeoOptionsFlow(config_entry)

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.reauth_entry = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]
            _LOGGER.debug("Connecting to Actron Neo API")
            try:
                api = ActronNeoAPI(username, password)
            except ActronNeoAuthError:
                errors["base"] = ERROR_INVALID_AUTH
                return self.async_show_form(
                    step_id="user",
                    data_schema=ACTRON_AIR_SCHEMA,
                    errors=errors,
                )

            assert api is not None

            try:
                instance_uuid = await instance_id.async_get(self.hass)
                await api.request_pairing_token("HomeAssistant", instance_uuid)
                await api.refresh_token()
            except ActronNeoAPIError:
                errors["base"] = ERROR_API_ERROR
                return self.async_show_form(
                    step_id="user",
                    data_schema=ACTRON_AIR_SCHEMA,
                    errors=errors,
                )

            user_data = await api.get_user()
            await self.async_set_unique_id(user_data["id"])

            if self.reauth_entry:
                return self.async_update_reload_and_abort(
                    self.reauth_entry,
                    data={
                        CONF_API_TOKEN: api.pairing_token,
                    },
                    reason="reauth_successful",
                )

            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=username,
                data={
                    CONF_API_TOKEN: api.pairing_token,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=ACTRON_AIR_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, user_input=None):
        """Handle reauthorization request."""
        self.reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Handle reauthorization confirmation."""
        errors = {}

        if user_input:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            try:
                api = ActronNeoAPI(username, password)
                instance_uuid = await instance_id.async_get(self.hass)
                await api.request_pairing_token("HomeAssistant", instance_uuid)
                await api.refresh_token()

                return self.async_update_reload_and_abort(
                    self.reauth_entry,
                    data={
                        CONF_API_TOKEN: api.pairing_token,
                    },
                    reason="reauth_successful",
                )
            except ActronNeoAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except ActronNeoAPIError:
                errors["base"] = ERROR_API_ERROR

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=ACTRON_AIR_SCHEMA,
            errors=errors,
            description_placeholders={"account": self.reauth_entry.title},
        )


class ActronNeoOptionsFlow(OptionsFlowWithConfigEntry):
    """Handle Actron Neo options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return self.async_abort(reason="not_supported")
