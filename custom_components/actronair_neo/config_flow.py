"""Setup config flow for Actron Neo integration."""

import logging

from actron_neo_api import ActronNeoAPI
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_LOGGER.debug("Config flow for Actron Air Neo loaded")


class ActronNeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Actron Air Neo."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate user input by attempting to connect to the API
                api = ActronNeoAPI(
                    username=user_input["username"], password=user_input["password"]
                )
                await api.request_pairing_token("HomeAssistant", "ha-instance-id")
                await api.request_bearer_token()

                # Step 2: Fetch AC systems
                systems = await api.get_ac_systems()
                if not systems or not systems.get("_embedded", {}).get("ac-system"):
                    raise ValueError("No AC systems found for the account.")

                # Extract the serial number from the first AC system
                ac_system = systems["_embedded"]["ac-system"][0]
                serial_number = ac_system["serial"]

                # Save the access_token and serial_number
                return self.async_create_entry(
                    title=ac_system.get("description", "Actron Neo"),
                    data={
                        "access_token": api.access_token,
                        "serial_number": serial_number,
                    },
                )

            except ActronNeoAPI.ConnectionError:
                errors["base"] = "cannot_connect"

        # Show the form with any errors
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ActronNeoOptionsFlowHandler(config_entry)


class ActronNeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Actron Neo."""

    def __init__(self, config_entry) -> None:
        """Initialise options flow handler."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Manage the Actron Neo options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Define options form here if needed
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
