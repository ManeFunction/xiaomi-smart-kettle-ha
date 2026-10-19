"""Tests for the kettle entities."""

from __future__ import annotations

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest

from custom_components.xiaomi_smart_kettle.protocol import POLLED

from .conftest import UNIQUE_ID
from .fake_kettle import FakeKettle

pytestmark = pytest.mark.usefixtures("setup_integration")

PREFIX = "xiaomi_smart_kettle_2_pro"


async def test_states(hass: HomeAssistant) -> None:
    assert hass.states.get(f"sensor.{PREFIX}_water_temperature").state == "23"
    assert hass.states.get(f"sensor.{PREFIX}_status").state == "standby"
    assert hass.states.get(f"binary_sensor.{PREFIX}_kettle_lifted").state == STATE_OFF
    assert hass.states.get(f"switch.{PREFIX}_keep_warm").state == STATE_ON
    assert hass.states.get(f"number.{PREFIX}_target_temperature").state == "80"
    assert hass.states.get(f"number.{PREFIX}_keep_warm_time").state == "720"


async def test_every_entity_value_is_polled(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, setup_integration
) -> None:
    entries = er.async_entries_for_config_entry(
        entity_registry, setup_integration.entry_id
    )
    keys = {
        entry.unique_id.removeprefix(f"{UNIQUE_ID}_")
        for entry in entries
        if entry.domain != "button"
    }
    assert keys <= set(POLLED)


async def test_unreported_values_are_unknown(
    hass: HomeAssistant, device: FakeKettle, setup_integration
) -> None:
    device.failing_reads |= {(2, 1), (3, 7), (6, 1)}

    await setup_integration.runtime_data.async_refresh()

    for entity_id in (
        f"sensor.{PREFIX}_status",
        f"binary_sensor.{PREFIX}_kettle_lifted",
        f"switch.{PREFIX}_do_not_disturb",
    ):
        assert hass.states.get(entity_id).state == STATE_UNKNOWN


async def test_unique_ids(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    entry = entity_registry.async_get(f"sensor.{PREFIX}_water_temperature")
    assert entry.unique_id == f"{UNIQUE_ID}_temperature"
    entry = entity_registry.async_get(f"button.{PREFIX}_heat")
    assert entry.unique_id == f"{UNIQUE_ID}_heat"


async def test_switch_writes_property(hass: HomeAssistant, device: FakeKettle) -> None:
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: f"switch.{PREFIX}_do_not_disturb"},
        blocking=True,
    )

    assert device.sent("set_properties") == [
        [{"did": "6-1", "siid": 6, "piid": 1, "value": True}]
    ]


async def test_number_writes_property(hass: HomeAssistant, device: FakeKettle) -> None:
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: f"number.{PREFIX}_keep_warm_time", ATTR_VALUE: 90},
        blocking=True,
    )

    assert device.sent("set_properties") == [
        [{"did": "3-1", "siid": 3, "piid": 1, "value": 90}]
    ]


async def test_heat_button(hass: HomeAssistant, device: FakeKettle) -> None:
    await _press(hass, "heat")

    [payload] = device.sent("set_properties")
    assert payload[-1] == {"did": "3-12", "siid": 3, "piid": 12, "value": "80,1,50,720"}


async def test_boil_button(hass: HomeAssistant, device: FakeKettle) -> None:
    await _press(hass, "boil")

    [payload] = device.sent("set_properties")
    assert payload[-1] == {"did": "3-13", "siid": 3, "piid": 13, "value": "99,1,50,720"}


async def test_stop_button(hass: HomeAssistant, device: FakeKettle) -> None:
    await _press(hass, "stop")

    assert device.sent("action") == [
        {"did": "action-3-1", "siid": 3, "aiid": 1, "in": []}
    ]


async def _press(hass: HomeAssistant, key: str) -> None:
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: f"button.{PREFIX}_{key}"},
        blocking=True,
    )
