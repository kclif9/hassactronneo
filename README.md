# Actron Air Neo Integration

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kclif9/hassactronneo)
![GitHub](https://img.shields.io/github/license/kclif9/hassactronneo)

This is a custom integration for Home Assistant to integrate the Actron Air Neo system.

## Installation

### Prerequisites

- Home Assistant (version 2023.3.0 or later recommended)
- An Actron Air Neo air conditioning system
- A valid Actron Air Neo account (username and password)
- Your Actron Air Neo system must be connected to the internet

### HACS (Home Assistant Community Store)

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Go to HACS > Integrations.
3. Click on the three dots in the top right corner and select "Custom repositories".
4. Add the repository URL: `https://github.com/kclif9/hassactronneo` and select "Integration".
5. Find "Actron Air Neo" in the list and click "Install".
6. Restart Home Assistant after installation.

### Manual Installation

1. Download the `custom_components` directory from the [latest release](https://github.com/kclif9/hassactronneo/releases/latest).
2. Copy the `custom_components/actronair_neo` directory to your Home Assistant configuration directory (typically `/config/custom_components/`).
3. Restart Home Assistant after installation.

## Configuration

### Configuration Parameters

The integration requires the following information during setup:

- **Username**: Your Actron Air Neo account username (email address)
- **Password**: Your Actron Air Neo account password

### Setup Process

1. In the Home Assistant UI, navigate to `Configuration` > `Devices & Services`.
2. Click the `+ Add Integration` button.
3. Search for `Actron Air Neo` and select it.
4. Enter your Actron Air Neo username and password.
5. The integration will connect to your Actron Air Neo account and discover all your connected devices.

### Configuration Notes

- The integration uses a pairing token for secure authentication with the Actron Neo API.
- One configuration entry is created per Actron Air Neo account.
- Each air conditioning unit under your account will be added as a separate device.

## Features

- **Climate Control**: Control your Actron Air Neo air conditioning units.
- **Sensors**: Monitor various sensors such as temperature, humidity, and system status.
- **Switches**: Control switches for continuous fan and zone control.

## Supported Platforms

- `climate`
- `sensor`
- `switch`

## Example Configuration

No YAML configuration is needed. The integration is configured via the Home Assistant UI.

## Troubleshooting

If you encounter issues, please check the Home Assistant logs for any error messages related to the `actronair_neo` integration.

Common issues:
- **Authentication errors**: Verify your username and password are correct.
- **Connection errors**: Ensure your Actron Air Neo system is connected to the internet.
- **API errors**: The Actron Air Neo cloud service might be temporarily unavailable.

## Removing the Integration

1. Go to `Configuration` > `Devices & Services`.
2. Find the Actron Air Neo integration card and click on it.
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
- [Actron Neo API](https://github.com/kclif9/actronneoapi)
