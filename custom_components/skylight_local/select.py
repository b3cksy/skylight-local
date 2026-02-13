"""Select platform for Skylight Local."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SkylightController
from .const import DATA_CONTROLLER, DOMAIN
from .const import MODE_AUTO, MODE_DEMO, MODE_MANUAL, MODE_OFF
from .entity import SkylightEntity
from .presets import PRESET_OPTIONS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities for one config entry."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities(
        [
            SkylightPresetSelect(entry, controller),
            SkylightModeSelect(entry, controller),
        ],
        update_before_add=False,
    )


class SkylightPresetSelect(SkylightEntity, SelectEntity):
    """Preset selector. Selecting option applies preset immediately."""

    _attr_name = "Preset"
    _attr_icon = "mdi:palette"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_preset"
        self._attr_options = PRESET_OPTIONS

    @property
    def current_option(self) -> str:
        return self._controller.selected_preset

    async def async_select_option(self, option: str) -> None:
        await self._controller.apply_preset(option)
        self.async_write_ha_state()


class SkylightModeSelect(SkylightEntity, SelectEntity):
    """Lamp mode selector."""

    _attr_name = "Mode"
    _attr_icon = "mdi:lightbulb-auto"
    _attr_options = [MODE_OFF, MODE_AUTO, MODE_MANUAL, MODE_DEMO]

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_mode"

    @property
    def current_option(self) -> str:
        return self._controller.mode

    async def async_select_option(self, option: str) -> None:
        await self._controller.set_mode(option)
        self.async_write_ha_state()
