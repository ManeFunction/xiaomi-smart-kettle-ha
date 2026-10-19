from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from miio import MiotDevice
from miio.exceptions import DeviceException

from .const import CONF_TOKEN, DOMAIN, UPDATE_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

PROPERTIES = [
    ("status", 2, 1),
    ("fault", 2, 2),
    ("temperature", 2, 3),
    ("target_temperature", 2, 4),
    ("auto_keep_warm", 2, 5),
    ("keep_warm_temperature", 2, 6),
    ("on", 2, 7),
    ("keep_warm_time", 3, 1),
    ("custom_knob_temp", 3, 2),
    ("lift_remember_temp", 3, 4),
    ("boiling_reminder", 3, 5),
    ("keep_warm_reminder", 3, 6),
    ("kettle_lifting", 3, 7),
    ("extended_mode", 3, 8),
    ("warming_time", 3, 10),
    ("target_mode", 3, 11),
    ("heat_mode", 3, 12),
    ("boil_mode", 3, 13),
    ("knob_sequence", 4, 1),
    ("knob_one", 4, 2),
    ("knob_two", 4, 3),
    ("knob_three", 4, 4),
    ("knob_four", 4, 5),
    ("knob_five", 4, 6),
    ("knob_six", 4, 7),
    ("scene_sequence", 5, 1),
    ("scene_one", 5, 2),
    ("scene_two", 5, 3),
    ("scene_three", 5, 4),
    ("scene_four", 5, 5),
    ("scene_five", 5, 6),
    ("no_disturb", 6, 1),
]


class KettleCoordinator(DataUpdateCoordinator[dict[str, object]]):
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
        self.model = "xiaomi.kettle.v20"
        self.mac = entry.unique_id

    def _read_sync(self) -> dict[str, object]:
        data: dict[str, object] = {}
        for pos in range(0, len(PROPERTIES), 5):
            batch = PROPERTIES[pos : pos + 5]
            req = [
                {"did": name, "siid": siid, "piid": piid} for name, siid, piid in batch
            ]
            result = self.device.send("get_properties", req)
            for item in result:
                if item.get("code") == 0:
                    data[item["did"]] = item.get("value")
        return data

    async def _async_update_data(self) -> dict[str, object]:
        try:
            return await self.hass.async_add_executor_job(self._read_sync)
        except DeviceException as err:
            raise UpdateFailed(
                f"No response from kettle at {self.host}: {err}"
            ) from err

    def _set_property_sync(self, siid: int, piid: int, value: object) -> None:
        result = self.device.send(
            "set_properties",
            [{"did": f"{siid}-{piid}", "siid": siid, "piid": piid, "value": value}],
        )
        if not result or result[0].get("code") != 0:
            raise HomeAssistantError(
                f"Kettle rejected property {siid}.{piid}: {result}"
            )

    async def async_set_property(self, siid: int, piid: int, value: object) -> None:
        await self.hass.async_add_executor_job(
            self._set_property_sync, siid, piid, value
        )
        await self.async_request_refresh()

    def _action_sync(self, siid: int, aiid: int) -> None:
        result = self.device.send(
            "action",
            {"did": f"action-{siid}-{aiid}", "siid": siid, "aiid": aiid, "in": []},
        )
        if isinstance(result, dict) and result.get("code", 0) != 0:
            raise HomeAssistantError(f"Kettle rejected action {siid}.{aiid}: {result}")

    async def async_action(self, siid: int, aiid: int) -> None:
        await self.hass.async_add_executor_job(self._action_sync, siid, aiid)
        await self.async_request_refresh()

    def _set_properties_sync(self, properties: list[dict[str, object]]) -> None:
        payload = [
            {
                "did": f"{item['siid']}-{item['piid']}",
                "siid": item["siid"],
                "piid": item["piid"],
                "value": item["value"],
            }
            for item in properties
        ]
        result = self.device.send("set_properties", payload)
        if not result or any(item.get("code") != 0 for item in result):
            raise HomeAssistantError(f"Kettle rejected properties: {result}")

    async def async_start_heat(self) -> None:
        target = int(self.data.get("target_temperature", 80))
        keep_warm = bool(self.data.get("auto_keep_warm", True))
        keep_temp = int(self.data.get("keep_warm_temperature", 45))
        keep_time = int(self.data.get("keep_warm_time", 1440))
        mode = f"{target},{1 if keep_warm else 0},{keep_temp},{keep_time}"
        await self.hass.async_add_executor_job(
            self._set_properties_sync,
            [
                {"siid": 2, "piid": 4, "value": target},
                {"siid": 2, "piid": 5, "value": keep_warm},
                {"siid": 2, "piid": 6, "value": keep_temp},
                {"siid": 3, "piid": 1, "value": keep_time},
                {"siid": 3, "piid": 11, "value": 0},
                {"siid": 3, "piid": 12, "value": mode},
            ],
        )
        await self.async_request_refresh()

    async def async_start_boil(self) -> None:
        keep_warm = bool(self.data.get("auto_keep_warm", True))
        keep_temp = int(self.data.get("keep_warm_temperature", 45))
        keep_time = int(self.data.get("keep_warm_time", 1440))
        mode = f"99,{1 if keep_warm else 0},{keep_temp},{keep_time}"
        await self.hass.async_add_executor_job(
            self._set_properties_sync,
            [
                {"siid": 2, "piid": 4, "value": 99},
                {"siid": 2, "piid": 5, "value": keep_warm},
                {"siid": 2, "piid": 6, "value": keep_temp},
                {"siid": 3, "piid": 1, "value": keep_time},
                {"siid": 3, "piid": 11, "value": 1},
                {"siid": 3, "piid": 13, "value": mode},
            ],
        )
        await self.async_request_refresh()
