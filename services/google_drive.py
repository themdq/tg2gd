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


def find_or_create_folder(credentials: Credentials, folder_name: str) -> str:
    """Find existing folder by name or create a new one. Returns folder_id."""
    service = build("drive", "v3", credentials=credentials)

    # Search for existing folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()

    if results.get("files"):
        return results["files"][0]["id"]

    # Create folder if not found
    metadata = {"name": folder_name, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_file(
    credentials: Credentials,
    file_content: BytesIO,
    file_name: str,
    mime_type: str,
    folder_id: str | None = None,
) -> str:
    """Upload file to Google Drive and return the shareable link."""
    service = build("drive", "v3", credentials=credentials)

    file_metadata: dict[str, str | list[str]] = {"name": file_name}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(file_content, mimetype=mime_type, resumable=True)

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    return file.get("webViewLink", f"https://drive.google.com/file/d/{file['id']}/view")
