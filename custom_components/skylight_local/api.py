"""HTTP client and runtime controller for Skylight lamp."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import re
import time

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEFAULT_POWER, MODE_AUTO, MODE_DEMO, MODE_MANUAL, MODE_OFF
from .presets import PRESETS

_LOGGER = logging.getLogger(__name__)
_COLOR_CODE_TO_PRESET = {
    int(match.group(1)): preset
    for preset, command in PRESETS.items()
    if (match := re.search(r"k(\d+)l", command)) is not None
}
_PRESET_CONTROL_PATTERN = re.compile(
    r"^74"
    r"(?P<ch0>-?\d+(?:\.\d+)?)h"
    r"(?P<ch1>-?\d+(?:\.\d+)?)i"
    r"(?P<ch2>-?\d+(?:\.\d+)?)j"
    r"(?P<ch3>-?\d+(?:\.\d+)?)k"
    r"(?P<color>\d+)l"
    r"-?\d+(?:\.\d+)?m$"
)


@dataclass
class SkylightStatus:
    """Normalized status parsed from /statusPage."""

    name: str | None = None
    model: str | None = None
    mac: str | None = None
    is_master: bool | None = None
    master_mac: str | None = None
    clone_count: int | None = None
    sntp_enabled: bool | None = None
    date: str | None = None
    time: str | None = None
    pwm_freq: int | None = None
    pwm0: float | None = None
    pwm1: float | None = None
    pwm2: float | None = None
    pwm3: float | None = None
    manual_intensity: float | None = None
    manual_color: float | None = None
    calib_pwm: int | None = None
    night_mode_enabled: bool | None = None
    schedule_enabled: bool | None = None
    schedule_items_count: int | None = None
    schedule_active_item_idx: int | None = None


class SkylightHttpClient:
    """Minimal HTTP client for lamp commands."""

    def __init__(self, hass: HomeAssistant, lamp_ip: str) -> None:
        self._session = async_get_clientsession(hass)
        self._schedule_url = f"http://{lamp_ip}/scheduleSettings"
        self._status_url = f"http://{lamp_ip}/statusPage"

    async def _get(self, url: str, params: dict[str, str] | None = None) -> str:
        try:
            response = await self._session.get(url, params=params, timeout=15)
            if response.status >= 400:
                text = await response.text()
                raise HomeAssistantError(f"Lamp returned HTTP {response.status}: {text}")
            return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HomeAssistantError(f"Cannot connect to lamp: {err}") from err

    async def send_params(self, value: str) -> None:
        """Send /scheduleSettings?params=<value>."""
        await self._get(self._schedule_url, {"params": value})

    async def set_manual_mode(self) -> None:
        """Disable AUTO mode before sending manual controls."""
        await self.send_params("9")

    async def set_off_mode(self) -> None:
        """Turn lamp off (AUTO mode OFF)."""
        await self.send_params("9")

    async def set_auto_mode(self) -> None:
        """Turn lamp on in automatic schedule mode."""
        await self.send_params("a")

    async def set_demo_mode(self) -> None:
        """Enable lamp demo mode."""
        await self.send_params("c")

    async def send_ctrl(self, ctrl_value: str) -> None:
        """Send raw ctrl command value."""
        await self._get(self._schedule_url, {"ctrl": ctrl_value})

    async def get_firmware_version(self) -> str:
        """Read firmware version from diagnostics endpoint."""
        try:
            return (await self._get(self._schedule_url, {"params": "n1"})).strip()
        except HomeAssistantError:
            return (await self._get(self._schedule_url, {"params": "n"})).strip()

    async def get_status_page(self) -> str:
        """Fetch full lamp status."""
        return await self._get(self._status_url)

    async def set_channel_pwm(self, channel: int, value: float) -> None:
        """Set one LED PWM channel (0..3) in percent."""
        if channel < 0 or channel > 3:
            raise HomeAssistantError(f"Invalid channel: {channel}")
        await self.send_ctrl(f"7{channel}{value:g}")

    async def set_all_channels(
        self,
        ch0: float,
        ch1: float,
        ch2: float,
        ch3: float,
        color_code: int,
        intensity: float,
    ) -> None:
        """Set all channels with color code and global intensity."""
        payload = f"74{ch0:g}h{ch1:g}i{ch2:g}j{ch3:g}k{color_code}l{intensity:g}m"
        await self.send_ctrl(payload)

    async def set_pwm_frequency(self, hz: int) -> None:
        await self.send_ctrl(f"75{hz}")

    async def get_pwm_frequency(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "76"})).strip()

    async def init_pwm(self) -> None:
        await self.send_ctrl("78")

    async def rtc_sync(self) -> None:
        await self.send_ctrl("6")

    async def set_timezone(self, value: str) -> None:
        await self.send_ctrl(f"b{value}")

    async def add_clone_mac(self, mac_no_sep: str) -> None:
        await self.send_params(f"k{mac_no_sep}")

    async def remove_clone_mac(self, mac_no_sep: str) -> None:
        await self.send_params(f"l{mac_no_sep}")

    async def clear_master_and_clone(self) -> None:
        await self.send_params("j")

    async def set_clone_mode(self) -> None:
        await self.send_params("i")

    async def clear_schedule(self) -> None:
        await self.send_params("4")

    async def save_schedule(self) -> None:
        await self.send_params("6")

    async def start_old_schedule_transfer(self, count: int) -> None:
        await self.send_params(f"7_{count}")

    async def old_schedule_payload(self, payload: str) -> None:
        await self.send_params(f"g_{payload}")

    async def start_safe_schedule_transfer(self, count: int) -> None:
        await self.send_params(f"p_{count}")

    async def safe_schedule_payload(self, payload: str) -> None:
        await self.send_params(f"s_{payload}")

    async def start_new_schedule(self) -> None:
        await self.send_params("r")

    async def read_description(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "g0"})).strip()

    async def read_led_status(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "g2"})).strip()

    async def read_schedule_status(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "g30"})).strip()

    async def read_schedule_string(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "g31"})).strip()

    async def read_status_g8(self) -> str:
        return (await self._get(self._schedule_url, {"ctrl": "g8"})).strip()

    async def set_night_mode(self, enabled: bool) -> None:
        await self.send_ctrl("gt01" if enabled else "gt00")

    async def manual_mode_1h(self) -> None:
        await self.send_ctrl("gu1")

    async def manual_mode_default(self) -> None:
        await self.send_ctrl("gu3")

    async def send_raw(self, *, params: str | None = None, ctrl: str | None = None) -> str:
        """Send raw params/ctrl command and return raw response."""
        if bool(params) == bool(ctrl):
            raise HomeAssistantError("Provide exactly one of params or ctrl")
        if params:
            return await self._get(self._schedule_url, {"params": params})
        return await self._get(self._schedule_url, {"ctrl": ctrl})


def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None and value != "" else None
    except ValueError:
        return None


def _to_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None and value != "" else None
    except ValueError:
        return None


def _raw_pwm_to_percent(value: str | None) -> float | None:
    raw = _to_float(value)
    if raw is None:
        return None
    return round(max(0.0, min(100.0, raw * 100.0 / 255.0)), 1)


def _decode_hex_text(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) % 2 != 0:
        return value
    try:
        return bytes.fromhex(value).decode("ascii", errors="ignore").strip("\x00")
    except ValueError:
        return value


def parse_status_page(raw: str) -> SkylightStatus:
    """Parse /statusPage response into a structured object."""
    status = SkylightStatus()
    lines = [line for line in raw.splitlines() if line != ""]

    if len(lines) > 0:
        parts = lines[0].split("\t")
        status.name = _decode_hex_text(parts[0]) if len(parts) > 0 else None
        status.model = _decode_hex_text(parts[1]) if len(parts) > 1 else None
        status.mac = parts[2] if len(parts) > 2 and parts[2] else None
        status.is_master = (parts[3] == "1") if len(parts) > 3 and parts[3] != "" else None
        status.master_mac = parts[4] if len(parts) > 4 and parts[4] else None
        status.clone_count = _to_int(parts[5]) if len(parts) > 5 else None

    if len(lines) > 1:
        parts = lines[1].split("\t")
        status.sntp_enabled = (parts[0] == "1") if len(parts) > 0 and parts[0] != "" else None
        status.date = parts[1] if len(parts) > 1 and parts[1] else None
        status.time = parts[2] if len(parts) > 2 and parts[2] else None

    if len(lines) > 2:
        parts = lines[2].split("\t")
        status.pwm_freq = _to_int(parts[0]) if len(parts) > 0 else None
        status.pwm0 = _raw_pwm_to_percent(parts[1]) if len(parts) > 1 else None
        status.pwm1 = _raw_pwm_to_percent(parts[2]) if len(parts) > 2 else None
        status.pwm2 = _raw_pwm_to_percent(parts[3]) if len(parts) > 3 else None
        status.pwm3 = _raw_pwm_to_percent(parts[4]) if len(parts) > 4 else None
        status.manual_intensity = _to_float(parts[5]) if len(parts) > 5 else None
        status.manual_color = _to_float(parts[6]) if len(parts) > 6 else None
        status.calib_pwm = _to_int(parts[7]) if len(parts) > 7 else None
        status.night_mode_enabled = (parts[8] == "1") if len(parts) > 8 and parts[8] != "" else None

    if len(lines) > 3:
        parts = lines[3].split("\t")
        status.schedule_enabled = (parts[0] == "1") if len(parts) > 0 and parts[0] != "" else None
        status.schedule_items_count = _to_int(parts[1]) if len(parts) > 1 else None
        status.schedule_active_item_idx = _to_int(parts[2]) if len(parts) > 2 else None

    return status


class SkylightController:
    """Shared state and commands for entities."""

    def __init__(self, client: SkylightHttpClient) -> None:
        self._client = client
        self._refresh_lock = asyncio.Lock()
        self._command_lock = asyncio.Lock()
        self._last_refresh_monotonic = 0.0
        self.selected_preset = "A1"
        self.power = DEFAULT_POWER
        self.firmware_version: str | None = None
        self.status: SkylightStatus | None = None
        self.is_auto_mode = False
        self.mode = MODE_OFF
        self.lamp_is_on: bool | None = None
        self.last_raw_response: str | None = None

    def set_power(self, power: int) -> None:
        """Store output power percentage (0-100)."""
        self.power = max(0, min(100, power))

    async def set_power_and_apply(self, power: int) -> None:
        """Update power and apply currently selected preset immediately."""
        async with self._command_lock:
            self.set_power(power)
            await self._apply_preset(self.selected_preset)

    def _ctrl_with_power(self, preset: str) -> str:
        base = PRESETS[preset]
        match = _PRESET_CONTROL_PATTERN.fullmatch(base)
        if match is None:
            raise HomeAssistantError(f"Preset {preset} has unexpected ctrl format: {base}")

        # Preset PWM values are encoded against the app's 30% reference level
        # (the stock commands end in l30m). Convert that reference to the
        # requested 0-100% output so HA's 100% reaches the app's full range.
        scale = self.power / 30.0

        def format_channel(name: str) -> str:
            value = min(100.0, float(match.group(name)) * scale)
            return f"{value:.2f}".rstrip("0").rstrip(".") or "0"

        return (
            f"74{format_channel('ch0')}h{format_channel('ch1')}i"
            f"{format_channel('ch2')}j{format_channel('ch3')}k"
            f"{match.group('color')}l{self.power}m"
        )

    async def apply_preset(self, preset: str | None = None) -> None:
        """Apply preset after switching lamp to manual mode."""
        target_preset = preset or self.selected_preset
        if target_preset not in PRESETS:
            raise HomeAssistantError(f"Unknown preset: {target_preset}")

        async with self._command_lock:
            await self._apply_preset(target_preset)

    async def _apply_preset(self, target_preset: str) -> None:
        """Send one complete preset update without interleaving another slider call."""

        ctrl = self._ctrl_with_power(target_preset)
        entering_manual = self.mode != MODE_MANUAL
        if entering_manual:
            await self._client.set_manual_mode()
        await self._client.send_ctrl(ctrl)
        # The mode transition makes the lamp blink. Do it only when entering
        # manual mode; repeated power adjustments should update PWM channels only.
        if entering_manual:
            await self._client.manual_mode_1h()
        self.selected_preset = target_preset
        self.is_auto_mode = False
        self.mode = MODE_MANUAL
        self.lamp_is_on = self.power > 0

    async def set_auto_mode(self) -> None:
        """Switch lamp to automatic schedule mode."""
        await self._client.set_auto_mode()
        self.is_auto_mode = True
        self.mode = MODE_AUTO
        self.lamp_is_on = True

    async def set_off_mode(self) -> None:
        """Turn lamp off by disabling AUTO mode."""
        await self._client.set_off_mode()
        self.is_auto_mode = False
        self.mode = MODE_OFF
        self.lamp_is_on = False

    async def set_demo_mode(self) -> None:
        """Enable demo mode."""
        await self._client.set_demo_mode()
        self.is_auto_mode = False
        self.mode = MODE_DEMO
        self.lamp_is_on = True

    async def set_mode(self, mode: str) -> None:
        if mode == MODE_AUTO:
            await self.set_auto_mode()
        elif mode == MODE_OFF:
            await self.set_off_mode()
        elif mode == MODE_DEMO:
            await self.set_demo_mode()
        elif mode == MODE_MANUAL:
            await self.apply_preset()
        else:
            raise HomeAssistantError(f"Unsupported mode: {mode}")

    async def set_channel_pwm(self, channel: int, value: float) -> None:
        await self._client.set_channel_pwm(channel, value)
        self.mode = MODE_MANUAL
        self.is_auto_mode = False
        if value > 0:
            self.lamp_is_on = True

    async def set_all_channels(
        self,
        ch0: float,
        ch1: float,
        ch2: float,
        ch3: float,
        color_code: int,
        intensity: float,
    ) -> None:
        await self._client.set_all_channels(ch0, ch1, ch2, ch3, color_code, intensity)
        self.mode = MODE_MANUAL
        self.is_auto_mode = False
        self.lamp_is_on = intensity > 0 and any(value > 0 for value in (ch0, ch1, ch2, ch3))

    async def set_pwm_frequency(self, hz: int) -> None:
        await self._client.set_pwm_frequency(hz)

    async def init_pwm(self) -> None:
        await self._client.init_pwm()

    async def rtc_sync(self) -> None:
        await self._client.rtc_sync()

    async def set_timezone(self, value: str) -> None:
        await self._client.set_timezone(value)

    async def clear_schedule(self) -> None:
        await self._client.clear_schedule()

    async def save_schedule(self) -> None:
        await self._client.save_schedule()

    async def start_old_schedule_transfer(self, count: int) -> None:
        await self._client.start_old_schedule_transfer(count)

    async def old_schedule_payload(self, payload: str) -> None:
        await self._client.old_schedule_payload(payload)

    async def start_safe_schedule_transfer(self, count: int) -> None:
        await self._client.start_safe_schedule_transfer(count)

    async def safe_schedule_payload(self, payload: str) -> None:
        await self._client.safe_schedule_payload(payload)

    async def start_new_schedule(self) -> None:
        await self._client.start_new_schedule()
        self.mode = MODE_AUTO
        self.is_auto_mode = True

    async def add_clone_mac(self, mac_no_sep: str) -> None:
        await self._client.add_clone_mac(mac_no_sep)

    async def remove_clone_mac(self, mac_no_sep: str) -> None:
        await self._client.remove_clone_mac(mac_no_sep)

    async def clear_master_and_clone(self) -> None:
        await self._client.clear_master_and_clone()

    async def set_clone_mode(self) -> None:
        await self._client.set_clone_mode()

    async def set_night_mode(self, enabled: bool) -> None:
        await self._client.set_night_mode(enabled)

    async def manual_mode_1h(self) -> None:
        await self._client.manual_mode_1h()
        self.mode = MODE_MANUAL
        self.is_auto_mode = False
        self.lamp_is_on = True

    async def manual_mode_default(self) -> None:
        await self._client.manual_mode_default()
        self.mode = MODE_MANUAL
        self.is_auto_mode = False
        self.lamp_is_on = True

    async def send_raw(self, *, params: str | None = None, ctrl: str | None = None) -> str:
        response = await self._client.send_raw(params=params, ctrl=ctrl)
        self.last_raw_response = response.strip() if response else ""
        return response

    async def get_pwm_frequency(self) -> str:
        response = await self._client.get_pwm_frequency()
        self.last_raw_response = response
        return response

    async def read_description(self) -> str:
        response = await self._client.read_description()
        self.last_raw_response = response
        return response

    async def read_led_status(self) -> str:
        response = await self._client.read_led_status()
        self.last_raw_response = response
        return response

    async def read_schedule_status(self) -> str:
        response = await self._client.read_schedule_status()
        self.last_raw_response = response
        return response

    async def read_schedule_string(self) -> str:
        response = await self._client.read_schedule_string()
        self.last_raw_response = response
        return response

    async def read_status_g8(self) -> str:
        response = await self._client.read_status_g8()
        self.last_raw_response = response
        return response

    async def refresh_diagnostics(self) -> None:
        """Fetch diagnostic data from lamp."""
        async with self._refresh_lock:
            now = time.monotonic()
            if now - self._last_refresh_monotonic < 1.0:
                return

            self.firmware_version = await self._client.get_firmware_version()
            status_raw = await self._client.get_status_page()
            self.status = parse_status_page(status_raw)
            if self.status.manual_color is not None:
                color_code = int(self.status.manual_color)
                if preset := _COLOR_CODE_TO_PRESET.get(color_code):
                    self.selected_preset = preset
            if self.status.schedule_enabled:
                self.lamp_is_on = True
            elif self.status.manual_intensity is not None:
                channel_values = (self.status.pwm0, self.status.pwm1, self.status.pwm2, self.status.pwm3)
                if all(value is not None for value in channel_values):
                    self.lamp_is_on = any(value > 0 for value in channel_values if value is not None)
                else:
                    self.lamp_is_on = self.status.manual_intensity > 0
            if self.status.schedule_enabled is not None:
                self.is_auto_mode = self.status.schedule_enabled
                if self.is_auto_mode:
                    self.mode = MODE_AUTO
                else:
                    channel_values = (self.status.pwm0, self.status.pwm1, self.status.pwm2, self.status.pwm3)
                    has_output = any(value > 0 for value in channel_values if value is not None)
                    if has_output or (self.status.manual_intensity or 0) > 0:
                        # A demo is still distinguishable only while this
                        # controller has seen the command; after a restart,
                        # report the observable lamp state as manual.
                        if self.mode != MODE_DEMO:
                            self.mode = MODE_MANUAL
                    else:
                        self.mode = MODE_OFF
            self._last_refresh_monotonic = time.monotonic()
