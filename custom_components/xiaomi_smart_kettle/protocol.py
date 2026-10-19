"""MIoT protocol of the Xiaomi Smart Kettle 2 Pro (xiaomi.kettle.v20).

Everything that depends on the device spec lives here: property and action
addresses, and the payloads of the kettle commands. Spec:
https://home.miot-spec.com/spec/xiaomi.kettle.v20

The kettle is reached through a ``send(method, params)`` callable, so this module
needs neither Home Assistant nor a real device to be tested.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

type Send = Callable[[str, Any], Any]

# name -> (siid, piid)
PROPERTIES: dict[str, tuple[int, int]] = {
    "status": (2, 1),
    "fault": (2, 2),
    "temperature": (2, 3),
    "target_temperature": (2, 4),
    "auto_keep_warm": (2, 5),
    "keep_warm_temperature": (2, 6),
    "on": (2, 7),
    "keep_warm_time": (3, 1),
    "custom_knob_temp": (3, 2),
    "lift_remember_temp": (3, 4),
    "boiling_reminder": (3, 5),
    "keep_warm_reminder": (3, 6),
    "kettle_lifting": (3, 7),
    "extended_mode": (3, 8),
    "warming_time": (3, 10),
    "target_mode": (3, 11),
    "heat_mode": (3, 12),
    "boil_mode": (3, 13),
    "knob_sequence": (4, 1),
    "knob_one": (4, 2),
    "knob_two": (4, 3),
    "knob_three": (4, 4),
    "knob_four": (4, 5),
    "knob_five": (4, 6),
    "knob_six": (4, 7),
    "scene_sequence": (5, 1),
    "scene_one": (5, 2),
    "scene_two": (5, 3),
    "scene_three": (5, 4),
    "scene_four": (5, 5),
    "scene_five": (5, 6),
    "no_disturb": (6, 1),
}
POLLED = tuple(PROPERTIES)
READ_BATCH_SIZE = 5

STOP_WORK = (3, 1)  # (siid, aiid)

HEAT_TARGET_MODE = 0
BOIL_TARGET_MODE = 1
BOIL_TEMPERATURE = 99


class KettleError(Exception):
    """The kettle rejected a request."""


class Kettle:
    """Reads and controls one kettle."""

    def __init__(self, send: Send) -> None:
        self._send = send

    def read(self, names: Iterable[str] = POLLED) -> dict[str, Any]:
        """Read properties by name, leaving out those the kettle fails to report."""
        names = list(names)
        values: dict[str, Any] = {}
        for start in range(0, len(names), READ_BATCH_SIZE):
            batch = names[start : start + READ_BATCH_SIZE]
            request = [{"did": name, **_address(name)} for name in batch]
            for item in self._send("get_properties", request):
                if item.get("code") == 0:
                    values[item["did"]] = item.get("value")
        return values

    def write(self, values: Mapping[str, Any]) -> None:
        """Write properties by name in one request, in the given order."""
        payload = []
        for name, value in values.items():
            address = _address(name)
            did = f"{address['siid']}-{address['piid']}"
            payload.append({"did": did, **address, "value": value})
        _check(self._send("set_properties", payload), "properties")

    def stop(self) -> None:
        """Stop heating or boiling."""
        siid, aiid = STOP_WORK
        params = {"did": f"action-{siid}-{aiid}", "siid": siid, "aiid": aiid, "in": []}
        _check(self._send("action", params), f"action {siid}.{aiid}")

    def start_heat(self, state: Mapping[str, Any]) -> None:
        """Heat to the target temperature with the current keep-warm settings."""
        target = int(state.get("target_temperature", 80))
        self._start(state, target, HEAT_TARGET_MODE, "heat_mode")

    def start_boil(self, state: Mapping[str, Any]) -> None:
        """Boil with the current keep-warm settings."""
        self._start(state, BOIL_TEMPERATURE, BOIL_TARGET_MODE, "boil_mode")

    def _start(
        self, state: Mapping[str, Any], target: int, target_mode: int, mode: str
    ) -> None:
        keep_warm = bool(state.get("auto_keep_warm", True))
        keep_temp = int(state.get("keep_warm_temperature", 45))
        keep_time = int(state.get("keep_warm_time", 1440))
        self.write(
            {
                "target_temperature": target,
                "auto_keep_warm": keep_warm,
                "keep_warm_temperature": keep_temp,
                "keep_warm_time": keep_time,
                "target_mode": target_mode,
                mode: f"{target},{int(keep_warm)},{keep_temp},{keep_time}",
            }
        )


def _address(name: str) -> dict[str, int]:
    siid, piid = PROPERTIES[name]
    return {"siid": siid, "piid": piid}


def _check(result: Any, what: str) -> None:
    """Raise unless every item of a miIO result reports code 0."""
    items = result if isinstance(result, list) else [result]
    if not items or any(not isinstance(i, dict) or i.get("code") != 0 for i in items):
        raise KettleError(f"Kettle rejected {what}: {result}")
