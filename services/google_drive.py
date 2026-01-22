from datetime import datetime, timedelta, timezone
from io import BytesIO

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


def create_credentials(access_token: str, refresh_token: str) -> Credentials:
    """Create Google Credentials object from tokens."""
    return Credentials(
        token=access_token,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )


def is_token_expired(expires_at: datetime | None) -> bool:
    """Check if token needs refresh (5-minute buffer)."""
    if expires_at is None:
        return True
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now >= expires_at - timedelta(minutes=5)


def upload_file(
    credentials: Credentials, file_content: BytesIO, file_name: str, mime_type: str
) -> str:
    """Upload file to Google Drive and return the shareable link."""
    service = build("drive", "v3", credentials=credentials)

    file_metadata = {"name": file_name}
    media = MediaIoBaseUpload(file_content, mimetype=mime_type, resumable=True)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    return file.get("webViewLink", f"https://drive.google.com/file/d/{file['id']}/view")
