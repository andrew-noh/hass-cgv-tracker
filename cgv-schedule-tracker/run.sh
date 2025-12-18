#!/usr/bin/with-contenv bashio

# Get configuration from Home Assistant options
TELEGRAM_BOT_TOKEN=$(bashio::config 'telegram_bot_token')
TELEGRAM_CHAT_ID=$(bashio::config 'telegram_chat_id')
TARGET_DATE=$(bashio::config 'target_date')
MOVIE_NO=$(bashio::config 'movie_no')
SITE_NO=$(bashio::config 'site_no')
CHECK_INTERVAL=$(bashio::config 'check_interval')

# Export as environment variables
export TELEGRAM_BOT_TOKEN
export TELEGRAM_CHAT_ID
export TARGET_DATE
export MOVIE_NO
export SITE_NO
export CHECK_INTERVAL

# Log configuration (without sensitive data)
bashio::log.info "Starting CGV Schedule Tracker"
bashio::log.info "Target date: ${TARGET_DATE}"
bashio::log.info "Movie: ${MOVIE_NO}"
bashio::log.info "Theater: ${SITE_NO}"
bashio::log.info "Check interval: ${CHECK_INTERVAL}s"

# Validate required configuration
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
    bashio::log.error "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be configured"
    exit 1
fi

# Run the Python script
exec python3 /app/main.py

