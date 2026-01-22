import logging
from io import BytesIO

from aiogram import Router, F, Bot
from aiogram.types import Message, Document, PhotoSize, Video, Audio, Voice, VideoNote
from google.auth.exceptions import RefreshError

from db.queries import get_oauth_token, update_oauth_token
from services.google_auth import refresh_access_token
from services.google_drive import create_credentials, is_token_expired, upload_file

router = Router()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB Telegram limit


def get_file_info(
    message: Message,
) -> tuple[str, str, str, int] | None:
    """Extract file_id, name, mime_type, size from any file type."""
    if message.document:
        doc: Document = message.document
        return (
            doc.file_id,
            doc.file_name or "document",
            doc.mime_type or "application/octet-stream",
            doc.file_size or 0,
        )
    if message.photo:
        photo: PhotoSize = message.photo[-1]  # Largest size
        return (
            photo.file_id,
            "photo.jpg",
            "image/jpeg",
            photo.file_size or 0,
        )
    if message.video:
        video: Video = message.video
        return (
            video.file_id,
            video.file_name or "video.mp4",
            video.mime_type or "video/mp4",
            video.file_size or 0,
        )
    if message.audio:
        audio: Audio = message.audio
        return (
            audio.file_id,
            audio.file_name or "audio.mp3",
            audio.mime_type or "audio/mpeg",
            audio.file_size or 0,
        )
    if message.voice:
        voice: Voice = message.voice
        return (
            voice.file_id,
            "voice.ogg",
            voice.mime_type or "audio/ogg",
            voice.file_size or 0,
        )
    if message.video_note:
        video_note: VideoNote = message.video_note
        return (
            video_note.file_id,
            "video_note.mp4",
            "video/mp4",
            video_note.file_size or 0,
        )
    return None


async def ensure_valid_token(
    token: dict, user_id: int, chat_id: int, topic_id: int | None
) -> dict:
    """Refresh token if expired, returning updated token dict."""
    if not is_token_expired(token.get("expires_at")):
        return token

    refreshed = refresh_access_token(token["refresh_token"])
    await update_oauth_token(
        user_id, chat_id, topic_id, refreshed["access_token"], refreshed["expires_at"]
    )
    return {
        **token,
        "access_token": refreshed["access_token"],
        "expires_at": refreshed["expires_at"],
    }


@router.message(F.document | F.photo | F.video | F.audio | F.voice | F.video_note)
async def handle_file_upload(message: Message, bot: Bot) -> None:
    """Handle file uploads to Google Drive."""
    if not message.from_user:
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    token = await get_oauth_token(user_id, chat_id, topic_id)

    if not token:
        location = "this topic" if topic_id else "this chat"
        await message.answer(
            f"Not connected to Google Drive for {location}.\n"
            "Use /connect to link your account first."
        )
        return

    file_info = get_file_info(message)
    if not file_info:
        return

    file_id, file_name, mime_type, file_size = file_info

    if file_size > MAX_FILE_SIZE:
        await message.answer(
            f"File is too large ({file_size / 1024 / 1024:.1f}MB).\n"
            "Telegram bots can only download files up to 20MB."
        )
        return

    status_msg = await message.answer(f"Uploading {file_name} to Google Drive...")

    try:
        token = await ensure_valid_token(token, user_id, chat_id, topic_id)
    except RefreshError:
        await status_msg.edit_text(
            "Your Google Drive connection has expired.\n"
            "Please use /disconnect and then /connect to reconnect."
        )
        return
    except Exception:
        logging.exception("Token refresh failed")
        await status_msg.edit_text(
            "Failed to refresh Google Drive connection.\n"
            "Please try again or use /disconnect and /connect to reconnect."
        )
        return

    try:
        file = await bot.get_file(file_id)
        if not file.file_path:
            await status_msg.edit_text(
                "Failed to get file from Telegram. Please try again."
            )
            return
        file_content = BytesIO()
        await bot.download_file(file.file_path, file_content)
        file_content.seek(0)
    except Exception:
        logging.exception("Failed to download file from Telegram")
        await status_msg.edit_text(
            "Failed to download file from Telegram. Please try again."
        )
        return

    try:
        credentials = create_credentials(token["access_token"], token["refresh_token"])
        drive_link = upload_file(credentials, file_content, file_name, mime_type)
        await status_msg.edit_text(f"Uploaded to Google Drive:\n{drive_link}")
    except RefreshError:
        await status_msg.edit_text(
            "Your Google Drive access has been revoked.\n"
            "Please use /disconnect and then /connect to reconnect."
        )
    except Exception:
        logging.exception("Failed to upload file to Google Drive")
        await status_msg.edit_text(
            "Failed to upload file to Google Drive. Please try again."
        )
