"""Shared entity helpers for Skylight Local."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .api import SkylightController
from .const import CONF_LAMP_IP, DOMAIN


class SkylightEntity(Entity):
    """Base entity that attaches all entities to one device card."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, controller: SkylightController) -> None:
        self._controller = controller
        lamp_ip = entry.data.get(CONF_LAMP_IP, entry.data.get("host", "0.0.0.0"))
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Skylight",
            model="Hyperbar",
            configuration_url=f"http://{lamp_ip}",
        )

