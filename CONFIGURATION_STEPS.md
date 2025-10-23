# Configuration Steps for Telegram Bot Integration

## Step 1: Create .env file
Create a `.env` file in the `/backend` directory with the following content:

```bash
# Replace with your actual bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Default channel (optional)
TELEGRAM_CHANNEL_ID=your_default_channel_id_here

# Configure your channels here
# Format: JSON array or simple "Name=ID, Name2=ID2" format
# Examples:
# TELEGRAM_CHANNELS='[{"id":"-1001234567890","name":"My Private Channel"},{"id":"@mychannel","name":"My Public Channel"}]'
# TELEGRAM_CHANNELS="My Channel=-1001234567890, Public Channel=@mychannel"
TELEGRAM_CHANNELS=
```

## Step 2: Get your Bot Token
1. Open Telegram and search for `@BotFather`
2. Start a chat and send `/newbot`
3. Follow instructions to create your bot
4. Copy the token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 3: Add Bot to Your Channel
1. Add your bot as an administrator to your channel
2. Give it permission to post messages
3. Get the channel ID:
   - For public channels: Use `@channelname`
   - For private channels: Forward a message to `@userinfobot` to get numeric ID

## Step 4: Configure Channels
Add your channels to the `TELEGRAM_CHANNELS` variable in `.env`:

### Option 1: JSON Format
```bash
TELEGRAM_CHANNELS='[{"id":"-1001234567890","name":"My Private Channel"},{"id":"@mychannel","name":"My Public Channel"}]'
```

### Option 2: Simple Format
```bash
TELEGRAM_CHANNELS="My Channel=-1001234567890, Public Channel=@mychannel"
```

## Step 5: Test the Setup
1. Restart the server: `python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
2. Open http://localhost:8000
3. Check the sidebar for bot status (green dot = connected)
4. Check channel status (✓ = accessible, ✗ = not accessible)

## Step 6: Send Your First Message
1. Select a channel from the sidebar
2. Click "New Note"
3. Add a title and content
4. Click "Publish" to send to Telegram
