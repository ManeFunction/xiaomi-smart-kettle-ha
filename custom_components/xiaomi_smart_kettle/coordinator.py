from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from miio import MiotDevice
from miio.exceptions import DeviceException

from .const import DOMAIN, UPDATE_INTERVAL_SECONDS
from .protocol import Kettle, KettleRejectedError, KettleStateError

_LOGGER = logging.getLogger(__name__)

type KettleConfigEntry = ConfigEntry[KettleCoordinator]


class KettleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    config_entry: KettleConfigEntry

    def __init__(self, hass: HomeAssistant, entry: KettleConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
            config_entry=entry,
        )
        self.host = entry.data[CONF_HOST]
        self.kettle = Kettle(MiotDevice(self.host, entry.data[CONF_TOKEN]).send)

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
        await self._async_run(self.kettle.start_heat)

    async def async_start_boil(self) -> None:
        await self._async_run(self.kettle.start_boil)

    async def async_stop(self) -> None:
        await self._async_run(self.kettle.stop)

    async def _async_run(self, command: Callable[..., None], *args: Any) -> None:
        """Run a kettle command in the executor, then refresh the state."""
        try:
            await self.hass.async_add_executor_job(command, *args)
        except DeviceException as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_communicate",
                translation_placeholders={"host": self.host, "error": str(err)},
            ) from err
        except KettleRejectedError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_rejected",
                translation_placeholders={"result": str(err.result)},
            ) from err
        except KettleStateError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="state_unknown",
                translation_placeholders={"properties": ", ".join(err.missing)},
            ) from err
        await self.async_request_refresh()
