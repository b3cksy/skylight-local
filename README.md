# Skylight Local

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.1.0-blue.svg)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Unofficial Home Assistant integration for Skylight lamps over local HTTP API (`/scheduleSettings`, `/statusPage`).

## Supported Lamps

| Manufacturer | Model | Supported |
| --- | --- | --- |
| Hyperbar | H-BAR-FM | Yes |

## Features

- Local control (no WiFi dependency).
- Config Flow setup in Home Assistant UI (IP + optional name).
- Preset selection (`A1`..`F10`) with adjustable output power.
- Manual PWM channel control for channels `0..3`.
- Extended diagnostic and maintenance services.

## Installation

### Quick HACS Install

[![Open your Home Assistant instance and show the add custom repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=b3cksy&repository=skylight-local&category=integration)

If the button does not work, follow the manual HACS steps below.

### Option 1: HACS (recommended)

1. Open HACS in Home Assistant.
2. Add this repository as a custom repository (type: `Integration`).
3. Install **Skylight Local**.
4. Restart Home Assistant.

### Option 2: Manual

1. Copy `custom_components/skylight_local` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant go to **Settings -> Devices & Services -> Add Integration**.
2. Search for **Skylight Local**.
3. Enter:
   - `lamp_ip` (required)
   - `name` (optional)

Each configured lamp creates one config entry and one controller instance.

## Entities

### Select

- `Preset` (`A1`..`F10`)
- `Mode` (`off`, `auto`, `manual`, `demo`)

### Number

- `Power` (0-100%)
- `Channel 0` (0-100%)
- `Channel 1` (0-100%)
- `Channel 2` (0-100%)
- `Channel 3` (0-100%)

### Button

- `Auto mode`
- `Off`
- `Demo mode`

### Switch

- `Auto`

### Sensors

- `Firmware version`
- `Status`
- `Device name`
- `Device model`
- `MAC`
- `Master MAC`
- `PWM frequency`
- `PWM channel 0`
- `PWM channel 1`
- `PWM channel 2`
- `PWM channel 3`
- `Manual intensity`
- `Manual color`
- `Calibration PWM`
- `Schedule items count`
- `Is master`
- `Night mode enabled`
- `Schedule`

## Services

The integration registers services in `skylight_local.*`.

Main control services:

- `set_channel`
- `set_all_channels`
- `set_pwm_frequency`
- `init_pwm`
- `sync_rtc`
- `set_timezone`
- `set_night_mode`
- `manual_mode_1h`
- `manual_mode_default`

Schedule services:

- `clear_schedule`
- `save_schedule`
- `start_old_schedule`
- `send_old_schedule_payload`
- `start_safe_schedule`
- `send_safe_schedule_payload`
- `start_new_schedule`

Clone services:

- `add_clone`
- `remove_clone`
- `set_clone_mode`
- `clear_master_clone`

Diagnostics/raw services:

- `send_raw_command`
- `read_pwm_frequency`
- `read_description`
- `read_led_status`
- `read_schedule_status`
- `read_schedule_string`
- `read_info_g8`

For full field definitions see: `custom_components/skylight_local/services.yaml`.

## Example Service Call

```yaml
service: skylight_local.set_channel
data:
  entry_id: YOUR_ENTRY_ID
  channel: 0
  value: 35.5
```

## Notes and Limitations

- This is an unofficial project.
- Commands are sent directly to the lamp over HTTP.
- Connection failures and HTTP errors are surfaced as Home Assistant errors.
- `send_raw_command` requires exactly one of: `params` or `ctrl`.

## Troubleshooting

- Confirm the lamp IP is reachable from Home Assistant host.
- Verify lamp local API endpoints respond:
  - `http://<lamp_ip>/statusPage`
- If an entity appears stale, trigger an update or call one diagnostic read service.

## Disclaimer

This project is provided "as is", without any warranty of any kind, express or implied.

By using this integration, you accept full responsibility for configuration, operation, and any outcomes on your Home Assistant instance, network, lamp hardware, or data.

The author and contributors are not liable for any direct, indirect, incidental, special, exemplary, or consequential damages, including but not limited to device malfunction, data loss, downtime, misconfiguration, or any other issues resulting from installation or use.

Use at your own risk.

## License

MIT (see `LICENSE`).







