import math
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
    STATE_ON,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry
from .entity import KettleEntity
from .protocol import (
    HEAT_TEMPERATURE_MAX,
    HEAT_TEMPERATURE_MIN,
    KEEP_WARM_TEMPERATURE_MAX,
    KEEP_WARM_TEMPERATURE_MIN,
    STATUSES,
)

# Home Assistant's HomeKit bridge exposes a water heater as a thermostat with
# Heat and Off modes, which gives Apple Home a tile for each of these.

# The kettle itself, named after the device: on is Heat, off is Stop, and the
# target is the heat temperature.
HEAT = WaterHeaterEntityDescription(
    key="kettle", translation_key="kettle", name=None, icon="mdi:kettle"
)
# The keep-warm settings: on/off is the Keep warm switch, and the target is the
# keep-warm temperature.
KEEP_WARM = WaterHeaterEntityDescription(
    key="keep_warm", translation_key="keep_warm", icon="mdi:kettle-outline"
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            KettleHeatWaterHeater(coordinator, HEAT),
            KettleKeepWarmWaterHeater(coordinator, KEEP_WARM),
        ]
    )


class KettleWaterHeater(KettleEntity, WaterHeaterEntity):
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_precision = PRECISION_WHOLE
    _attr_target_temperature_step = 1


class KettleHeatWaterHeater(KettleWaterHeater):
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
        await self.coordinator.async_set_heat_target(_whole(kwargs[ATTR_TEMPERATURE]))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_start_heat()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_stop()


class KettleKeepWarmWaterHeater(KettleWaterHeater):
    _attr_min_temp = KEEP_WARM_TEMPERATURE_MIN
    _attr_max_temp = KEEP_WARM_TEMPERATURE_MAX

    @property
    def current_operation(self) -> str | None:
        keep_warm = self.coordinator.data.get("auto_keep_warm")
        if keep_warm is None:
            return None
        return STATE_ON if keep_warm else STATE_OFF

    @property
    def current_temperature(self) -> float | None:
        """Mirror the keep-warm temperature instead of the water temperature.

        A HomeKit thermostat always shows a current temperature, and the bridge
        shows a fixed 50 °C when there is none. Mirroring the target keeps this
        tile apart from the kettle's, which shows the water temperature.
        """
        return self.target_temperature

    @property
    def target_temperature(self) -> float | None:
        return self.coordinator.data.get("keep_warm_temperature")

    async def async_set_temperature(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_properties(
            {"keep_warm_temperature": _whole(kwargs[ATTR_TEMPERATURE])}
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_properties({"auto_keep_warm": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_properties({"auto_keep_warm": False})


def _whole(temperature: float) -> int:
    """Round to the whole degrees the kettle takes, halves up.

    The Home app's dial moves in half degrees, and round() would send 72.5 to 72
    but 73.5 to 74.
    """
    return math.floor(temperature + 0.5)
