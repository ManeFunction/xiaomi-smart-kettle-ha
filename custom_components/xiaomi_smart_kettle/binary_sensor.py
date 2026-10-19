from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity

DESCRIPTIONS = [
    BinarySensorEntityDescription(
        key="kettle_lifting", translation_key="kettle_lifting"
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(KettleBinarySensor(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleBinarySensor(KettleEntity, BinarySensorEntity):
    entity_description: BinarySensorEntityDescription

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self.entity_description.key)
        return None if value is None else bool(value)
