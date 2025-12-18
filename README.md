# CGV Schedule Tracker - Home Assistant Add-on

Monitor CGV movie schedules and receive Telegram notifications when schedules open.

## Features

- ✅ Lightweight (no browser required)
- ✅ Direct API calls with signature authentication
- ✅ Telegram notifications
- ✅ Configurable check interval
- ✅ Runs continuously until schedule is found

## Installation

1. Add this repository to Home Assistant:
   - Go to **Supervisor** → **Add-on Store**
   - Click the three dots (⋮) → **Repositories**
   - Add: `https://github.com/yourusername/cgv-schedule-tracker`

2. Install the add-on:
   - Find **CGV Schedule Tracker** in the add-on store
   - Click **Install**

3. Configure:
   - Go to **Configuration** tab
   - Fill in the required settings (see below)
   - Click **Save**

4. Start the add-on:
   - Click **Start**

## Configuration

| Option | Description | Required | Default |
|--------|-------------|----------|---------|
| `telegram_bot_token` | Telegram bot token from @BotFather | Yes | - |
| `telegram_chat_id` | Your Telegram chat ID | Yes | - |
| `target_date` | Date to check (YYYYMMDD format) | Yes | 20251231 |
| `movie_no` | CGV movie number | Yes | 30000774 |
| `site_no` | Theater site number (0013 = 용산아이파크몰) | Yes | 0013 |
| `check_interval` | Check interval in seconds | No | 60 |

### Getting Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow instructions
3. Copy the bot token

### Getting Telegram Chat ID

1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}` - that's your chat ID

## Usage

The add-on will:
1. Check the CGV API every `check_interval` seconds
2. Monitor for schedule availability on the target date
3. Send a Telegram notification when schedules are found
4. Stop automatically after sending notification

## Logs

View logs in Home Assistant:
- Go to **Supervisor** → **CGV Schedule Tracker** → **Log**

## Example Configuration

```yaml
telegram_bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
telegram_chat_id: "123456789"
target_date: "20251231"
movie_no: "30000774"
site_no: "0013"
check_interval: 60
```

## Support

For issues or questions, please open an issue on GitHub.

