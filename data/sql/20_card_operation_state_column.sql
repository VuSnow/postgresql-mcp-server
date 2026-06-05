-- Add card_operation_state column to chat_sessions table
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS card_operation_state JSONB DEFAULT NULL;
