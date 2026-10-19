from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import KettleEntity


@dataclass(frozen=True, kw_only=True)
class KettleNumberDescription(NumberEntityDescription):
    siid: int
    piid: int


DESCRIPTIONS = [
    KettleNumberDescription(
        key="target_temperature",
        translation_key="target_temperature",
        siid=2,
        piid=4,
        native_min_value=40,
        native_max_value=99,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KettleNumberDescription(
        key="keep_warm_temperature",
        translation_key="keep_warm_temperature",
        siid=2,
        piid=6,
        native_min_value=40,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    KettleNumberDescription(
        key="keep_warm_time",
        translation_key="keep_warm_time",
        siid=3,
        piid=1,
        native_min_value=60,
        native_max_value=1440,
        native_step=30,
        native_unit_of_measurement="min",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(KettleNumber(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleNumber(KettleEntity, NumberEntity):
    entity_description: KettleNumberDescription

    def __init__(self, coordinator, description):
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_property(
            self.entity_description.siid, self.entity_description.piid, int(value)
        )
