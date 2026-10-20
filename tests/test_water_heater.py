"""Tests for the kettle water heater."""

from __future__ import annotations

from homeassistant.components.water_heater import (
    ATTR_TEMPERATURE,
    DOMAIN as WATER_HEATER_DOMAIN,
    SERVICE_SET_TEMPERATURE,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
import pytest

from .fake_kettle import FakeKettle

pytestmark = pytest.mark.usefixtures("setup_integration")

ENTITY_ID = "water_heater.xiaomi_smart_kettle_2_pro"


async def test_state(hass: HomeAssistant) -> None:
    state = hass.states.get(ENTITY_ID)

    assert state.state == STATE_OFF
    assert state.attributes["current_temperature"] == 23
    assert state.attributes["temperature"] == 80
    assert state.attributes["min_temp"] == 40
    assert state.attributes["max_temp"] == 99
    assert state.attributes["target_temp_step"] == 1


@pytest.mark.parametrize(
    ("status", "state"),
    [(1, "heating"), (2, "boiling"), (3, "cooling"), (4, "keep_warm"), (9, None)],
)
async def test_state_follows_status(
    hass: HomeAssistant,
    device: FakeKettle,
    setup_integration,
    status: int,
    state: str | None,
) -> None:
    device.state[(2, 1)] = status

    await setup_integration.runtime_data.async_refresh()

    assert hass.states.get(ENTITY_ID).state == (state or STATE_UNKNOWN)


async def test_turn_on_starts_heat(hass: HomeAssistant, device: FakeKettle) -> None:
    await _call(hass, SERVICE_TURN_ON)

    [payload] = device.sent("set_properties")
    assert payload[-1] == {"did": "3-12", "siid": 3, "piid": 12, "value": "80,1,50,720"}


async def test_turn_off_stops(hass: HomeAssistant, device: FakeKettle) -> None:
    await _call(hass, SERVICE_TURN_OFF)

    assert device.sent("action") == [
        {"did": "action-3-1", "siid": 3, "aiid": 1, "in": []}
    ]


async def test_set_temperature_sets_heat_target(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    await _call(hass, SERVICE_SET_TEMPERATURE, {ATTR_TEMPERATURE: 70})

    assert device.sent("set_properties") == [
        [{"did": "2-4", "siid": 2, "piid": 4, "value": 70}]
    ]
    assert hass.states.get(ENTITY_ID).attributes["temperature"] == 70
    assert (
        hass.states.get("number.xiaomi_smart_kettle_2_pro_heat_temperature").state
        == "70"
    )


async def test_target_survives_boil(hass: HomeAssistant, device: FakeKettle) -> None:
    await hass.services.async_call(
        "button",
        "press",
        {ATTR_ENTITY_ID: "button.xiaomi_smart_kettle_2_pro_boil"},
        blocking=True,
    )

    assert device.state[(2, 4)] == 99
    assert hass.states.get(ENTITY_ID).attributes["temperature"] == 80


async def _call(
    hass: HomeAssistant,
    service: str,
    data: dict | None = None,
    entity_id: str = ENTITY_ID,
) -> None:
    await hass.services.async_call(
        WATER_HEATER_DOMAIN,
        service,
        {ATTR_ENTITY_ID: entity_id, **(data or {})},
        blocking=True,
    )


KEEP_WARM_ID = "water_heater.xiaomi_smart_kettle_2_pro_keep_kettle_warm"


async def test_keep_warm_state(hass: HomeAssistant, device: FakeKettle) -> None:
    state = hass.states.get(KEEP_WARM_ID)

    assert state.state == "on"
    assert state.attributes["temperature"] == 50
    assert state.attributes["current_temperature"] == 50  # not the water's 23
    assert state.attributes["min_temp"] == 40
    assert state.attributes["max_temp"] == 90


async def test_keep_warm_follows_the_switch(
    hass: HomeAssistant, device: FakeKettle, setup_integration
) -> None:
    device.state[(2, 5)] = False

    await setup_integration.runtime_data.async_refresh()

    assert hass.states.get(KEEP_WARM_ID).state == STATE_OFF


async def test_keep_warm_turn_off_writes_switch(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    await _call(hass, SERVICE_TURN_OFF, entity_id=KEEP_WARM_ID)

    assert device.sent("set_properties") == [
        [{"did": "2-5", "siid": 2, "piid": 5, "value": False}]
    ]
    assert hass.states.get("switch.xiaomi_smart_kettle_2_pro_keep_warm").state == "off"


async def test_keep_warm_set_temperature(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    await _call(
        hass, SERVICE_SET_TEMPERATURE, {ATTR_TEMPERATURE: 65.4}, entity_id=KEEP_WARM_ID
    )

    assert device.sent("set_properties") == [
        [{"did": "2-6", "siid": 2, "piid": 6, "value": 65}]
    ]
    assert hass.states.get(KEEP_WARM_ID).attributes["current_temperature"] == 65
