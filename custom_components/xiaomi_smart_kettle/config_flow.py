from __future__ import annotations

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.data_entry_flow import FlowResult
from miio import MiotDevice
from miio.exceptions import DeviceException
import voluptuous as vol

from .const import CONF_TOKEN, DOMAIN, MODEL


class XiaomiSmartKettleConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN].strip()
            try:
                info = await self.hass.async_add_executor_job(
                    MiotDevice(host, token).info
                )
                model = getattr(info, "model", None)
                if model != MODEL:
                    errors["base"] = "unsupported_model"
                else:
                    mac = (
                        getattr(info, "mac_address", None)
                        or getattr(info, "mac", None)
                        or host
                    )
                    unique_id = str(mac).lower()
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: host, CONF_TOKEN: token}
                    )
                    return self.async_create_entry(
                        title="Xiaomi Smart Kettle 2 Pro",
                        data={CONF_HOST: host, CONF_TOKEN: token},
                    )
            except (DeviceException, ValueError, OSError):
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {vol.Required(CONF_HOST): str, vol.Required(CONF_TOKEN): str}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
