"""Tests for the kettle protocol, without Home Assistant."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from custom_components.xiaomi_smart_kettle.protocol import (
    POLLED,
    READ_BATCH_SIZE,
    Kettle,
    KettleError,
    KettleStateError,
)

from .fake_kettle import FakeKettle


@pytest.fixture
def device() -> FakeKettle:
    return FakeKettle()


@pytest.fixture
def kettle(device: FakeKettle) -> Kettle:
    return Kettle(device.send)


def test_read_batches_requests(device: FakeKettle, kettle: Kettle) -> None:
    kettle.read()

    batches = device.sent("get_properties")
    assert [len(batch) for batch in batches[:-1]] == [READ_BATCH_SIZE] * (
        len(batches) - 1
    )
    assert [item["did"] for batch in batches for item in batch] == list(POLLED)


def test_read_maps_values_by_name(kettle: Kettle) -> None:
    values = kettle.read(["temperature", "target_temperature", "heat_mode"])

    assert values == {
        "temperature": 23,
        "target_temperature": 80,
        "heat_mode": "80,1,50,720",
    }


def test_read_leaves_out_failed_properties(device: FakeKettle, kettle: Kettle) -> None:
    device.failing_reads.add((2, 3))

    values = kettle.read(["temperature", "target_temperature"])

    assert values == {"target_temperature": 80}


def test_write_sends_one_request_in_order(device: FakeKettle, kettle: Kettle) -> None:
    kettle.write({"keep_warm_time": 120, "no_disturb": True})

    assert device.sent("set_properties") == [
        [
            {"did": "3-1", "siid": 3, "piid": 1, "value": 120},
            {"did": "6-1", "siid": 6, "piid": 1, "value": True},
        ]
    ]


def test_write_raises_when_rejected(device: FakeKettle, kettle: Kettle) -> None:
    device.reject_code = -4004

    with pytest.raises(KettleError):
        kettle.write({"no_disturb": True})


def test_stop_calls_stop_work_action(device: FakeKettle, kettle: Kettle) -> None:
    kettle.stop()

    assert device.sent("action") == [
        {"did": "action-3-1", "siid": 3, "aiid": 1, "in": []}
    ]


@pytest.mark.parametrize("result", [{"code": -4004}, [], None, "ok"])
def test_stop_raises_on_unexpected_result(result: object) -> None:
    kettle = Kettle(lambda method, params: result)

    with pytest.raises(KettleError):
        kettle.stop()


def test_requests_never_overlap(device: FakeKettle) -> None:
    in_flight = 0
    overlapped = threading.Event()

    def slow_send(method: str, params: object) -> object:
        nonlocal in_flight
        in_flight += 1
        if in_flight > 1:
            overlapped.set()
        time.sleep(0.01)
        in_flight -= 1
        return device.send(method, params)

    kettle = Kettle(slow_send)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for _ in range(4):
            pool.submit(kettle.read)
        pool.submit(kettle.stop)

    assert not overlapped.is_set()


def test_start_heat_payload(device: FakeKettle, kettle: Kettle) -> None:
    kettle.start_heat()

    assert device.sent("set_properties") == [
        [
            {"did": "2-4", "siid": 2, "piid": 4, "value": 80},
            {"did": "2-5", "siid": 2, "piid": 5, "value": True},
            {"did": "2-6", "siid": 2, "piid": 6, "value": 50},
            {"did": "3-1", "siid": 3, "piid": 1, "value": 720},
            {"did": "3-11", "siid": 3, "piid": 11, "value": 0},
            {"did": "3-12", "siid": 3, "piid": 12, "value": "80,1,50,720"},
        ]
    ]


def test_start_boil_payload(device: FakeKettle, kettle: Kettle) -> None:
    device.state[(2, 5)] = False
    kettle.start_boil()

    assert device.sent("set_properties") == [
        [
            {"did": "2-4", "siid": 2, "piid": 4, "value": 99},
            {"did": "2-5", "siid": 2, "piid": 5, "value": False},
            {"did": "2-6", "siid": 2, "piid": 6, "value": 50},
            {"did": "3-1", "siid": 3, "piid": 1, "value": 720},
            {"did": "3-11", "siid": 3, "piid": 11, "value": 1},
            {"did": "3-13", "siid": 3, "piid": 13, "value": "99,0,50,720"},
        ]
    ]


def test_start_uses_fresh_settings(device: FakeKettle, kettle: Kettle) -> None:
    kettle.read()
    device.state[(2, 6)] = 60  # changed in the Mi Home app after the poll

    kettle.start_boil()

    [payload] = device.sent("set_properties")
    assert payload[-1]["value"] == "99,1,60,720"


@pytest.mark.parametrize("start", [Kettle.start_heat, Kettle.start_boil])
def test_start_refuses_without_settings(
    device: FakeKettle, kettle: Kettle, start
) -> None:
    device.failing_reads.add((3, 1))

    with pytest.raises(KettleStateError) as err:
        start(kettle)

    assert err.value.missing == ["keep_warm_time"]
    assert device.sent("set_properties") == []


def _heat_payload_target(device: FakeKettle) -> object:
    return device.sent("set_properties")[-1][0]["value"]


def test_heat_after_boil_keeps_the_heat_target(
    device: FakeKettle, kettle: Kettle
) -> None:
    kettle.read()
    kettle.start_boil()
    kettle.read()
    assert device.state[(2, 4)] == 99

    kettle.start_heat()

    assert _heat_payload_target(device) == 80
    assert device.state[(3, 12)] == "80,1,50,720"


def test_heat_target_follows_changes_in_heat_mode(
    device: FakeKettle, kettle: Kettle
) -> None:
    kettle.read()
    device.state[(2, 4)] = 85  # changed on the kettle

    kettle.start_heat()

    assert _heat_payload_target(device) == 85


def test_heat_target_after_restart_in_boil_mode(device: FakeKettle) -> None:
    device.state.update({(2, 4): 99, (3, 11): 1, (3, 12): "75,1,50,720"})
    kettle = Kettle(device.send)

    kettle.start_heat()

    assert _heat_payload_target(device) == 75


def test_set_heat_target_while_in_boil_mode(device: FakeKettle) -> None:
    device.state.update({(2, 4): 99, (3, 11): 1})
    kettle = Kettle(device.send)
    kettle.read()

    kettle.set_heat_target(70)
    kettle.read()

    assert kettle.heat_target == 70
    kettle.start_heat()
    assert _heat_payload_target(device) == 70


def test_heat_refuses_when_heat_target_is_unknown(device: FakeKettle) -> None:
    device.state.update({(2, 4): 99, (3, 11): 1, (3, 12): ""})
    kettle = Kettle(device.send)

    with pytest.raises(KettleStateError) as err:
        kettle.start_heat()

    assert err.value.missing == ["target_temperature"]
    assert device.sent("set_properties") == []


def test_set_heat_target_sends_nothing(device: FakeKettle, kettle: Kettle) -> None:
    kettle.read()

    kettle.set_heat_target(70)
    kettle.read()

    assert device.sent("set_properties") == []
    assert kettle.heat_target == 70
