#!/usr/bin/env bash

# Legacy entry point script
# This is kept for backward compatibility but isn't used directly with newer Home Assistant add-ons

echo "AI Automation Builder starting..."
echo "This script is maintained for compatibility only. The S6 overlay will start the service."

# This will be handled by S6-overlay in newer HA add-ons
cd /app
python3 app.py