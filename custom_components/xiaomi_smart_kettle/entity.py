from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEVICE_NAME, DOMAIN
from .coordinator import KettleCoordinator
from .protocol import MODEL


class KettleEntity(CoordinatorEntity[KettleCoordinator]):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: KettleCoordinator, description: EntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        uid = coordinator.config_entry.unique_id
        self._attr_unique_id = f"{uid}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, uid)},
            name=DEVICE_NAME,
            manufacturer="Xiaomi",
            model=f"{DEVICE_NAME} ({MODEL})",
        )
