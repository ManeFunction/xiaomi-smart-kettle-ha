from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity

HEAT_TARGET = NumberEntityDescription(
    key="target_temperature",
    translation_key="target_temperature",
    native_min_value=40,
    native_max_value=99,
    native_step=1,
    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
)

DESCRIPTIONS = [
    NumberEntityDescription(
        key="keep_warm_temperature",
        translation_key="keep_warm_temperature",
        native_min_value=40,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
    NumberEntityDescription(
        key="keep_warm_time",
        translation_key="keep_warm_time",
        native_min_value=60,
        native_max_value=1440,
        native_step=30,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            KettleHeatTargetNumber(coordinator, HEAT_TARGET),
            *(KettleNumber(coordinator, d) for d in DESCRIPTIONS),
        ]
    )


class KettleNumber(KettleEntity, NumberEntity):
    entity_description: NumberEntityDescription

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_properties(
            {self.entity_description.key: int(value)}
        )


class KettleHeatTargetNumber(KettleNumber):
    """The heat temperature, which keeps the heat target while the kettle boils."""

    @property
    def native_value(self) -> float | None:
        return self.coordinator.heat_target

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_heat_target(int(value))
