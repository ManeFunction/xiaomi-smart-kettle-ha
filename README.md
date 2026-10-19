# Xiaomi Smart Kettle 2 Pro for Home Assistant

**English** | [Русский](README.ru.md)

[![GitHub release](https://img.shields.io/github/v/release/username-andrey/xiaomi-smart-kettle-ha)](https://github.com/username-andrey/xiaomi-smart-kettle-ha/releases)
[![GitHub issues](https://img.shields.io/github/issues/username-andrey/xiaomi-smart-kettle-ha)](https://github.com/username-andrey/xiaomi-smart-kettle-ha/issues)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue)](https://www.hacs.xyz/)

**Xiaomi Smart Kettle 2 Pro** is a custom [Home Assistant](https://www.home-assistant.io/) integration that shows the state and settings of the Xiaomi Smart Kettle 2 Pro, model ID **`xiaomi.kettle.v20`**, and lets you control it over the local network.

> [!IMPORTANT]
> This is an unofficial project. It is not developed or supported by Xiaomi. It has been confirmed to work on one specific device; compatibility with other models and firmware versions is not guaranteed.

## Features

The integration reads the kettle's Xiaomi miIO properties and creates these entities:

| Entity | Description |
| --- | --- |
| Water temperature | Current temperature of the water |
| Heat temperature | Temperature that **Heat** heats to (40–99 °C) |
| Status | Standby, heating, boiling, cooling down or keeping warm |
| Fault | Diagnostic code reported by the kettle |
| Keep warm | Whether the kettle keeps the water warm afterwards |
| Keep-warm temperature | Temperature to keep the water at (40–90 °C) |
| Keep-warm time | How long to keep the water warm (60–1440 min) |
| Warming time | Warming time reported by the kettle |
| Kettle lifted | Whether the kettle is off its base |
| Other settings | Boiling and keep-warm notifications in the Mi Home app, remember temperature after lifting, do not disturb |
| Boil | Button that starts boiling |
| Heat | Button that heats the water to the heat temperature |
| Stop | Button that stops heating or boiling |

> [!NOTE]
> **The Boil and Heat buttons work** on the tested Xiaomi Smart Kettle 2 Pro. The exact set of entities and commands may depend on the integration version and the kettle's firmware.

## Compatibility

| Component | Tested configuration |
| --- | --- |
| Device | Xiaomi Smart Kettle 2 Pro |
| miIO model | `xiaomi.kettle.v20` |
| Firmware of the test device | `v2.2.7_0016` |
| Platform | Home Assistant, installed through HACS |
| Project version | The `v0.2` release was used during development |

Do not assume other kettle models, including `yunmi.kettle.*`, are compatible without testing them: their protocol and properties may differ.

## Requirements

- Home Assistant 2024.11 or newer, with custom integrations enabled.
- [HACS](https://www.hacs.xyz/) for the recommended installation method.
- A Xiaomi Smart Kettle 2 Pro (`xiaomi.kettle.v20`) connected to the local network.
- The kettle's IP address and a valid device token.
- Network access from the Home Assistant host to the kettle.

## Installation through HACS

1. Open **HACS** in Home Assistant.
2. From the menu, choose **Custom repositories**.
3. Add the repository:

   ```text
   https://github.com/username-andrey/xiaomi-smart-kettle-ha
   ```

4. Choose the **Integration** type.
5. Open the added repository and install the available version.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration** and search for Xiaomi Smart Kettle.
8. Follow the setup prompts.

> If the repository is already in HACS, you don't need to add it again. Field names may differ between releases.

## Manual installation

1. Get the source files from the [repository](https://github.com/username-andrey/xiaomi-smart-kettle-ha).
2. Copy the component folder from the repository's `custom_components/` into a folder of the same name inside Home Assistant's `/config/custom_components/`. Keep the folder structure.
3. Restart Home Assistant and add the integration under **Devices & services**.

Do not copy the whole repository into `custom_components`, and do not add an extra level of nesting.

## Usage

After setup, open the kettle device in Home Assistant. Its entities show the current and heat temperature, the status, the keep-warm settings and diagnostic information.

The **Boil**, **Heat** and **Stop** buttons start and stop those modes from Home Assistant. **Heat** heats the water to the heat temperature. Boiling does not change it, so the next **Heat** after a **Boil** heats to your setting again. Both buttons send the current keep-warm settings along with the command.

The buttons have been confirmed to work on the test device. Try them on your own kettle before using them in automations. Do not run the kettle unattended, and do not bypass its built-in safety mechanisms.

## Troubleshooting

### The kettle is unavailable

- Check that Home Assistant and the kettle can reach each other over the network.
- Make sure the kettle's IP address has not changed; reserve it in DHCP if needed.
- Check that the token is correct.
- Reload the integration and check the Home Assistant log.

### Temperature and status do not update

- Make sure the kettle responds on the network.
- Look for communication errors under **Settings → System → Logs**.
- Check that the device's model ID is `xiaomi.kettle.v20`.

### The Boil and Heat buttons do nothing

Both buttons work on the test device. If a command fails, Home Assistant shows the reason. Check the connection between Home Assistant and the kettle, the kettle's state, the water level and the integration log. Do not send commands repeatedly while the kettle reports a fault.

### Error `E2`

`E2` means **the water level in the kettle is low**. It was seen during a boiling test and does not by itself indicate a problem with the integration. If it appears, stop heating, let the kettle cool down if needed, and check the water level, following the MIN/MAX marks and the manufacturer's instructions.

## Security and privacy

- **Do not publish** private network IP addresses together with device tokens, passwords, logs containing secrets, or configuration files with credentials.
- Do not add real tokens to Git, issues or screenshots.
- Give access to Home Assistant only to trusted users.
- Back up before updating Home Assistant or the integration.
- Treat heating commands as potentially dangerous: they control an appliance that heats water.

## Updating and removal

To update, open the integration in **HACS**, install the available release and restart Home Assistant if asked. Back up before major updates.

To remove it, first delete the integration entry under **Settings → Devices & services**, then remove the component through **HACS**. After a manual installation, also delete only the component's folder from `/config/custom_components/`.

## Bug reports and suggestions

Open an issue in [GitHub Issues](https://github.com/username-andrey/xiaomi-smart-kettle-ha/issues). Include your Home Assistant version, the integration version, the kettle's model and firmware, steps to reproduce and an anonymized log excerpt. **Remove tokens and other secrets before posting.**

## Development

The tests use [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) and a fake kettle, so they need neither a real device nor a running Home Assistant:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements_test.txt
.venv/bin/ruff format --check . && .venv/bin/ruff check .
.venv/bin/pytest
```

Everything that depends on the kettle's MIoT spec, such as property addresses and command payloads, lives in `custom_components/xiaomi_smart_kettle/protocol.py`.

## Project status

The integration is under development. Reading the main values and the **Boil** and **Heat** buttons have been confirmed on the test device. Other firmware versions and models need separate testing.

## License

The project is licensed under the MIT License; see [`LICENSE`](LICENSE).

## Disclaimer

The project is provided "as is", without any guarantee of compatibility or uninterrupted operation. Xiaomi, Mi Home and Home Assistant are trademarks of their respective owners. This is an unofficial integration.
