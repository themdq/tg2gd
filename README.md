# BookSyncBot

A Telegram bot that uploads files to Google Drive. Supports per-chat and per-topic connections, allowing different Google accounts for different conversations.

## Features

- Upload any file type to Google Drive (documents, photos, videos, audio, voice messages)
- Per-chat/topic Google Drive connections
- Custom upload folders via `/setfolder`
- Automatic token refresh
- 20MB file size limit (Telegram bot API constraint)

## Commands

- `/start` - Welcome message and instructions
- `/connect` - Connect your Google Drive account
- `/disconnect` - Disconnect Google Drive
- `/status` - Check connection status
- `/setfolder FolderName` - Set upload destination folder

## Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- PostgreSQL database
- Google Cloud project with Drive API enabled

### Google Cloud Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Drive API
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials (Desktop app type)
5. Note your Client ID and Client Secret

### Environment Variables

Create a `.env` file:

```env
BOT_TOKEN=your_telegram_bot_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### Local Development

```bash
# Install dependencies
uv sync

# Start PostgreSQL and bot with Docker Compose
docker compose up -d

# Or run directly (requires DATABASE_URL)
uv run python main.py
```

### Development Commands

```bash
# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run ty check
```

## Docker Deployment

```bash
docker compose up -d
```

This starts:
- PostgreSQL database on port 5432
- Bot with hot-reload enabled

## Usage

1. Start a chat with the bot
2. Run `/connect` and follow the OAuth flow
3. Send any file to upload it to your Google Drive
4. Optionally use `/setfolder MyFolder` to organize uploads

## Project Structure

```
BookSyncBot/
├── main.py              # Entry point
├── config.py            # Environment configuration
├── bot/
│   └── handlers/        # Telegram command handlers
│       ├── start.py     # /start, /status
│       ├── oauth.py     # /connect, /disconnect, /setfolder
│       └── upload.py    # File upload handling
├── services/
│   ├── google_auth.py   # OAuth flow
│   └── google_drive.py  # Drive API operations
├── db/
│   ├── connection.py    # Database pool
│   └── queries.py       # SQL queries
└── migrations/          # Database schema
```

## License

MIT
