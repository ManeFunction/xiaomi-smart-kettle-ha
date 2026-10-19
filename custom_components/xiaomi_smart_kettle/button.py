from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KettleEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            KettleHeatButton(entry.runtime_data),
            KettleBoilButton(entry.runtime_data),
            KettleStopButton(entry.runtime_data),
        ]
    )


class KettleHeatButton(KettleEntity, ButtonEntity):
    _attr_translation_key = "heat"
    _attr_icon = "mdi:kettle-steam"

    def __init__(self, coordinator):
        super().__init__(coordinator, "heat")

    async def async_press(self) -> None:
        await self.coordinator.async_start_heat()


class KettleBoilButton(KettleEntity, ButtonEntity):
    _attr_translation_key = "boil"
    _attr_icon = "mdi:kettle-steam"

    def __init__(self, coordinator):
        super().__init__(coordinator, "boil")

    async def async_press(self) -> None:
        await self.coordinator.async_start_boil()


class KettleStopButton(KettleEntity, ButtonEntity):
    _attr_translation_key = "stop"
    _attr_icon = "mdi:stop-circle-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator, "stop")

    async def async_press(self) -> None:
        await self.coordinator.async_stop()
