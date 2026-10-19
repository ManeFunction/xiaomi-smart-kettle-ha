"""Fixtures for the Xiaomi Smart Kettle tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import patch

from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xiaomi_smart_kettle.const import DOMAIN

from .fake_kettle import FakeKettle

HOST = "192.168.1.50"
TOKEN = "00112233445566778899aabbccddeeff"
UNIQUE_ID = "aa:bb:cc:dd:ee:ff"


@pytest.fixture
def device() -> Generator[FakeKettle]:
    """Replace the miIO device the coordinator talks to with a fake kettle."""
    fake = FakeKettle()
    with patch(
        "custom_components.xiaomi_smart_kettle.coordinator.MiotDevice"
    ) as device_cls:
        device_cls.return_value.send = fake.send
        yield fake


@pytest.fixture
def config_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Xiaomi Smart Kettle 2 Pro",
        unique_id=UNIQUE_ID,
        data={CONF_HOST: HOST, CONF_TOKEN: TOKEN},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device: FakeKettle,
    enable_custom_integrations: None,
) -> MockConfigEntry:
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry
