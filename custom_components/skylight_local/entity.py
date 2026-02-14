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
        self._entry_id = entry.entry_id
        self._entry_title = entry.title
        self._lamp_ip = entry.data.get(CONF_LAMP_IP, entry.data.get("host", "0.0.0.0"))

    @property
    def device_info(self) -> DeviceInfo:
        """Build dynamic device info from the latest controller status."""
        model = self._controller.status.model if self._controller.status else None
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._entry_title,
            manufacturer="Skylight",
            model=model,
            configuration_url=f"http://{self._lamp_ip}",
        )
