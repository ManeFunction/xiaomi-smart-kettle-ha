from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityDescription,
    WaterHeaterEntityFeature,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    STATE_OFF,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity
from .protocol import HEAT_TEMPERATURE_MAX, HEAT_TEMPERATURE_MIN, STATUSES

# The kettle itself, named after the device. Home Assistant's HomeKit bridge
# exposes a water heater as a thermostat: on is Heat, off is Stop, and the
# target is the heat temperature.
DESCRIPTION = WaterHeaterEntityDescription(
    key="kettle", translation_key="kettle", name=None, icon="mdi:kettle"
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([KettleWaterHeater(entry.runtime_data, DESCRIPTION)])


class KettleWaterHeater(KettleEntity, WaterHeaterEntity):
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_WHOLE
    _attr_target_temperature_step = 1
    _attr_min_temp = HEAT_TEMPERATURE_MIN
    _attr_max_temp = HEAT_TEMPERATURE_MAX

    @property
    def current_operation(self) -> str | None:
        """Return the kettle status, with standby as off.

        The HomeKit bridge shows the kettle as Off only for the "off" state, so
        heating, boiling, cooling down and keeping warm all show as Heat.
        """
        status = STATUSES.get(self.coordinator.data.get("status"))
        return STATE_OFF if status == "standby" else status

    @property
    def current_temperature(self) -> float | None:
        return self.coordinator.data.get("temperature")

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.heat_target

    async def async_set_temperature(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_heat_target(round(kwargs[ATTR_TEMPERATURE]))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_start_heat()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_stop()
