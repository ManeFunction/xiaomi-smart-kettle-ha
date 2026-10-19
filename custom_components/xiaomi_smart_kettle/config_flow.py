from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_TOKEN
from miio import Device
from miio.exceptions import DeviceException
import voluptuous as vol

from .const import DEVICE_NAME, DOMAIN
from .protocol import MODEL


class XiaomiSmartKettleConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN].strip()
            try:
                info = await self.hass.async_add_executor_job(Device(host, token).info)
                if info.model != MODEL:
                    errors["base"] = "unsupported_model"
                else:
                    await self.async_set_unique_id((info.mac_address or host).lower())
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: host, CONF_TOKEN: token}
                    )
                    return self.async_create_entry(
                        title=DEVICE_NAME,
                        data={CONF_HOST: host, CONF_TOKEN: token},
                    )
            except (DeviceException, ValueError, OSError):
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {vol.Required(CONF_HOST): str, vol.Required(CONF_TOKEN): str}
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
