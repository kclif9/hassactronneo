import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class ActronNeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Actron Neo."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Validate user input by attempting to connect to the API
                api = ActronNeoAPI(
                    username=user_input["username"],
                    password=user_input["password"]
                )
                await api.request_pairing_token("HomeAssistant", "ha-instance-id")

                # Save the config entry
                return self.async_create_entry(
                    title="Actron Neo",
                    data=user_input
                )

            except Exception as e:
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
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ActronNeoOptionsFlowHandler(config_entry)


class ActronNeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Actron Neo."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the Actron Neo options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Define options form here if needed
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
