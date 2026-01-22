import logging
import secrets

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from db.queries import (
    create_oauth_state,
    delete_oauth_state,
    save_oauth_token,
    get_oauth_token,
    delete_oauth_token,
    update_folder_id,
)
from services.google_auth import generate_auth_url, exchange_code, get_user_email
from services.google_drive import create_credentials, find_or_create_folder

router = Router()


@router.message(Command("connect"))
async def command_connect(message: Message) -> None:
    """Generate OAuth URL and send to user."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    existing = await get_oauth_token(user_id, chat_id, topic_id)
    if existing:
        email = existing.get("email", "Unknown")
        await message.answer(
            f"Already connected as {email}.\n"
            "Use /disconnect first if you want to connect a different account."
        )
        return

    state = secrets.token_urlsafe(32)
    await create_oauth_state(user_id, chat_id, topic_id, state)

    auth_url = generate_auth_url(state)

    await message.answer(
        "Click the link below to connect your Google Drive:\n\n"
        f"{auth_url}\n\n"
        "After authorizing, you'll be redirected to a page that won't load.\n"
        "Copy the <code>code</code> parameter from the URL and send it here.\n\n"
        "Example: if URL is <code>http://localhost/?code=4/0ABC...&amp;scope=...</code>\n"
        "Send me: <code>4/0ABC...</code>"
    )


@router.message(Command("disconnect"))
async def command_disconnect(message: Message) -> None:
    """Remove stored OAuth tokens."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    deleted = await delete_oauth_token(user_id, chat_id, topic_id)

    if deleted:
        await message.answer("Disconnected from Google Drive.")
    else:
        await message.answer("Not connected to Google Drive.")


@router.message(F.text.startswith("4/"))
async def handle_oauth_code(message: Message) -> None:
    """Handle OAuth authorization code from user."""
    if not message.from_user or not message.text:
        return

    code = message.text.strip()
    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    # Find the OAuth state for this user/chat/topic
    # We need to check if there's a pending state for this context
    # Since the code doesn't include the state, we look for any pending state
    # for this user+chat+topic combination
    from db.connection import get_pool

    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT state FROM oauth_states
        WHERE user_id = $1 AND chat_id = $2 AND topic_id IS NOT DISTINCT FROM $3
        ORDER BY created_at DESC
        LIMIT 1
        """,
        user_id,
        chat_id,
        topic_id,
    )

    if not row:
        await message.answer(
            "No pending connection request found.\n"
            "Use /connect to start the authorization process."
        )
        return

    state = row["state"]

    try:
        tokens = exchange_code(code)
        email = get_user_email(tokens["access_token"])

        await save_oauth_token(user_id, chat_id, topic_id, tokens, email)
        await delete_oauth_state(state)

        await message.answer(
            f"Successfully connected to Google Drive as {email}!\n"
            "You can now send files and I'll upload them to your Drive.\n\n"
            "Use /setfolder FolderName to specify a folder for uploads."
        )
    except Exception:
        logging.exception("OAuth code exchange failed")
        await message.answer(
            "Failed to connect. The code may be invalid or expired.\n"
            "Please try /connect again."
        )


@router.message(Command("setfolder"))
async def command_setfolder(message: Message) -> None:
    """Set upload folder for Google Drive."""
    if not message.from_user or not message.text:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    # Check for active connection
    token = await get_oauth_token(user_id, chat_id, topic_id)
    if not token:
        location = "this topic" if topic_id else "this chat"
        await message.answer(
            f"Not connected to Google Drive for {location}.\n"
            "Use /connect to link your account first."
        )
        return

    # Parse folder name from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Please specify a folder name.\n"
            "Usage: /setfolder FolderName\n"
            "Example: /setfolder MyBooks"
        )
        return

    folder_name = parts[1].strip()
    if not folder_name:
        await message.answer("Folder name cannot be empty.")
        return

    status_msg = await message.answer(f"Setting up folder '{folder_name}'...")

    try:
        credentials = create_credentials(token["access_token"], token["refresh_token"])
        folder_id = find_or_create_folder(credentials, folder_name)
        await update_folder_id(user_id, chat_id, topic_id, folder_id)

        await status_msg.edit_text(
            f"Files will now be uploaded to folder '{folder_name}'."
        )
    except Exception:
        logging.exception("Failed to set folder")
        await status_msg.edit_text(
            "Failed to set folder. Please try again or check your connection."
        )
