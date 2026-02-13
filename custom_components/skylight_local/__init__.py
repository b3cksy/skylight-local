from __future__ import annotations

import re

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.exceptions import HomeAssistantError
from homeassistant.core import ServiceCall

from .api import SkylightController, SkylightHttpClient
from .const import CONF_LAMP_IP, DATA_CONTROLLER, DOMAIN, PLATFORMS

SERVICE_SET_CHANNEL = "set_channel"
SERVICE_SET_ALL_CHANNELS = "set_all_channels"
SERVICE_SET_PWM_FREQUENCY = "set_pwm_frequency"
SERVICE_INIT_PWM = "init_pwm"
SERVICE_RTC_SYNC = "sync_rtc"
SERVICE_SET_TIMEZONE = "set_timezone"
SERVICE_CLEAR_SCHEDULE = "clear_schedule"
SERVICE_SAVE_SCHEDULE = "save_schedule"
SERVICE_START_OLD_SCHEDULE = "start_old_schedule"
SERVICE_SEND_OLD_SCHEDULE_PAYLOAD = "send_old_schedule_payload"
SERVICE_START_SAFE_SCHEDULE = "start_safe_schedule"
SERVICE_SEND_SAFE_SCHEDULE_PAYLOAD = "send_safe_schedule_payload"
SERVICE_START_NEW_SCHEDULE = "start_new_schedule"
SERVICE_ADD_CLONE = "add_clone"
SERVICE_REMOVE_CLONE = "remove_clone"
SERVICE_SET_CLONE_MODE = "set_clone_mode"
SERVICE_CLEAR_MASTER_CLONE = "clear_master_clone"
SERVICE_SET_NIGHT_MODE = "set_night_mode"
SERVICE_MANUAL_MODE_1H = "manual_mode_1h"
SERVICE_MANUAL_MODE_DEFAULT = "manual_mode_default"
SERVICE_SEND_RAW = "send_raw_command"
SERVICE_READ_DESCRIPTION = "read_description"
SERVICE_READ_LED_STATUS = "read_led_status"
SERVICE_READ_SCHEDULE_STATUS = "read_schedule_status"
SERVICE_READ_SCHEDULE_STRING = "read_schedule_string"
SERVICE_READ_INFO_G8 = "read_info_g8"
SERVICE_READ_PWM_FREQUENCY = "read_pwm_frequency"

_MAC_RE = re.compile(r"^[0-9A-Fa-f]{12}$")

SERVICE_SET_CHANNEL_SCHEMA = vol.Schema(
    {
        vol.Required("channel"): vol.All(vol.Coerce(int), vol.Range(min=0, max=3)),
        vol.Required("value"): vol.Coerce(float),
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_SET_ALL_CHANNELS_SCHEMA = vol.Schema(
    {
        vol.Required("ch0"): vol.Coerce(float),
        vol.Required("ch1"): vol.Coerce(float),
        vol.Required("ch2"): vol.Coerce(float),
        vol.Required("ch3"): vol.Coerce(float),
        vol.Required("color_code"): vol.Coerce(int),
        vol.Required("intensity"): vol.Coerce(float),
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_SET_PWM_FREQUENCY_SCHEMA = vol.Schema(
    {
        vol.Required("hz"): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_ENTRY_ID_SCHEMA = vol.Schema({vol.Optional("entry_id"): cv.string})
SERVICE_PAYLOAD_SCHEMA = vol.Schema(
    {
        vol.Required("payload"): cv.string,
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_TIMEZONE_SCHEMA = vol.Schema(
    {
        vol.Required("timezone"): cv.string,
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_COUNT_SCHEMA = vol.Schema(
    {
        vol.Required("count"): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_MAC_SCHEMA = vol.Schema(
    {
        vol.Required("mac"): cv.string,
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_NIGHT_MODE_SCHEMA = vol.Schema(
    {
        vol.Required("enabled"): cv.boolean,
        vol.Optional("entry_id"): cv.string,
    }
)
SERVICE_SEND_RAW_SCHEMA = vol.Schema(
    {
        vol.Optional("params"): cv.string,
        vol.Optional("ctrl"): cv.string,
        vol.Optional("entry_id"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up component-level services."""
    async_register_services(hass)
    return True


def _normalize_mac(mac: str) -> str:
    value = mac.replace(":", "").replace("-", "")
    if not _MAC_RE.fullmatch(value):
        raise HomeAssistantError("MAC must contain exactly 12 hex characters")
    return value.upper()


def _iter_controllers(hass: HomeAssistant, entry_id: str | None = None) -> list[SkylightController]:
    domain_data = hass.data.get(DOMAIN, {})
    if entry_id:
        if entry_id not in domain_data:
            raise HomeAssistantError(f"Unknown entry_id: {entry_id}")
        return [domain_data[entry_id][DATA_CONTROLLER]]
    controllers = [data[DATA_CONTROLLER] for data in domain_data.values()]
    if not controllers:
        raise HomeAssistantError("No configured Skylight entries")
    return controllers


async def _for_each_controller(hass: HomeAssistant, call: ServiceCall, action) -> None:
    entry_id = call.data.get("entry_id")
    controllers = _iter_controllers(hass, entry_id)
    for controller in controllers:
        await action(controller)


def async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    if hass.services.has_service(DOMAIN, SERVICE_SET_CHANNEL):
        return

    async def handle_set_channel(call: ServiceCall) -> None:
        channel = call.data["channel"]
        value = call.data["value"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.set_channel_pwm(channel, value),
        )

    async def handle_set_all_channels(call: ServiceCall) -> None:
        ch0 = call.data["ch0"]
        ch1 = call.data["ch1"]
        ch2 = call.data["ch2"]
        ch3 = call.data["ch3"]
        color_code = call.data["color_code"]
        intensity = call.data["intensity"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.set_all_channels(ch0, ch1, ch2, ch3, color_code, intensity),
        )

    async def handle_set_pwm_frequency(call: ServiceCall) -> None:
        hz = call.data["hz"]
        await _for_each_controller(hass, call, lambda controller: controller.set_pwm_frequency(hz))

    async def handle_init_pwm(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.init_pwm())

    async def handle_rtc_sync(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.rtc_sync())

    async def handle_set_timezone(call: ServiceCall) -> None:
        timezone = call.data["timezone"]
        await _for_each_controller(hass, call, lambda controller: controller.set_timezone(timezone))

    async def handle_clear_schedule(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.clear_schedule())

    async def handle_save_schedule(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.save_schedule())

    async def handle_start_old_schedule(call: ServiceCall) -> None:
        count = call.data["count"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.start_old_schedule_transfer(count),
        )

    async def handle_send_old_schedule_payload(call: ServiceCall) -> None:
        payload = call.data["payload"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.old_schedule_payload(payload),
        )

    async def handle_start_safe_schedule(call: ServiceCall) -> None:
        count = call.data["count"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.start_safe_schedule_transfer(count),
        )

    async def handle_send_safe_schedule_payload(call: ServiceCall) -> None:
        payload = call.data["payload"]
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.safe_schedule_payload(payload),
        )

    async def handle_start_new_schedule(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.start_new_schedule())

    async def handle_add_clone(call: ServiceCall) -> None:
        mac = _normalize_mac(call.data["mac"])
        await _for_each_controller(hass, call, lambda controller: controller.add_clone_mac(mac))

    async def handle_remove_clone(call: ServiceCall) -> None:
        mac = _normalize_mac(call.data["mac"])
        await _for_each_controller(hass, call, lambda controller: controller.remove_clone_mac(mac))

    async def handle_set_clone_mode(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.set_clone_mode())

    async def handle_clear_master_clone(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.clear_master_and_clone())

    async def handle_set_night_mode(call: ServiceCall) -> None:
        enabled = call.data["enabled"]
        await _for_each_controller(hass, call, lambda controller: controller.set_night_mode(enabled))

    async def handle_manual_mode_1h(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.manual_mode_1h())

    async def handle_manual_mode_default(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.manual_mode_default())

    async def handle_send_raw(call: ServiceCall) -> None:
        params = call.data.get("params")
        ctrl = call.data.get("ctrl")
        if bool(params) == bool(ctrl):
            raise HomeAssistantError("Provide exactly one of params or ctrl")
        await _for_each_controller(
            hass,
            call,
            lambda controller: controller.send_raw(params=params, ctrl=ctrl),
        )

    async def handle_read_description(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.read_description())

    async def handle_read_led_status(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.read_led_status())

    async def handle_read_schedule_status(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.read_schedule_status())

    async def handle_read_schedule_string(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.read_schedule_string())

    async def handle_read_info_g8(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.read_status_g8())

    async def handle_read_pwm_frequency(call: ServiceCall) -> None:
        await _for_each_controller(hass, call, lambda controller: controller.get_pwm_frequency())

    hass.services.async_register(DOMAIN, SERVICE_SET_CHANNEL, handle_set_channel, schema=SERVICE_SET_CHANNEL_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_ALL_CHANNELS,
        handle_set_all_channels,
        schema=SERVICE_SET_ALL_CHANNELS_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_PWM_FREQUENCY,
        handle_set_pwm_frequency,
        schema=SERVICE_SET_PWM_FREQUENCY_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_INIT_PWM, handle_init_pwm, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_RTC_SYNC, handle_rtc_sync, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_TIMEZONE, handle_set_timezone, schema=SERVICE_TIMEZONE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_SCHEDULE, handle_clear_schedule, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SAVE_SCHEDULE, handle_save_schedule, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_START_OLD_SCHEDULE, handle_start_old_schedule, schema=SERVICE_COUNT_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_OLD_SCHEDULE_PAYLOAD,
        handle_send_old_schedule_payload,
        schema=SERVICE_PAYLOAD_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_START_SAFE_SCHEDULE, handle_start_safe_schedule, schema=SERVICE_COUNT_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SAFE_SCHEDULE_PAYLOAD,
        handle_send_safe_schedule_payload,
        schema=SERVICE_PAYLOAD_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_START_NEW_SCHEDULE, handle_start_new_schedule, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ADD_CLONE, handle_add_clone, schema=SERVICE_MAC_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_CLONE, handle_remove_clone, schema=SERVICE_MAC_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_CLONE_MODE, handle_set_clone_mode, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_MASTER_CLONE, handle_clear_master_clone, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_NIGHT_MODE, handle_set_night_mode, schema=SERVICE_NIGHT_MODE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_MANUAL_MODE_1H, handle_manual_mode_1h, schema=SERVICE_ENTRY_ID_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_MANUAL_MODE_DEFAULT,
        handle_manual_mode_default,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(DOMAIN, SERVICE_SEND_RAW, handle_send_raw, schema=SERVICE_SEND_RAW_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_DESCRIPTION,
        handle_read_description,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_LED_STATUS,
        handle_read_led_status,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_SCHEDULE_STATUS,
        handle_read_schedule_status,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_SCHEDULE_STRING,
        handle_read_schedule_string,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_INFO_G8,
        handle_read_info_g8,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_READ_PWM_FREQUENCY,
        handle_read_pwm_frequency,
        schema=SERVICE_ENTRY_ID_SCHEMA,
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    lamp_ip = entry.data.get(CONF_LAMP_IP, entry.data.get("host", "0.0.0.0"))
    controller = SkylightController(SkylightHttpClient(hass, lamp_ip))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_CONTROLLER: controller}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
