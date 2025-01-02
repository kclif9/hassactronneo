"""Setup config flow for Actron Neo integration."""

import logging
from actron_neo_api import ActronNeoAPI, ActronNeoAuthError, ActronNeoAPIError
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, ERROR_API_ERROR, ERROR_INVALID_AUTH, ERROR_NO_SYSTEMS_FOUND

_LOGGER = logging.getLogger(__name__)


class ActronNeoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Actron Air Neo."""

    VERSION = 3

    async def async_step_user(self, user_input=None) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            _LOGGER.debug("User input received: %s", user_input)
            try:
                if not user_input.get("username") or not user_input.get("password"):
                    errors["base"] = "invalid_input"
                    raise ValueError("Invalid username or password.")

                _LOGGER.debug("Connecting to Actron Neo API")
                api = ActronNeoAPI(
                    username=user_input["username"], password=user_input["password"]
                )
                await api.request_pairing_token("HomeAssistant", "ha-instance-id")
                await api.refresh_token()

                systems = await api.get_ac_systems()
                ac_systems = systems.get("_embedded", {}).get("ac-system", [])
                if not ac_systems:
                    raise ValueError("No AC systems found.")

                if len(ac_systems) > 1:
                    self.context["api"] = api
                    self.context["ac_systems"] = ac_systems
                    return self.async_show_form(
                        step_id="select_system",
                        data_schema=vol.Schema(
                            {
                                vol.Required("selected_system"): vol.In(
                                    {
                                        system["serial"]: system["description"]
                                        for system in ac_systems
                                    }
                                )
                            }
                        ),
                    )

                selected_system = ac_systems[0]
            except ActronNeoAuthError:
                errors["base"] = ERROR_INVALID_AUTH
            except ActronNeoAPIError:
                errors["base"] = ERROR_API_ERROR
            except ValueError:
                errors["base"] = ERROR_NO_SYSTEMS_FOUND
            else:
                serial_number = selected_system["serial"]
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=selected_system["description"],
                    data={
                        "pairing_token": api.pairing_token,
                        "serial_number": serial_number,
                    },
                )

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

    async def async_step_select_system(
        self, user_input=None
    ) -> config_entries.ConfigFlowResult:
        """Handle system selection step."""
        ac_systems = self.context["ac_systems"]
        selected_system = next(
            (
                system
                for system in ac_systems
                if system["serial"] == user_input["selected_system"]
            ),
            None,
        )
        if not selected_system:
            return self.async_abort(reason=ERROR_NO_SYSTEMS_FOUND)
        return self.async_create_entry(
            title=selected_system["description"],
            data={
                "pairing_token": self.context["api"].pairing_token,
                "serial_number": selected_system["serial"],
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return ActronNeoOptionsFlowHandler(config_entry)


class ActronNeoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for Actron Air Neo."""

    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        )
