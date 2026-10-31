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
        self._attr_device_info = get_device_info(coordinator.zone)

    @property
    def available(self) -> bool:
        """Stored days stay usable even when the last JAKIM check failed."""
        return bool(self.coordinator.days)
