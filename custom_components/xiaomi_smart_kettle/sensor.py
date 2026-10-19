from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import KettleConfigEntry
from .entity import KettleEntity

STATUS = {0: "standby", 1: "heating", 2: "boiling", 3: "cooling", 4: "keep_warm"}

DESCRIPTIONS = [
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    SensorEntityDescription(key="status", translation_key="status"),
    SensorEntityDescription(key="fault", translation_key="fault"),
    SensorEntityDescription(
        key="warming_time",
        translation_key="warming_time",
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(KettleSensor(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleSensor(KettleEntity, SensorEntity):
    entity_description: SensorEntityDescription

    @property
    def native_value(self) -> StateType:
        value = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.key == "status" and value is not None:
            return STATUS.get(value, f"unknown_{value}")
        return value
