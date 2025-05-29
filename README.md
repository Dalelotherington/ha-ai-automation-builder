# AI Automation Builder for Home Assistant

Create Home Assistant automations using natural language with a local LLM.

## About

AI Automation Builder is a Home Assistant add-on that allows you to create automations using natural language descriptions. It uses a local LLM (Language Learning Model) to interpret your descriptions and convert them into Home Assistant automations.

## Features

- Create automations from natural language descriptions
- Browse and test Home Assistant entities directly in the UI
- Support for running with or without a local LLM
- Uses lightweight TinyLlama model by default
- Direct integration with Home Assistant through the Supervisor API

## Installation

1. Add this repository to your Home Assistant instance:
   - Navigate to Settings → Add-ons → Add-on Store
   - Click the menu icon in the top right and select "Repositories"
   - Add the repository URL: `https://github.com/yourusername/ha-ai_automation_builder`
   - Click "Add"

2. Find the "AI Automation Builder" add-on in the add-on store and install it.

3. Configure the add-on:
   - Port: Default is 5001 (change only if needed)
   - Debug: Set to true for more verbose logging
   - Use LLM: Enable/disable the local LLM
   - LLM Model: Select model to use (default is tinyllama.gguf)

4. Start the add-on and open the web UI.

## Usage

1. Open the AI Automation Builder web UI.
2. Navigate to the "Create Automation" tab.
3. Enter a description of what you want your automation to do.
4. Click "Generate Automation" to create the automation.
5. Review the generated YAML.
6. Click "Save to Home Assistant" to save the automation.

## Troubleshooting

### Common Issues

- **Error 127 when starting**: This indicates a missing dependency or script error. Check that all required files are in place.
- **"Home Assistant token not available"**: The add-on cannot access the Supervisor API. Make sure you've granted the required permissions.
- **No entities showing**: Ensure the add-on has permission to access the Home Assistant API.

### Logs

To view logs:
1. Navigate to Settings → Add-ons → AI Automation Builder
2. Click the "Logs" tab

### Debugging

If you enable debug mode in the configuration, the add-on will output more detailed logs that can help diagnose issues.

## Changelog

### 1.0.6
- Fixed issue with Home Assistant token access
- Added better error handling for API requests
- Improved stability and robustness of the startup sequence
- Added timeout handling for API requests

### 1.0.5
- Initial release with basic functionality

## Support

If you need help or want to report an issue, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License. 