# Google OAuth Design for BookSyncBot

## Overview

Implement Google OAuth2 authentication in the Telegram bot to allow users to connect their Google Drive accounts on a per-topic basis. When users send files to a topic, the bot uploads them to the linked Google Drive.

## User Flow

1. User sends `/connect` in a Telegram topic
2. Bot generates OAuth URL with unique state (user_id + topic_id) and sends inline button
3. User clicks link, logs into Google, approves Drive access
4. Google shows authorization code (out-of-band flow)
5. User pastes code back to bot
6. Bot exchanges code for tokens, stores in PostgreSQL
7. Future file uploads in that topic go to the linked Drive

## Database Schema

```sql
-- Stores Google OAuth tokens per user per topic
CREATE TABLE google_tokens (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    topic_id BIGINT,  -- NULL means default/no topic
    google_email VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expiry TIMESTAMP NOT NULL,
    scopes TEXT NOT NULL,  -- JSON array of granted scopes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(telegram_user_id, topic_id)
);

-- Tracks pending OAuth flows (expires after 10 minutes)
CREATE TABLE oauth_states (
    state VARCHAR(64) PRIMARY KEY,  -- Random UUID
    telegram_user_id BIGINT NOT NULL,
    topic_id BIGINT,
    chat_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Bot Commands

| Command | Description |
|---------|-------------|
| `/connect` | Start OAuth flow for current topic |
| `/disconnect` | Remove Google account link for current topic |
| `/status` | Show connected Google account for current topic |

## Project Structure

```
BookSyncBot/
├── main.py
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py
│   │   ├── oauth.py
│   │   └── upload.py
│   └── middlewares/
│       └── __init__.py
├── services/
│   ├── __init__.py
│   ├── google_auth.py
│   └── google_drive.py
├── db/
│   ├── __init__.py
│   └── connection.py
├── config.py
└── migrations/
    └── 001_initial.sql
```

## Dependencies

- `asyncpg` - Async PostgreSQL driver (raw SQL, no ORM)

## Environment Variables

- `BOT_TOKEN` - Telegram bot token
- `DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret

## Error Handling

1. **Token refresh** - Check expiry before Drive API calls, refresh automatically
2. **Revoked access** - Catch `invalid_grant`, prompt to reconnect
3. **Expired OAuth state** - 10-minute timeout, show restart message
4. **Duplicate code submission** - Fail gracefully on second attempt
5. **No connection for topic** - Prompt user to `/connect`
6. **Upload failures** - Retry with backoff, then notify user
