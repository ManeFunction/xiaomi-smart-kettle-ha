"""A stand-in for the kettle's miIO transport."""

from __future__ import annotations

from typing import Any

# (siid, piid) -> value, as a kettle heating to 80 °C with keep-warm on reports it
DEVICE_STATE: dict[tuple[int, int], Any] = {
    (2, 1): 0,
    (2, 2): 0,
    (2, 3): 23,
    (2, 4): 80,
    (2, 5): True,
    (2, 6): 50,
    (2, 7): False,
    (3, 1): 720,
    (3, 2): False,
    (3, 4): True,
    (3, 5): False,
    (3, 6): False,
    (3, 7): False,
    (3, 8): "",
    (3, 10): 0,
    (3, 11): 0,
    (3, 12): "80,1,50,720",
    (3, 13): "99,1,50,720",
    (6, 1): False,
}

NOT_FOUND = -4003


class FakeKettle:
    """Answers miIO requests from a property table and records every request."""

    def __init__(self) -> None:
        self.state = dict(DEVICE_STATE)
        self.requests: list[tuple[str, Any]] = []
        self.failing_reads: set[tuple[int, int]] = set()
        self.reject_code = 0
        self.error: Exception | None = None

    def send(self, method: str, params: Any = None) -> Any:
        self.requests.append((method, params))
        if self.error is not None:
            raise self.error
        if method == "get_properties":
            return [self._get(item) for item in params]
        if method == "set_properties":
            return [self._set(item) for item in params]
        if method == "action":
            return {"did": params["did"], "code": self.reject_code, "out": []}
        raise AssertionError(f"unexpected method {method}")

    def sent(self, method: str) -> list[Any]:
        """Return the params of every request with this method."""
        return [params for m, params in self.requests if m == method]

    def _get(self, item: dict[str, Any]) -> dict[str, Any]:
        address = (item["siid"], item["piid"])
        if address in self.failing_reads or address not in self.state:
            return {**item, "code": NOT_FOUND}
        return {**item, "code": 0, "value": self.state[address]}

    def _set(self, item: dict[str, Any]) -> dict[str, Any]:
        if self.reject_code == 0:
            self.state[(item["siid"], item["piid"])] = item["value"]
        return {"did": item["did"], "code": self.reject_code}
