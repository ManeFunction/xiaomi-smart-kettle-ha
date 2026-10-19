from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity

DESCRIPTIONS = [
    # Without a device class the HomeKit bridge exposes a binary sensor as an
    # occupancy sensor. As an opening, Apple Home shows a contact sensor that is
    # open while the kettle is off its base.
    BinarySensorEntityDescription(
        key="kettle_lifting",
        translation_key="kettle_lifting",
        device_class=BinarySensorDeviceClass.OPENING,
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
