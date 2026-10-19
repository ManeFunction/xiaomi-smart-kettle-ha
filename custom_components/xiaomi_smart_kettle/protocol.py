"""MIoT protocol of the Xiaomi Smart Kettle 2 Pro (xiaomi.kettle.v20).

Everything that depends on the device spec lives here: property and action
addresses, and the payloads of the kettle commands. Spec:
https://home.miot-spec.com/spec/xiaomi.kettle.v20

The kettle is reached through a ``send(method, params)`` callable, so this module
needs neither Home Assistant nor a real device to be tested.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from threading import Lock
from typing import Any

type Send = Callable[[str, Any], Any]

MODEL = "xiaomi.kettle.v20"

# name -> (siid, piid), for the properties this integration reads or writes
PROPERTIES: dict[str, tuple[int, int]] = {
    "status": (2, 1),
    "fault": (2, 2),
    "temperature": (2, 3),
    "target_temperature": (2, 4),
    "auto_keep_warm": (2, 5),
    "keep_warm_temperature": (2, 6),
    "keep_warm_time": (3, 1),
    "lift_remember_temp": (3, 4),
    "boiling_reminder": (3, 5),
    "keep_warm_reminder": (3, 6),
    "kettle_lifting": (3, 7),
    "warming_time": (3, 10),
    "target_mode": (3, 11),
    "heat_mode": (3, 12),
    "boil_mode": (3, 13),
    "no_disturb": (6, 1),
}
# Properties the entities show; the mode properties are only written.
POLLED = (
    "status",
    "fault",
    "temperature",
    "target_temperature",
    "auto_keep_warm",
    "keep_warm_temperature",
    "keep_warm_time",
    "lift_remember_temp",
    "boiling_reminder",
    "keep_warm_reminder",
    "kettle_lifting",
    "warming_time",
    "no_disturb",
)
READ_BATCH_SIZE = 5
# Properties Heat and Boil send back to the kettle unchanged
START_INPUTS = (
    "target_temperature",
    "auto_keep_warm",
    "keep_warm_temperature",
    "keep_warm_time",
)

STOP_WORK = (3, 1)  # (siid, aiid)

STATUSES = {0: "standby", 1: "heating", 2: "boiling", 3: "cooling", 4: "keep_warm"}

HEAT_TARGET_MODE = 0
BOIL_TARGET_MODE = 1
BOIL_TEMPERATURE = 99


class KettleError(Exception):
    """A kettle request could not be completed."""


class KettleRejectedError(KettleError):
    """The kettle answered a request with an error code."""

    def __init__(self, request: str, result: Any) -> None:
        super().__init__(f"Kettle rejected {request}: {result}")
        self.result = result


class KettleStateError(KettleError):
    """The kettle did not report properties a command needs."""

    def __init__(self, missing: list[str]) -> None:
        super().__init__(f"Kettle did not report {', '.join(missing)}")
        self.missing = missing


class Kettle:
    """Reads and controls one kettle."""

    def __init__(self, send: Send) -> None:
        self._send = send
        # python-miio tracks message IDs per device without locking, so two
        # requests in flight at once can reuse an ID and time out.
        self._lock = Lock()

    def read(self, names: Iterable[str] = POLLED) -> dict[str, Any]:
        """Read properties by name, leaving out those the kettle fails to report."""
        names = list(names)
        values: dict[str, Any] = {}
        for start in range(0, len(names), READ_BATCH_SIZE):
            batch = names[start : start + READ_BATCH_SIZE]
            request = [{"did": name, **_address(name)} for name in batch]
            for item in self._request("get_properties", request):
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
        _check(self._request("set_properties", payload), "properties")

    def stop(self) -> None:
        """Stop heating or boiling."""
        siid, aiid = STOP_WORK
        params = {"did": f"action-{siid}-{aiid}", "siid": siid, "aiid": aiid, "in": []}
        _check(self._request("action", params), f"action {siid}.{aiid}")

    def _request(self, method: str, params: Any) -> Any:
        with self._lock:
            return self._send(method, params)

    def start_heat(self) -> None:
        """Heat to the target temperature with the current keep-warm settings."""
        state = self._read_start_inputs()
        target = int(state["target_temperature"])
        self._start(state, target, HEAT_TARGET_MODE, "heat_mode")

    def start_boil(self) -> None:
        """Boil with the current keep-warm settings."""
        state = self._read_start_inputs()
        self._start(state, BOIL_TEMPERATURE, BOIL_TARGET_MODE, "boil_mode")

    def _read_start_inputs(self) -> dict[str, Any]:
        """Read the settings Heat and Boil resend, fresh from the kettle.

        A cached poll can be seconds old and would undo a change made in the
        Mi Home app or on the kettle in the meantime.
        """
        state = self.read(START_INPUTS)
        missing = [name for name in START_INPUTS if state.get(name) is None]
        if missing:
            raise KettleStateError(missing)
        return state

    def _start(
        self, state: Mapping[str, Any], target: int, target_mode: int, mode: str
    ) -> None:
        keep_warm = bool(state["auto_keep_warm"])
        keep_temp = int(state["keep_warm_temperature"])
        keep_time = int(state["keep_warm_time"])
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
        raise KettleRejectedError(what, result)
