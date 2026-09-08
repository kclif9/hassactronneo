# Actron Air Integration

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kclif9/hassactronneo)
![GitHub](https://img.shields.io/github/license/kclif9/hassactronneo)

This repository contains the legacy custom Actron Air integration for Home Assistant.

> [!WARNING]
> This custom integration is deprecated and no longer maintained.
>
> Actron Air support is now built into Home Assistant. Please migrate to the
> [official Home Assistant integration](https://www.home-assistant.io/integrations/actron_air/)
> and remove this custom integration from HACS.
>
> No further bug fixes or feature updates will be made here.

## Migration

Remove this custom integration from HACS and configure the official Home Assistant
[Actron Air integration](https://www.home-assistant.io/integrations/actron_air/).
The remaining sections describe the legacy integration and are provided for
reference only.

## Legacy Configuration

### Setup Process

The integration uses an **OAuth2 Device Code** flow for authentication:

1. In the Home Assistant UI, navigate to `Configuration` > `Devices & Services`.
2. Click the `+ Add Integration` button.
3. Search for `Actron Air` and select it.
4. A link and authorization code will be displayed. Open the link and authorize on the Actron Air website.
5. Once authorized, the integration will automatically complete setup and discover all your connected devices.

### Configuration Notes

- Each air conditioning unit under your account will be added as a separate device.
- Reauthentication is supported if your token expires — Home Assistant will prompt you to re-authorize.
- The integration can also be discovered automatically via DHCP for Neo devices.

## Legacy Features

- **Climate Control**: Full control of your AC system and individual zones
- **Sensors**: Compressor diagnostics, outdoor temperature, and wireless peripheral readings
- **Binary Sensors**: Filter cleaning alerts and defrost mode status
- **Switches**: Away mode, continuous fan, quiet mode, and turbo mode
- **Covers**: Read-only zone damper position monitoring
- **Diagnostics**: Full system and status data export with sensitive fields redacted

## Legacy Supported Devices

The legacy integration supported the following Actron Air devices:

- **Actron Air Neo Series**: All models of the Neo Series air conditioners
- **Actron Air Que Series**: Que Series air conditioners
- **Zone Controllers**: Control individual zones within your system
- **Wall Controllers**: Compatible with wall controller units
- **Wireless Peripherals**: Temperature, humidity, and battery sensors

The integration does not currently support older Actron Air models, or those that are not part of the Neo/Que ecosystem. Other systems were not supported by the legacy integration.

## Entities

### Climate

| Entity | Features | Notes |
|---|---|---|
| AC System | Target temperature, fan mode, HVAC mode, on/off | HVAC modes: Cool, Heat, Fan, Auto, Dry. Fan modes: Auto, Low, Medium, High. Exposes current temperature and humidity. |
| Zone (per zone) | Target temperature, on/off | One entity per configured zone. Exposes current temperature and humidity. No independent fan mode. |

### Sensors

**System-level** (on the AC device):

| Sensor | Device Class | Unit | Enabled by Default |
|---|---|---|---|
| Outdoor temperature | Temperature | °C | Yes |
| Compressor mode | — | — | No |
| Compressor chasing temperature | Temperature | °C | No |
| Compressor live temperature | Temperature | °C | No |
| Compressor power | Power | W | No |
| Compressor speed | — | — | No |
| Compressor capacity | — | % | No |
| Fan speed | — | RPM | No |

**Wireless peripherals** (per sensor device):

| Sensor | Device Class | Unit |
|---|---|---|
| Temperature | Temperature | °C |
| Humidity | Humidity | % |
| Battery | Battery | % |

### Binary Sensors

| Sensor | Device Class | Category |
|---|---|---|
| Clean filter | Problem | Diagnostic |
| Defrost mode | Running | Diagnostic |

### Switches

All switches are configuration entities.

| Switch | Condition |
|---|---|
| Away mode | Always available |
| Continuous fan | Always available |
| Quiet mode | Always available |
| Turbo mode | Only if supported by hardware |

### Covers

| Entity | Device Class | Notes |
|---|---|---|
| Zone damper position | Damper | Read-only. One per zone. Reports current position and open/closed state. |

## Legacy Data Updates

The legacy integration updates data using the following approach:

- **Update Frequency**: Data is polled from the Actron Air cloud service every 30 seconds.
- **Update Method**: The integration uses a cloud polling approach as specified by the `iot_class: cloud_polling` in the integration manifest.
- **Coordinator Pattern**: All entities share a common update coordinator to minimize API calls and improve performance.
- **Token Refresh**: Authentication tokens are automatically refreshed when they expire.
- **API Limits**: The integration respects the API rate limits of the Actron Air cloud service to prevent lockouts.

## Legacy Example Use Cases

Here are some common use cases for the Actron Air integration:

### Basic Climate Automation

```yaml
# Turn on AC when temperature rises above threshold
automation:
  - alias: "Turn on AC when hot"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 26
    action:
      service: climate.set_hvac_mode
      target:
        entity_id: climate.living_room
      data:
        hvac_mode: cool
```

### Zone-Based Control

```yaml
# Turn on bedroom zone at night
automation:
  - alias: "Bedroom AC at night"
    trigger:
      platform: time
      at: "22:00:00"
    condition:
      condition: numeric_state
      entity_id: sensor.bedroom_temperature
      above: 24
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom_zone
        data:
          temperature: 22
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.bedroom_zone
        data:
          hvac_mode: cool
```

### Using Continuous Fan Mode

```yaml
# Set continuous fan mode during certain hours
automation:
  - alias: "Continuous fan during day"
    trigger:
      platform: time
      at: "09:00:00"
    action:
      service: switch.turn_on
      target:
        entity_id: switch.neo_continuous_fan
```

## Legacy Known Limitations

The legacy integration has the following known limitations:

- **Cloud Dependency**: The integration relies on the Actron Air cloud service, so internet connectivity is required for operation.
- **Zone Configuration**: Zone names and configurations are determined controller and cannot be changed from Home Assistant.
- **System-Level Settings**: Some advanced system-level settings can only be modified through the wall controller.
- **Firmware Updates**: The integration does not support triggering firmware updates, which must be done through the wall controller.

## Legacy Troubleshooting

No support is provided for this legacy integration. Existing users can check the
Home Assistant logs for error messages related to the `actronair` integration.

### Common Issues

#### Authentication Errors

- **Symptom**: Unable to authenticate, entities show as unavailable
- **Possible Causes**:
  - Incorrect username or password
  - Expired authentication token
  - Account has been locked out due to too many failed attempts
- **Solutions**:
  - Verify your credentials are correct
  - Go to the integration in Home Assistant, click "Configure" and re-enter your credentials
  - Wait a few minutes if you suspect a rate limit or lockout

#### Connection Errors

- **Symptom**: Entities unavailable, cannot control system
- **Possible Causes**:
  - Actron Air cloud service is down
  - Your internet connection is disrupted
  - Your Actron system is offline
- **Solutions**:
  - Check your internet connection
  - Verify the Actron Air system is powered on and connected to WiFi
  - Check if the official Actron Air app can connect to your system

#### Zone Control Issues

- **Symptom**: Cannot control individual zones
- **Possible Causes**:
  - Zone controller is offline
  - System-level issue preventing zone control
- **Solutions**:
  - Check if zones can be controlled from the official app
  - Ensure the main system is running and available
  - Check that zone controllers have power

#### API Errors

- **Symptom**: Errors in logs mentioning API issues, "too many requests", or timeouts
- **Possible Causes**:
  - Rate limiting by the Actron Air cloud service
  - API changes by Actron Air
- **Solutions**:
  - Reduce the number of automations that control the system
  - Migrate to the official Home Assistant integration
  - Check the GitHub repository for known issues

#### System Functionality Limitations

- **Symptom**: Cannot access certain features available in the official app
- **Solution**: Some advanced features are only available through the official app. Use the app for those functions.

### Log Checking

To check your logs for troubleshooting:

1. Go to Home Assistant "Settings" > "System" > "Logs"
2. Filter for "actronair" to see messages specific to this integration
3. Look for error messages that can help identify the issue

For new issues, use the official Home Assistant integration's support channels.

## Removing the Legacy Integration

1. Go to `Configuration` > `Devices & Services`.
2. Find the Actron Air integration card and click on it.
3. Click the three dots in the top-right corner and select "Delete".
4. Confirm the deletion.

## Contributing

This repository is no longer accepting feature or bug-fix contributions.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [Actron Air Neo API](https://github.com/kclif9/actronneoapi)
