"""Tests for the kettle protocol, without Home Assistant."""

from __future__ import annotations

import pytest

from custom_components.xiaomi_smart_kettle.protocol import (
    POLLED,
    READ_BATCH_SIZE,
    Kettle,
    KettleError,
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


def test_start_heat_payload(device: FakeKettle, kettle: Kettle) -> None:
    kettle.start_heat(kettle.read())

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
    kettle.start_boil(kettle.read())

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
