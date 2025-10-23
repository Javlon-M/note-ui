# Telegram Bot Setup Guide

This guide will help you connect your Telegram bot with channels and start sending messages.

## 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather and send `/newbot`
3. Follow the instructions to create your bot
4. Save the bot token (it looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## 2. Configure Environment Variables

Create a `.env` file in the backend directory with your bot token:

```bash
# Required: Your bot token from BotFather
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional: Default channel (if you want to set one)
TELEGRAM_CHANNEL_ID=-1001234567890
```

## 3. Add Your Bot to Channels

### For Public Channels:
1. Add your bot as an administrator to the channel
2. Give it permission to post messages
3. Use the channel username (e.g., `@mychannel`) as the channel ID

### For Private Channels/Groups:
1. Add your bot as an administrator
2. Give it permission to post messages
3. Use the numeric chat ID (e.g., `-1001234567890`)

### Finding Channel IDs:
- For public channels: Use `@channelname`
- For private channels: Forward a message from the channel to `@userinfobot` to get the numeric ID

## 4. Configure Channels

Set up your channels using the `TELEGRAM_CHANNELS` environment variable:

### Option 1: JSON Format
```bash
TELEGRAM_CHANNELS='[{"id":"-1001234567890","name":"My Private Channel"},{"id":"@mychannel","name":"My Public Channel"}]'
```

### Option 2: Simple Format
```bash
TELEGRAM_CHANNELS="My Channel=-1001234567890, Public Channel=@mychannel"
```

## 5. Start the Application

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   python -m app.main
   ```

3. Open your browser to `http://localhost:8000`

## 6. Using the Interface

1. **Check Bot Status**: The sidebar shows if your bot is connected (green dot) or disconnected (red dot)
2. **Channel Status**: Each channel shows ✓ (accessible) or ✗ (not accessible)
3. **Create Notes**: Click "New Note" to create a note for a specific channel
4. **Publish**: Click "Publish" to send your note to the selected channel

## Troubleshooting

### Bot Not Connected
- Check that `TELEGRAM_BOT_TOKEN` is set correctly
- Verify the token is valid by checking with BotFather

### Channel Not Accessible
- Make sure the bot is added as an administrator to the channel
- Check that the bot has permission to post messages
- Verify the channel ID is correct (numeric for private, @username for public)

### Publishing Fails
- Ensure the channel is accessible (shows ✓ in the sidebar)
- Check that your note has content (title or body)
- Verify the bot has posting permissions

## API Endpoints

- `GET /api/channels/` - List configured channels
- `GET /api/channels/status` - Check bot and channel status
- `POST /api/publish` - Publish content to a channel
- `POST /api/publish/test` - Test channel access without publishing
