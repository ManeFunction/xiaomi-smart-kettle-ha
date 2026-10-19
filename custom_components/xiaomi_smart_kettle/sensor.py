from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
from .protocol import STATUSES


@dataclass(frozen=True, kw_only=True)
class KettleSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Any], StateType] = lambda value: value


DESCRIPTIONS = [
    KettleSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KettleSensorDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=list(STATUSES.values()),
        value_fn=STATUSES.get,
    ),
    KettleSensorDescription(key="fault", translation_key="fault"),
    KettleSensorDescription(
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
    entity_description: KettleSensorDescription

    @property
    def native_value(self) -> StateType:
        value = self.coordinator.data.get(self.entity_description.key)
        return self.entity_description.value_fn(value)
