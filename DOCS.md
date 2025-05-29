# AI Automation Builder

This add-on allows you to create Home Assistant automations using natural language descriptions.

## How it works

The AI Automation Builder processes your natural language descriptions and converts them into functional Home Assistant automations in YAML format. You can then save them directly to your Home Assistant instance.

## Features

- **Natural Language Input**: Describe your automation ideas in plain English
- **Simple Interface**: Clean, easy-to-use web interface
- **Direct Integration**: Save automations directly to your Home Assistant configuration
- **Local Processing**: All processing happens on your Home Assistant instance

## Installation

1. Add this repository to your Home Assistant instance
2. Install the "AI Automation Builder" add-on
3. Start the add-on
4. Open the web UI from your Home Assistant sidebar

## Configuration

### Add-on Configuration

| Option | Description | Required |
|--------|-------------|----------|
| `api_key` | API key for external AI service (optional) | No |
| `model` | AI model to use for generating automations | No |
| `port` | Port for the web interface (default: 5001) | No |
| `ha_url` | Home Assistant URL (default: http://supervisor/core) | No |
| `ha_token` | Long-lived access token for Home Assistant | Yes, for saving automations |

## Usage

1. Open the AI Automation Builder from your Home Assistant sidebar
2. Type a description of the automation you want to create in natural language
   - Example: "Turn on the living room lights when motion is detected after sunset and turn them off after 10 minutes of no motion"
3. Click "Generate Automation"
4. Review the generated YAML automation
5. Click "Save to Home Assistant" to save it directly to your configuration

### Demo Mode

If you don't provide a Home Assistant token, the add-on will run in "Demo Mode." In this mode, you can still generate automations, but they won't be saved to your Home Assistant configuration.

## Integration with Home Assistant

The add-on uses the Home Assistant API to save automations directly to your configuration directory. To enable this feature:

1. Create a long-lived access token in Home Assistant
   - Go to your profile in Home Assistant
   - Scroll down to "Long-Lived Access Tokens"
   - Create a new token for this add-on
2. Enter this token in the add-on configuration
3. Restart the add-on

## Troubleshooting

If you encounter any issues:

1. Check the add-on logs for error messages
2. Verify that your Home Assistant instance can access the add-on
3. Make sure your Home Assistant token has the necessary permissions
4. Check that the port is not in use by another service

## Support

For bugs and feature requests, please [open an issue](https://github.com/Dalelotherington/ha-ai-automation-builder/issues) on GitHub.

## Future Plans

Future versions will include:
- AI-powered automation generation using LLMs
- Entity detection and validation
- Voice input for automation descriptions
- Integration with local LLMs via Ollama