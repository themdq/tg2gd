from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from db.queries import get_oauth_token

router = Router()


@router.message(CommandStart())
async def command_start(message: Message) -> None:
    """Welcome message with instructions."""
    user_name = message.from_user.full_name if message.from_user else "there"
    await message.answer(
        f"Hello, {user_name}!\n\n"
        "I can sync files to your Google Drive.\n\n"
        "Commands:\n"
        "/connect - Connect your Google Drive\n"
        "/disconnect - Disconnect your Google Drive\n"
        "/status - Check connection status\n\n"
        "Once connected, just send me any file and I'll upload it to your Drive."
    )


@router.message(Command("status"))
async def command_status(message: Message) -> None:
    """Show connection status for current topic."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    token = await get_oauth_token(user_id, chat_id, topic_id)

    if token:
        email = token.get("email", "Unknown")
        await message.answer(f"Connected to Google Drive as {email}")
    else:
        location = "this topic" if topic_id else "this chat"
        await message.answer(
            f"Not connected to Google Drive for {location}.\n"
            "Use /connect to link your account."
        )
