"""Switch platform for Skylight Local."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SkylightController
from .const import DATA_CONTROLLER, DOMAIN
from .entity import SkylightEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities for one config entry."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities([SkylightAutoSwitch(entry, controller)], update_before_add=False)


class SkylightAutoSwitch(SkylightEntity, SwitchEntity):
    """AUTO mode switch (ON=params=a, OFF=params=9)."""

    _attr_name = "Auto"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_auto_switch"

    @property
    def is_on(self) -> bool:
        return self._controller.is_auto_mode

    async def async_update(self) -> None:
        await self._controller.refresh_diagnostics()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._controller.set_auto_mode()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._controller.set_off_mode()
        self.async_write_ha_state()
