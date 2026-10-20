"""Tests for setting up the integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xiaomi_smart_kettle.const import DOMAIN

from .conftest import UNIQUE_ID
from .fake_kettle import FakeKettle


async def test_removes_the_old_keep_warm_temperature_number(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    config_entry: MockConfigEntry,
    device: FakeKettle,
    enable_custom_integrations: None,
) -> None:
    old = entity_registry.async_get_or_create(
        "number",
        DOMAIN,
        f"{UNIQUE_ID}_keep_warm_temperature",
        config_entry=config_entry,
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert entity_registry.async_get(old.entity_id) is None
    assert entity_registry.async_get_entity_id(
        "number", DOMAIN, f"{UNIQUE_ID}_target_temperature"
    )
