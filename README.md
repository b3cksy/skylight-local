# Skylight Local

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2026.11-blue.svg)](https://www.home-assistant.io/blog/2026/11/04/release-202611/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Skylight Local is an unofficial Home Assistant integration for controlling compatible Skylight lamps over their local HTTP API. It communicates directly with the lamp on your local network; no vendor cloud account is used. The integration is configured through Home Assistant's UI and creates entities for everyday control as well as diagnostics and maintenance.

HACS requires Home Assistant `2026.11.0` or newer. This is the minimum supported version declared by the integration metadata.

## Supported Lamps

| Manufacturer | Model | Supported |
| --- | --- | --- |
| Hyperbar / Skylight | H-BAR-FM | Supported |

Other Skylight models have not been verified and are not currently listed as supported.

## Features

- Local LAN control over HTTP; the lamp and Home Assistant must be able to reach each other on the network.
- UI setup with the lamp's IP address and an optional device name.
- A Home Assistant light entity with on/off, brightness, and 60 preset effects (`A1`..`F10`).
- Separate preset and mode selectors, plus buttons and a switch for Auto, Manual, Demo, and Off operation.
- Power control from 0–100% and direct PWM controls for channels `0`–`3`.
- Status and diagnostic sensors, plus services for schedules, clone/master configuration, maintenance, and raw commands.
- Read-only schedule snapshot for cards that visualize the schedule stored in the lamp.

## Installation

### Quick HACS Install

[![Open your Home Assistant instance and show the add custom repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=b3cksy&repository=skylight-local&category=integration)

If the button does not work, follow the manual HACS steps below.

### Option 1: HACS / Home Assistant Marketplace (recommended)

1. Open HACS (shown as Marketplace in newer Home Assistant releases).
2. If needed, add this repository as a custom repository with type `Integration`.
3. Install **Skylight Local** and restart Home Assistant.

### Option 2: Manual

1. Copy `custom_components/skylight_local` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Optional dashboard card

The Lovelace color-control card is maintained separately in the [Skylight Local Card repository](https://github.com/b3cksy/skylight-local-card). It requires this integration and uses its preset, power, and mode entities. See the card repository for installation and dashboard YAML configuration.

## Configuration

1. In Home Assistant go to **Settings -> Devices & Services -> Add Integration**.
2. Search for **Skylight Local**.
3. Enter:
   - `lamp_ip` (required)
   - `name` (optional)

Each configured lamp creates one config entry and one controller instance.

## Entities

### Light

- `Light`: turns the lamp on/off, sets brightness, and selects presets (`A1`..`F10`) through the effect list.
- Brightness and preset changes use the integration's manual preset control. The lamp's schedule is selected with the `Mode` entity or `Auto mode` button.

### Select

- `Preset` (`A1`..`F10`): applies the selected preset immediately.
- `Mode` (`off`, `auto`, `manual`, `demo`): selects the operating mode.

### Number

- `Power` (0-100%): applies the current preset at the chosen output level.
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
- `Schedule data` (read-only raw schedule snapshot for dashboard cards)
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
- Only the H-BAR-FM is currently listed as supported; other models need verification.
- Commands are sent directly to the lamp over the local network using HTTP.
- Preset selection and brightness control are provided by the integration's light entity.
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







