from datetime import datetime

from db.connection import get_pool


async def create_oauth_state(
    user_id: int, chat_id: int, topic_id: int | None, state: str
) -> None:
    """Store pending OAuth state for the authorization flow."""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO oauth_states (state, user_id, chat_id, topic_id)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (state) DO UPDATE SET
            user_id = $2, chat_id = $3, topic_id = $4, created_at = NOW()
        """,
        state,
        user_id,
        chat_id,
        topic_id,
    )


async def get_oauth_state(state: str) -> dict | None:
    """Validate and retrieve OAuth state. Returns None if not found."""
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT user_id, chat_id, topic_id FROM oauth_states WHERE state = $1",
        state,
    )
    if row:
        return {
            "user_id": row["user_id"],
            "chat_id": row["chat_id"],
            "topic_id": row["topic_id"],
        }
    return None


async def delete_oauth_state(state: str) -> None:
    """Clean up OAuth state after use."""
    pool = get_pool()
    await pool.execute("DELETE FROM oauth_states WHERE state = $1", state)


async def save_oauth_token(
    user_id: int,
    chat_id: int,
    topic_id: int | None,
    tokens: dict,
    email: str | None,
) -> None:
    """Store OAuth credentials for a user+chat+topic combination."""
    pool = get_pool()
    expires_at = tokens.get("expires_at")
    if isinstance(expires_at, datetime):
        expires_at = expires_at

    await pool.execute(
        """
        INSERT INTO oauth_tokens (user_id, chat_id, topic_id, email, access_token, refresh_token, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (user_id, chat_id, topic_id) DO UPDATE SET
            email = $4,
            access_token = $5,
            refresh_token = $6,
            expires_at = $7,
            updated_at = NOW()
        """,
        user_id,
        chat_id,
        topic_id,
        email,
        tokens["access_token"],
        tokens["refresh_token"],
        expires_at,
    )


async def get_oauth_token(
    user_id: int, chat_id: int, topic_id: int | None
) -> dict | None:
    """Retrieve OAuth credentials for a user+chat+topic combination."""
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT email, access_token, refresh_token, expires_at, folder_id
        FROM oauth_tokens
        WHERE user_id = $1 AND chat_id = $2 AND topic_id IS NOT DISTINCT FROM $3
        """,
        user_id,
        chat_id,
        topic_id,
    )
    if row:
        return {
            "email": row["email"],
            "access_token": row["access_token"],
            "refresh_token": row["refresh_token"],
            "expires_at": row["expires_at"],
            "folder_id": row["folder_id"],
        }
    return None


async def delete_oauth_token(user_id: int, chat_id: int, topic_id: int | None) -> bool:
    """Remove OAuth credentials. Returns True if a token was deleted."""
    pool = get_pool()
    result = await pool.execute(
        """
        DELETE FROM oauth_tokens
        WHERE user_id = $1 AND chat_id = $2 AND topic_id IS NOT DISTINCT FROM $3
        """,
        user_id,
        chat_id,
        topic_id,
    )
    return result == "DELETE 1"


async def update_oauth_token(
    user_id: int,
    chat_id: int,
    topic_id: int | None,
    access_token: str,
    expires_at: datetime,
) -> None:
    """Update access token and expiry after refresh."""
    pool = get_pool()
    await pool.execute(
        """
        UPDATE oauth_tokens
        SET access_token = $4, expires_at = $5, updated_at = NOW()
        WHERE user_id = $1 AND chat_id = $2 AND topic_id IS NOT DISTINCT FROM $3
        """,
        user_id,
        chat_id,
        topic_id,
        access_token,
        expires_at,
    )


async def update_folder_id(
    user_id: int,
    chat_id: int,
    topic_id: int | None,
    folder_id: str | None,
) -> None:
    """Set the upload folder for a user+chat+topic connection."""
    pool = get_pool()
    await pool.execute(
        """
        UPDATE oauth_tokens
        SET folder_id = $4, updated_at = NOW()
        WHERE user_id = $1 AND chat_id = $2 AND topic_id IS NOT DISTINCT FROM $3
        """,
        user_id,
        chat_id,
        topic_id,
        folder_id,
    )
