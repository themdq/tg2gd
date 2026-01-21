# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BookSyncBot is a Telegram bot built with aiogram that integrates with Google Drive. It allows users to send files to their Google Drives. Bot supports telegram topics, so it can send files to different drives depends on topic.

## Development Commands

```bash
# Install dependencies
uv sync

# Run the bot
uv run python main.py

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run ty check
```

## Environment Variables

- `BOT_TOKEN` - Telegram bot token from @BotFather

## Architecture

Bot using:

- **aiogram 3.x** - Async Telegram Bot framework with Dispatcher pattern
- **Google API Client** - For Google Drive integration via OAuth2

The bot uses aiogram's decorator-based message handlers attached to a global `Dispatcher` instance.

## Deploy

Bot will be deployed on k3s server.
