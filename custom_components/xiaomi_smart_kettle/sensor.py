from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        native_unit_of_measurement="min",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(KettleSensor(coordinator, d) for d in DESCRIPTIONS)


class KettleSensor(KettleEntity, SensorEntity):
    entity_description: SensorEntityDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        value = self.coordinator.data.get(self.entity_description.key)
        if self.entity_description.key == "status":
            return STATUS.get(value, f"unknown_{value}")
        return value
