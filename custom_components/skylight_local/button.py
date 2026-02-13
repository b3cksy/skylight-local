"""Button platform for Skylight Local."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Set up button entities for one config entry."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities(
        [
            SkylightAutoModeButton(entry, controller),
            SkylightOffModeButton(entry, controller),
            SkylightDemoModeButton(entry, controller),
        ],
        update_before_add=False,
    )


class SkylightAutoModeButton(SkylightEntity, ButtonEntity):
    """Switch lamp back to automatic schedule mode."""

    _attr_name = "Auto mode"
    _attr_icon = "mdi:calendar-sync-outline"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_auto_mode"

    async def async_press(self) -> None:
        await self._controller.set_auto_mode()


class SkylightOffModeButton(SkylightEntity, ButtonEntity):
    """Turn lamp off by disabling AUTO."""

    _attr_name = "Off"
    _attr_icon = "mdi:power"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_off_mode"

    async def async_press(self) -> None:
        await self._controller.set_off_mode()


class SkylightDemoModeButton(SkylightEntity, ButtonEntity):
    """Enable lamp demo mode."""

    _attr_name = "Demo mode"
    _attr_icon = "mdi:party-popper"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_demo_mode"

    async def async_press(self) -> None:
        await self._controller.set_demo_mode()
