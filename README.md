# Actron Air Neo Integration

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kclif9/hassactronneo)
![GitHub](https://img.shields.io/github/license/kclif9/hassactronneo)

This is a custom integration for Home Assistant to integrate the Actron Air Neo system.

## Installation

### HACS (Home Assistant Community Store)

1. Ensure that [HACS](https://hacs.xyz/) is installed.
2. Go to HACS > Integrations.
3. Click on the three dots in the top right corner and select "Custom repositories".
4. Add the repository URL: `https://github.com/kclif9/hassactronneo` and select "Integration".
5. Find "Actron Air Neo" in the list and click "Install".

### Manual Installation

1. Download the `custom_components` directory from the [latest release](https://github.com/kclif9/hassactronneo/releases/latest).
2. Copy the `custom_components/actronair_neo` directory to your Home Assistant configuration directory.

## Configuration

1. In the Home Assistant UI, navigate to `Configuration` > `Devices & Services`.
2. Click the `+ Add Integration` button.
3. Search for `Actron Air Neo` and follow the setup instructions.

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
