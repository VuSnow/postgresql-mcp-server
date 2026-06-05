-- Agent memory table for advisory agents (finance planning, etc.)
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(20) NOT NULL,
    session_id VARCHAR(100),
    domain VARCHAR(50) NOT NULL,
    memory_key VARCHAR(100) NOT NULL,
    memory_value JSONB NOT NULL,
    computed_at TIMESTAMP NOT NULL DEFAULT now(),
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now(),

    CONSTRAINT uq_agent_memory UNIQUE (user_id, session_id, domain, memory_key)
);

CREATE INDEX IF NOT EXISTS idx_agent_memory_lookup ON agent_memory(user_id, domain);
CREATE INDEX IF NOT EXISTS idx_agent_memory_expires ON agent_memory(expires_at) WHERE expires_at IS NOT NULL;
