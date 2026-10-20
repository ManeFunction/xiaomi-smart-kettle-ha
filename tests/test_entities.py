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
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from miio.exceptions import DeviceException
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
    assert hass.states.get(f"number.{PREFIX}_heat_temperature").state == "80"
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
        if entry.domain not in ("button", "water_heater")
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


@pytest.mark.parametrize(("raw", "state"), [(4, "keep_warm"), (9, STATE_UNKNOWN)])
async def test_status_is_an_enum(
    hass: HomeAssistant, device: FakeKettle, setup_integration, raw: int, state: str
) -> None:
    device.state[(2, 1)] = raw

    await setup_integration.runtime_data.async_refresh()

    status = hass.states.get(f"sensor.{PREFIX}_status")
    assert status.state == state
    assert status.attributes["options"] == [
        "standby",
        "heating",
        "boiling",
        "cooling",
        "keep_warm",
    ]


async def test_settings_are_configuration_entities(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    def category(entity_id: str) -> EntityCategory | None:
        return entity_registry.async_get(entity_id).entity_category

    assert category(f"switch.{PREFIX}_keep_warm") is None
    for name in (
        "remember_temperature_after_lifting",
        "boiling_notification",
        "keep_warm_notification",
        "do_not_disturb",
    ):
        assert category(f"switch.{PREFIX}_{name}") is EntityCategory.CONFIG


async def test_kettle_lifted_is_an_opening(hass: HomeAssistant) -> None:
    state = hass.states.get(f"binary_sensor.{PREFIX}_kettle_lifted")

    assert state.attributes["device_class"] == "opening"


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


async def test_heat_temperature_survives_boil(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    await _press(hass, "boil")

    assert device.state[(2, 4)] == 99
    assert hass.states.get(f"number.{PREFIX}_heat_temperature").state == "80"


async def test_heat_temperature_sets_heat_target(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    await _press(hass, "boil")
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: f"number.{PREFIX}_heat_temperature", ATTR_VALUE: 70},
        blocking=True,
    )
    assert device.sent("set_properties")[1:] == []  # only Boil was sent
    await _press(hass, "heat")

    assert device.state[(3, 12)] == "70,1,50,720"


async def test_poll_keeps_the_heat_temperature(
    hass: HomeAssistant, device: FakeKettle, setup_integration
) -> None:
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: f"number.{PREFIX}_heat_temperature", ATTR_VALUE: 70},
        blocking=True,
    )

    await setup_integration.runtime_data.async_refresh()
    assert hass.states.get(f"number.{PREFIX}_heat_temperature").state == "70"

    device.state[(2, 4)] = 85  # heated to 85 °C from the Mi Home app
    await setup_integration.runtime_data.async_refresh()
    assert hass.states.get(f"number.{PREFIX}_heat_temperature").state == "85"


async def test_stop_button(hass: HomeAssistant, device: FakeKettle) -> None:
    await _press(hass, "stop")

    assert device.sent("action") == [
        {"did": "action-3-1", "siid": 3, "aiid": 1, "in": []}
    ]


async def test_command_reports_unreachable_kettle(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    device.error = DeviceException("timeout")

    with pytest.raises(HomeAssistantError) as err:
        await _press(hass, "stop")

    assert err.value.translation_key == "cannot_communicate"
    assert str(err.value) == "Cannot reach the kettle at 192.168.1.50: timeout"


async def test_command_reports_rejection(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    device.reject_code = -4004

    with pytest.raises(HomeAssistantError) as err:
        await _press(hass, "stop")

    assert err.value.translation_key == "command_rejected"


async def test_heat_refuses_when_settings_are_unknown(
    hass: HomeAssistant, device: FakeKettle
) -> None:
    device.failing_reads.add((2, 6))

    with pytest.raises(HomeAssistantError) as err:
        await _press(hass, "heat")

    assert err.value.translation_key == "state_unknown"
    assert device.sent("set_properties") == []


async def _press(hass: HomeAssistant, key: str) -> None:
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: f"button.{PREFIX}_{key}"},
        blocking=True,
    )
