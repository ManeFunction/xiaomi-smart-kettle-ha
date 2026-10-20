# Changelog

All notable changes to this project are documented in this file. Commits follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), and the versions follow [Semantic Versioning](https://semver.org/).

## 0.3.0 (2026-10-19)

### Features

* **number:** remove the Keep-warm temperature number, which the keep-warm thermostat replaces; its entity is removed from the registry on existing installs
* **binary_sensor:** give "Kettle lifted" the opening device class with "Lifted" and "On base" states, so the HomeKit bridge exposes it as a contact sensor (open while lifted) instead of an occupancy sensor
* **water_heater:** add a Keep warm temperature water heater for the keep-warm settings: turning it on and off sets the Keep warm switch, its target is the keep-warm temperature (40–90 °C), and it shows that temperature instead of the water temperature, so its Apple Home tile differs from the kettle's
* **water_heater:** add a Kettle water heater entity for Home Assistant's water heater card and the HomeKit bridge: it shows the water temperature and status, its target is the heat temperature (40–99 °C), turning it on starts Heat and turning it off stops the kettle
* **sensor:** expose the kettle status as an enum sensor with translated states (standby, heating, boiling, cooling down, keeping warm)
* **switch:** move the remember-temperature, boiling notification, keep-warm notification and do-not-disturb switches to the device's Configuration section, which also keeps them off auto-generated dashboards and out of the HomeKit bridge by default

### Bug Fixes

* show the result of a change right away instead of after the next poll: a second change within 10 s used to wait for the debounced refresh, and the Home app's half-degree dial values now snap to the whole degree the kettle got (halves round up)
* **number:** rename "Target temperature" to "Heat temperature", since it is the temperature the Heat button heats to (entity IDs of existing installs are unchanged)
* **switch:** rename "Boiling reminder" and "Keep-warm reminder" to "Boiling notification" and "Keep-warm notification", which is what they control (entity IDs of existing installs are unchanged)
* keep the heat target when Boil runs, so the next Heat heats to the heat temperature instead of 99 °C and the heat temperature entity no longer jumps to 99
* re-read the keep-warm settings from the kettle right before Heat and Boil, and refuse to start instead of sending invented defaults when a setting is unknown
* raise readable, translated errors when a command fails because the kettle is unreachable or rejects it
* serialize requests to the kettle, so a poll and a command no longer collide on a message ID and time out
* show unreported values as unknown instead of off or the literal state `unknown_None`
* use `miio.Device` so python-miio no longer logs a mapping warning on every setup and config-flow submit
* **config_flow:** add a translated message for an already configured kettle

### Performance Improvements

* poll only the 15 properties the integration uses, in 3 round trips every 5 s instead of 7

### Code Refactoring

* move the MIoT protocol (property addresses, requests and the Heat/Boil/Stop commands) into `protocol.py`; entities address properties by name
* share entity setup in `KettleEntity` and describe the buttons the same way as the other platforms
* remove dead and duplicated constants
* type the config entry, entities and config flow

### Documentation

* add an English README and move the Russian one to `README.ru.md`
* correct the entity list, requirements and license in the README
* name the copyright holder in `LICENSE`

### Tests and CI

* add protocol, config flow, entity and translation tests that run against a fake kettle
* add a workflow that runs hassfest, HACS validation, ruff and pytest
* format the code with ruff

### Chores

* complete the manifest (`codeowners`, `documentation`, `issue_tracker`) and declare Home Assistant 2024.11.0 as the minimum version

## 0.2.2 (2026-10-07)

### Features

* add the integration icon ([706b3ed](https://github.com/username-andrey/xiaomi-smart-kettle-ha/commit/706b3edcedab3bc864a05f22a6b45a07d47ac403))

## 0.2.1 (2026-10-07)

### Bug Fixes

* make the Heat and Boil buttons work: send the target temperature, the keep-warm settings, the target mode and the mode settings in one request ([a1a7f88](https://github.com/username-andrey/xiaomi-smart-kettle-ha/commit/a1a7f88b49afd445c0c54e25817cb5e870d8e747))

## 0.2.0 (2026-10-07)

### Features

* add Heat and Boil buttons ([f49802a](https://github.com/username-andrey/xiaomi-smart-kettle-ha/commit/f49802a48c5470df72e3ac8d366fb6361aa175e5))
* translate entity names into English and Russian ([f49802a](https://github.com/username-andrey/xiaomi-smart-kettle-ha/commit/f49802a48c5470df72e3ac8d366fb6361aa175e5))

## 0.1.0 (2026-10-07)

### Features

* initial release: config flow with IP address and token, sensors, binary sensor, switches, numbers and a Stop button for the Xiaomi Smart Kettle 2 Pro (`xiaomi.kettle.v20`) ([8b5e631](https://github.com/username-andrey/xiaomi-smart-kettle-ha/commit/8b5e631c4d8aa89acf8fede85d0c24f534f781b0))
