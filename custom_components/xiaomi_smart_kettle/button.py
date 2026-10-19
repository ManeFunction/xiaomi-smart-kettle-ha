from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import KettleConfigEntry, KettleCoordinator
from .entity import KettleEntity


@dataclass(frozen=True, kw_only=True)
class KettleButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[KettleCoordinator], Awaitable[None]]


DESCRIPTIONS = [
    KettleButtonDescription(
        key="heat",
        translation_key="heat",
        icon="mdi:kettle-steam",
        press_fn=KettleCoordinator.async_start_heat,
    ),
    KettleButtonDescription(
        key="boil",
        translation_key="boil",
        icon="mdi:kettle-steam",
        press_fn=KettleCoordinator.async_start_boil,
    ),
    KettleButtonDescription(
        key="stop",
        translation_key="stop",
        icon="mdi:stop-circle-outline",
        press_fn=KettleCoordinator.async_stop,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KettleConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(KettleButton(entry.runtime_data, d) for d in DESCRIPTIONS)


class KettleButton(KettleEntity, ButtonEntity):
    entity_description: KettleButtonDescription

    async def async_press(self) -> None:
        await self.entity_description.press_fn(self.coordinator)
