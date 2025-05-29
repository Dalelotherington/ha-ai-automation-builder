#!/usr/bin/with-contenv bashio
# ==============================================================================
# Setup script for AI Automation Builder
# ==============================================================================

# Create required directories
mkdir -p /data/models

# Ensure we have the app files
if [ ! -d "/app" ]; then
    bashio::log.error "App directory missing!"
    exit 1
fi

# Verify Python is installed
if ! command -v python3 &> /dev/null; then
    bashio::log.error "Python3 not found! This is a required dependency."
    exit 1
fi

cd /app || bashio::exit.nok "Failed to change to app directory"

# Check for required Python files
if [ ! -f "/app/app.py" ]; then
    bashio::log.error "app.py file is missing!"
    exit 1
fi

# Set permissions
chmod +x /app/*.py
chmod +x /etc/services.d/app/run
chmod +x /etc/services.d/app/finish

# Create symlinks if needed
if [ ! -L /usr/bin/python ] && [ -f /usr/bin/python3 ]; then
    ln -sf /usr/bin/python3 /usr/bin/python
fi

# Check permissions on S6 scripts
if [ ! -x "/etc/services.d/app/run" ]; then
    bashio::log.error "Run script is not executable!"
    exit 1
fi

# Verify we can access Home Assistant API through supervisor
if bashio::supervisor.ping; then
    bashio::log.info "Successfully connected to the supervisor API!"
else
    bashio::log.warning "Failed to ping supervisor API - running in limited mode"
fi

# Test bashio token function directly
if type bashio::supervisor.token >/dev/null 2>&1; then
    bashio::log.info "bashio::supervisor.token function is available"
else
    bashio::log.error "bashio::supervisor.token function is NOT available!"
    # Create a wrapper function
    bashio::supervisor.token() {
        if [ -f "/data/options.json" ]; then
            jq --raw-output ".supervisor_token // empty" /data/options.json
        else
            echo ""
        fi
    }
    bashio::log.info "Created fallback function for token"
fi

# Show environment info
bashio::log.info "==== Environment Information ===="
bashio::log.info "Python Version: $(python3 --version)"
bashio::log.info "Bashio available: $(command -v bashio || echo 'Not found')"
bashio::log.info "Current directory: $(pwd)"
bashio::log.info "Directory listing:"
ls -la

# Test and ensure dependencies
if [ -f "/app/dependency_manager.py" ]; then
    bashio::log.info "Running dependency check..."
    python3 /app/dependency_manager.py || bashio::log.warning "Dependency check completed with warnings"
fi

bashio::log.info "Setup completed successfully" 