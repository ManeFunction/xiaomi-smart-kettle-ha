from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KettleCoordinator


class KettleEntity(CoordinatorEntity[KettleCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: KettleCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        uid = coordinator.mac or coordinator.host
        self._attr_unique_id = f"{uid}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        uid = self.coordinator.mac or self.coordinator.host
        return DeviceInfo(
            identifiers={(DOMAIN, uid)},
            name="Xiaomi Smart Kettle 2 Pro",
            manufacturer="Xiaomi",
            model="Xiaomi Smart Kettle 2 Pro (xiaomi.kettle.v20)",
        )
