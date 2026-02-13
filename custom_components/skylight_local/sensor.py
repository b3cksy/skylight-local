"""Sensor platform for Skylight Local."""
from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import SkylightController, SkylightStatus
from .const import DATA_CONTROLLER, DOMAIN
from .entity import SkylightEntity


StatusGetter = Callable[[SkylightController, SkylightStatus | None], str | int | float | None]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for one config entry."""
    controller: SkylightController = hass.data[DOMAIN][entry.entry_id][DATA_CONTROLLER]
    async_add_entities(
        [
            SkylightFirmwareVersionSensor(entry, controller),
            SkylightModeSensor(entry, controller),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="device_name",
                name="Device name",
                icon="mdi:tag-text-outline",
                getter=lambda c, s: None if s is None else s.name,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="device_model",
                name="Device model",
                icon="mdi:devices",
                getter=lambda c, s: None if s is None else s.model,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="mac",
                name="MAC",
                icon="mdi:identifier",
                getter=lambda c, s: None if s is None else s.mac,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="master_mac",
                name="Master MAC",
                icon="mdi:lan-connect",
                getter=lambda c, s: None if s is None else s.master_mac,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="pwm_freq",
                name="PWM frequency",
                icon="mdi:sine-wave",
                native_unit="Hz",
                getter=lambda c, s: None if s is None else s.pwm_freq,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="pwm0",
                name="PWM channel 0",
                icon="mdi:chart-bell-curve-cumulative",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.pwm0,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="pwm1",
                name="PWM channel 1",
                icon="mdi:chart-bell-curve-cumulative",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.pwm1,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="pwm2",
                name="PWM channel 2",
                icon="mdi:chart-bell-curve-cumulative",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.pwm2,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="pwm3",
                name="PWM channel 3",
                icon="mdi:chart-bell-curve-cumulative",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.pwm3,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="manual_intensity",
                name="Manual intensity",
                icon="mdi:brightness-percent",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.manual_intensity,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="manual_color",
                name="Manual color",
                icon="mdi:palette-outline",
                native_unit="%",
                getter=lambda c, s: None if s is None else s.manual_color,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="calib_pwm",
                name="Calibration PWM",
                icon="mdi:tune-variant",
                getter=lambda c, s: None if s is None else s.calib_pwm,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="schedule_items_count",
                name="Schedule items count",
                icon="mdi:format-list-numbered",
                getter=lambda c, s: None if s is None else s.schedule_items_count,
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="is_master",
                name="Is master",
                icon="mdi:account-star",
                getter=lambda c, s: _bool_to_text(None if s is None else s.is_master),
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="night_mode_enabled",
                name="Night mode enabled",
                icon="mdi:weather-night",
                getter=lambda c, s: _bool_to_text(None if s is None else s.night_mode_enabled),
            ),
            SkylightStatusAttributeSensor(
                entry,
                controller,
                key="schedule_enabled",
                name="Schedule",
                icon="mdi:calendar-check",
                getter=lambda c, s: _bool_to_text(None if s is None else s.schedule_enabled),
            ),
        ],
        update_before_add=True,
    )


def _bool_to_text(value: bool | None) -> str | None:
    if value is None:
        return None
    return "on" if value else "off"


class SkylightBaseDiagnosticSensor(SkylightEntity, SensorEntity):
    """Base diagnostic sensor for shared polling behavior."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_update(self) -> None:
        await self._controller.refresh_diagnostics()


class SkylightFirmwareVersionSensor(SkylightBaseDiagnosticSensor):
    """Firmware version sensor."""

    _attr_name = "Firmware version"
    _attr_icon = "mdi:information-outline"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_firmware_version"
        self._attr_native_value = None

    async def async_update(self) -> None:
        await super().async_update()
        self._attr_native_value = self._controller.firmware_version


class SkylightModeSensor(SkylightBaseDiagnosticSensor):
    """Current lamp mode sensor."""

    _attr_name = "Status"
    _attr_icon = "mdi:list-status"

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        super().__init__(entry, controller)
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_native_value = "unknown"

    async def async_update(self) -> None:
        await super().async_update()
        self._attr_native_value = self._controller.mode


class SkylightStatusAttributeSensor(SkylightBaseDiagnosticSensor):
    """Generic sensor for one /statusPage value."""

    def __init__(
        self,
        entry: ConfigEntry,
        controller: SkylightController,
        *,
        key: str,
        name: str,
        icon: str,
        getter: StatusGetter,
        native_unit: str | None = None,
    ) -> None:
        super().__init__(entry, controller)
        self._getter = getter
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        if native_unit is not None:
            self._attr_native_unit_of_measurement = native_unit
        self._attr_native_value = None

    async def async_update(self) -> None:
        await super().async_update()
        self._attr_native_value = self._getter(self._controller, self._controller.status)
