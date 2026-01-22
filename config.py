from os import getenv

BOT_TOKEN = getenv("BOT_TOKEN")
DATABASE_URL = getenv("DATABASE_URL")
GOOGLE_CLIENT_ID = getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = "http://localhost"

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/userinfo.email",
]
