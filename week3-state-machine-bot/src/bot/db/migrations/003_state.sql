-- Week 3: Conversation state machine persistence

CREATE TABLE conversation_states (
    id               INTEGER PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    workflow         TEXT NOT NULL,
    state            TEXT NOT NULL,
    data             TEXT NOT NULL DEFAULT '{}',
    status           TEXT NOT NULL DEFAULT 'active', -- 'active' | 'completed' | 'cancelled'
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_conversation_user_active
    ON conversation_states(user_id, status)
    WHERE status = 'active';
