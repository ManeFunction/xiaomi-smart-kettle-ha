from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KettleEntity

DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="kettle_lifting", translation_key="kettle_lifting"
    )
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(KettleBinarySensor(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleBinarySensor(KettleEntity, BinarySensorEntity):
    entity_description: BinarySensorEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self):
        return bool(self.coordinator.data.get(self.entity_description.key))
