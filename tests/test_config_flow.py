"""Tests for the config flow."""

from __future__ import annotations

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from miio.exceptions import DeviceException
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.xiaomi_smart_kettle.const import DOMAIN

from .conftest import HOST, TOKEN, UNIQUE_ID

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

USER_INPUT = {CONF_HOST: HOST, CONF_TOKEN: f" {TOKEN} "}


@pytest.fixture
def info() -> Generator[MagicMock]:
    """Patch the device probe; set ``return_value`` or ``side_effect`` per test."""
    with (
        patch("custom_components.xiaomi_smart_kettle.config_flow.Device") as device_cls,
        patch(
            "custom_components.xiaomi_smart_kettle.async_setup_entry",
            return_value=True,
        ),
    ):
        device_cls.return_value.info.return_value = SimpleNamespace(
            model="xiaomi.kettle.v20", mac_address=UNIQUE_ID.upper()
        )
        yield device_cls.return_value.info


async def _submit(hass: HomeAssistant) -> dict:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    return await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)


async def test_creates_entry(hass: HomeAssistant, info: MagicMock) -> None:
    result = await _submit(hass)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: HOST, CONF_TOKEN: TOKEN}
    assert result["result"].unique_id == UNIQUE_ID


async def test_rejects_other_models(hass: HomeAssistant, info: MagicMock) -> None:
    info.return_value = SimpleNamespace(model="yunmi.kettle.v2", mac_address="x")

    result = await _submit(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unsupported_model"}


async def test_reports_connection_errors(hass: HomeAssistant, info: MagicMock) -> None:
    info.side_effect = DeviceException("timeout")

    result = await _submit(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_updates_host_of_configured_kettle(
    hass: HomeAssistant, info: MagicMock
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=UNIQUE_ID,
        data={CONF_HOST: "192.168.1.2", CONF_TOKEN: TOKEN},
    )
    entry.add_to_hass(hass)

    result = await _submit(hass)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert entry.data[CONF_HOST] == HOST
