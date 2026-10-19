from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity

DESCRIPTIONS = [
    SwitchEntityDescription(key="auto_keep_warm", translation_key="auto_keep_warm"),
    # Settings rather than everyday controls: shown under Configuration
    *(
        SwitchEntityDescription(
            key=key, translation_key=key, entity_category=EntityCategory.CONFIG
        )
        for key in (
            "lift_remember_temp",
            "boiling_reminder",
            "keep_warm_reminder",
            "no_disturb",
        )
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(KettleSwitch(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleSwitch(KettleEntity, SwitchEntity):
    entity_description: SwitchEntityDescription

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self.entity_description.key)
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_properties({self.entity_description.key: True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_properties(
            {self.entity_description.key: False}
        )
