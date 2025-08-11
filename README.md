# Actron Air Integration

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kclif9/hassactronneo)
![GitHub](https://img.shields.io/github/license/kclif9/hassactronneo)

This is a custom integration for Home Assistant to integrate the Actron Air ecosystem. This integration currently supports the Actron Air Neo, but is targeted to support other systems in future. Let me know if you're keen to help test other Actron Air products.

This integration is currently the test version of the integration being submitted to Home Assistant for adding to the core integrations.

## Installation

### Prerequisites

- Home Assistant (version 2023.3.0 or later recommended)
- An Actron Air air conditioning system
- A valid Actron Air account (username and password)
- Your Actron Air system must be connected to the internet

### HACS (Home Assistant Community Store)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kclif9&repository=hassactronneo)

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Go to HACS > Integrations.
3. Click on the three dots in the top right corner and select "Custom repositories".
4. Add the repository URL: `https://github.com/kclif9/hassactronneo` and select "Integration".
5. Find "Actron Air" in the list and click "Install".
6. Restart Home Assistant after installation.

### Manual Installation

1. Download the `custom_components` directory from the [latest release](https://github.com/kclif9/hassactronneo/releases/latest).
2. Copy the `custom_components/actronair` directory to your Home Assistant configuration directory (typically `/config/custom_components/`).
3. Restart Home Assistant after installation.

## Configuration

### Configuration Parameters

The integration requires the following information during setup:

- **Username**: Your Actron Air account username (email address)
- **Password**: Your Actron Air account password

### Setup Process

1. In the Home Assistant UI, navigate to `Configuration` > `Devices & Services`.
2. Click the `+ Add Integration` button.
3. Search for `Actron Air` and select it.
4. When prompted with the oAuth link, click it and login to your Actron Air account.
5. The integration will connect to your Actron Air account and discover all your connected devices.

### Configuration Notes

- Each air conditioning unit under your account will be added as a separate device.

## Features

- **Climate Control**: Control your Actron Air air conditioning units.
- **Sensors**: Monitor various sensors such as temperature, humidity, and system status.
- **Switches**: Control switches for continuous fan and zone control.

## Supported Devices

This integration supports the following Actron Air devices:

- **Actron Air Neo Series**: All models of the Neo Series air conditioners
- **Zone Controllers**: Control individual zones within your system
- **Wall Controllers**: Compatible with wall controller units
- **Temperature/Humidity Sensors**: Compatible with remote temperature sensors

The integration does not currently support older Actron Air models, or those that are not part of the Neo ecosystem. We are keen to support other systems in future. Let me know if you're keen to help test other Actron Air products.

## Supported Functions

The integration supports the following functions:

### Climate Controls
- Turn the air conditioning system on/off
- Change operating mode (Cool, Heat, Fan, Auto)
- Set target temperature
- Change fan speed (Auto, Low, Medium, High)
- Enable/disable continuous fan operation

### Zone Controls
- Turn individual zones on/off
- Set zone-specific temperatures
- Monitor zone temperature and humidity

### Sensors
- System temperature sensors
- Zone temperature sensors
- System humidity sensors
- Zone humidity sensors
- Battery levels for wireless components
- System status indicators
- Fan speed indicators

## Data Updates

The integration updates data using the following approach:

- **Update Frequency**: Data is polled from the Actron Air cloud service every 30 seconds.
- **Update Method**: The integration uses a cloud polling approach as specified by the `iot_class: cloud_polling` in the integration manifest.
- **Coordinator Pattern**: All entities share a common update coordinator to minimize API calls and improve performance.
- **Token Refresh**: Authentication tokens are automatically refreshed when they expire.
- **API Limits**: The integration respects the API rate limits of the Actron Air cloud service to prevent lockouts.

## Example Use Cases

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

## Known Limitations

The integration has the following known limitations:

- **Cloud Dependency**: The integration relies on the Actron Air cloud service, so internet connectivity is required for operation.
- **Zone Configuration**: Zone names and configurations are determined controller and cannot be changed from Home Assistant.
- **System-Level Settings**: Some advanced system-level settings can only be modified through the wall controller.
- **Firmware Updates**: The integration does not support triggering firmware updates, which must be done through the wall controller.

## Troubleshooting

If you encounter issues, please check the Home Assistant logs for any error messages related to the `actronair` integration.

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
  - Update to the latest version of the integration
  - Check the GitHub repository for known issues

#### System Functionality Limitations
- **Symptom**: Cannot access certain features available in the official app
- **Solution**: Some advanced features are only available through the official app. Use the app for those functions.

### Log Checking

To check your logs for troubleshooting:

1. Go to Home Assistant "Settings" > "System" > "Logs"
2. Filter for "actronair" to see messages specific to this integration
3. Look for error messages that can help identify the issue

If you need further assistance, please open an issue on the [GitHub repository](https://github.com/kclif9/hassactronneo/issues) with the following information:
- Description of the problem
- Relevant log entries
- Home Assistant version
- Integration version

## Removing the Integration

1. Go to `Configuration` > `Devices & Services`.
2. Find the Actron Air integration card and click on it.
3. Click the three dots in the top-right corner and select "Delete".
4. Confirm the deletion.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add new feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Home Assistant](https://www.home-assistant.io/)
- [HACS](https://hacs.xyz/)
- [Actron Air Neo API](https://github.com/kclif9/actronneoapi)
