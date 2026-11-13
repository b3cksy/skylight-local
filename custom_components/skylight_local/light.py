"""Light platform for Skylight Local."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SkylightController
from .const import DATA_CONTROLLER, DOMAIN, MODE_OFF
from .entity import SkylightEntity
from .presets import PRESET_OPTIONS, PRESETS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Skylight lamp entity."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities([SkylightLight(entry, controller)], update_before_add=True)


class SkylightLight(SkylightEntity, LightEntity):
    """Expose the lamp's preset color palette as light effects."""

    _attr_name = "Light"
    _attr_icon = "mdi:lightbulb"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_supported_features = LightEntityFeature.EFFECT
    _attr_effect_list = PRESET_OPTIONS

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_light"

    @property
    def is_on(self) -> bool:
        """Return on state from the last status read or last command."""
        if self._controller.lamp_is_on is not None:
            return self._controller.lamp_is_on
        return self._controller.mode != MODE_OFF

    @property
    def brightness(self) -> int | None:
        """Convert the lamp's 0-100% intensity to Home Assistant's 0-255."""
        intensity = self._controller.power
        return round(max(0.0, min(100.0, intensity)) * 255 / 100)

    @property
    def effect(self) -> str | None:
        """Return the currently selected preset color."""
        preset = self._controller.selected_preset
        return preset if preset in PRESETS else None

    async def async_update(self) -> None:
        """Refresh lamp status before reporting current light state."""
        await self._controller.refresh_diagnostics()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the lamp on with an optional preset and brightness."""
        effect = kwargs.get(ATTR_EFFECT)
        if isinstance(effect, str) and effect in PRESETS:
            target_preset = effect
        else:
            target_preset = self._controller.selected_preset

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if isinstance(brightness, (int, float)):
            self._controller.set_power(round(max(0, min(255, brightness)) * 100 / 255))

        await self._controller.apply_preset(target_preset)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the lamp off."""
        await self._controller.set_off_mode()
        self.async_write_ha_state()
