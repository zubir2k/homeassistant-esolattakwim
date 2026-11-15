"""Base entity for eSolat Takwim Malaysia."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import get_device_info
from .coordinator import TakwimCoordinator


class TakwimEntity(CoordinatorEntity[TakwimCoordinator]):
    """Shares the service device and the coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TakwimCoordinator) -> None:
        super().__init__(coordinator)
        entry_id = coordinator.config_entry.entry_id if coordinator.config_entry else coordinator.zone
        self._attr_device_info = get_device_info(entry_id, coordinator.zone)

    @property
    def available(self) -> bool:
        """Stored days stay usable even when the last JAKIM check failed."""
        return super().available and bool(self.coordinator.days)
