"""Number platform for Skylight Local."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
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
    """Set up number entities for one config entry."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities(
        [
            SkylightPowerNumber(entry, controller),
            SkylightChannelPwmNumber(entry, controller, 0),
            SkylightChannelPwmNumber(entry, controller, 1),
            SkylightChannelPwmNumber(entry, controller, 2),
            SkylightChannelPwmNumber(entry, controller, 3),
        ],
        update_before_add=False,
    )


class SkylightPowerNumber(SkylightEntity, NumberEntity):
    """Output power percentage for preset commands."""

    _attr_name = "Power"
    _attr_icon = "mdi:brightness-percent"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_power"

    @property
    def native_value(self) -> float:
        return float(self._controller.power)

    async def async_set_native_value(self, value: float) -> None:
        await self._controller.set_power_and_apply(int(value))
        self.async_write_ha_state()


class SkylightChannelPwmNumber(SkylightEntity, NumberEntity):
    """Slider for one LED PWM channel."""

    _attr_icon = "mdi:chart-bell-curve-cumulative"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = "%"
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry, controller: SkylightController, channel: int) -> None:
        super().__init__(entry, controller)
        self._channel = channel
        self._last_value: float | None = None
        self._attr_name = f"Channel {channel}"
        self._attr_unique_id = f"{entry.entry_id}_pwm_channel_{channel}"

    @property
    def native_value(self) -> float | None:
        status = self._controller.status
        if status is not None:
            current = getattr(status, f"pwm{self._channel}", None)
            if current is not None:
                return float(current)
        return self._last_value

    async def async_set_native_value(self, value: float) -> None:
        numeric = float(value)
        await self._controller.set_channel_pwm(self._channel, numeric)
        if self._controller.status is not None:
            setattr(self._controller.status, f"pwm{self._channel}", numeric)
        self._last_value = numeric
        self.async_write_ha_state()
