-- Add folder_id column to oauth_tokens for storing user's preferred upload folder
ALTER TABLE oauth_tokens ADD COLUMN folder_id TEXT DEFAULT NULL;
