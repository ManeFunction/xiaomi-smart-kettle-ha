from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from miio import MiotDevice
from miio.exceptions import DeviceException

from .const import CONF_TOKEN, DOMAIN, UPDATE_INTERVAL_SECONDS
from .protocol import Kettle, KettleError

_LOGGER = logging.getLogger(__name__)


class KettleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            config_entry=entry,
        )
        self.host = entry.data[CONF_HOST]
        self.token = entry.data[CONF_TOKEN]
        self.device = MiotDevice(self.host, self.token)
        self.kettle = Kettle(self.device.send)
        self.model = "xiaomi.kettle.v20"
        self.mac = entry.unique_id

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self.kettle.read)
        except DeviceException as err:
            raise UpdateFailed(
                f"No response from kettle at {self.host}: {err}"
            ) from err

    async def async_set_properties(self, values: Mapping[str, Any]) -> None:
        await self._async_run(self.kettle.write, values)

    async def async_start_heat(self) -> None:
        await self._async_run(self.kettle.start_heat, self.data)

    async def async_start_boil(self) -> None:
        await self._async_run(self.kettle.start_boil, self.data)

    async def async_stop(self) -> None:
        await self._async_run(self.kettle.stop)

    async def _async_run(self, command: Callable[..., None], *args: Any) -> None:
        """Run a kettle command in the executor, then refresh the state."""
        try:
            await self.hass.async_add_executor_job(command, *args)
        except KettleError as err:
            raise HomeAssistantError(str(err)) from err
        await self.async_request_refresh()
