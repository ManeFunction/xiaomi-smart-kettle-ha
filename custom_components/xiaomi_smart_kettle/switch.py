from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KettleEntity

DESCRIPTIONS = [
    SwitchEntityDescription(key="auto_keep_warm", translation_key="auto_keep_warm"),
    SwitchEntityDescription(
        key="lift_remember_temp", translation_key="lift_remember_temp"
    ),
    SwitchEntityDescription(key="boiling_reminder", translation_key="boiling_reminder"),
    SwitchEntityDescription(
        key="keep_warm_reminder", translation_key="keep_warm_reminder"
    ),
    SwitchEntityDescription(key="no_disturb", translation_key="no_disturb"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(KettleSwitch(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleSwitch(KettleEntity, SwitchEntity):
    entity_description: SwitchEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self.entity_description.key))

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_set_properties({self.entity_description.key: True})

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_properties(
            {self.entity_description.key: False}
        )
