CREATE TABLE users (
    id               INTEGER PRIMARY KEY,
    platform         TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    username         TEXT,
    role             TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin','banned')),
    locale           TEXT NOT NULL DEFAULT 'en',
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at     TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (platform, platform_user_id)
);

CREATE TABLE user_settings (
    user_id INTEGER NOT NULL REFERENCES users(id),
    key     TEXT NOT NULL,
    value   TEXT NOT NULL,
    PRIMARY KEY (user_id, key)
);

CREATE TABLE audit_log (
    id               INTEGER PRIMARY KEY,
    user_id          INTEGER REFERENCES users(id),
    platform         TEXT,
    platform_user_id TEXT,
    command          TEXT NOT NULL,
    args             TEXT,
    result           TEXT NOT NULL CHECK (result IN ('ok','error','denied')),
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_user ON audit_log (user_id, created_at);
CREATE INDEX idx_users_platform ON users (platform, platform_user_id);
