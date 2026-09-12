-- Week 2: Scheduled jobs tables

CREATE TABLE scheduled_jobs (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL UNIQUE,
    job_type         TEXT NOT NULL,              -- 'cron' | 'interval'
    schedule         TEXT NOT NULL,              -- cron expr or interval seconds
    enabled          INTEGER NOT NULL DEFAULT 1, -- SQLite uses INTEGER for BOOLEAN
    last_run_at      TEXT,
    next_run_at      TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE job_runs (
    id               INTEGER PRIMARY KEY,
    job_id           INTEGER NOT NULL REFERENCES scheduled_jobs(id),
    started_at       TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at      TEXT,
    status           TEXT NOT NULL,              -- 'running' | 'success' | 'failed'
    result_summary   TEXT,                       -- e.g., "Sent to 42 users"
    error_message    TEXT,
    output_data      TEXT                        -- JSON blob of results
);

CREATE TABLE job_deliveries (
    id               INTEGER PRIMARY KEY,
    job_run_id       INTEGER NOT NULL REFERENCES job_runs(id),
    platform         TEXT NOT NULL,
    platform_user_id TEXT NOT NULL,
    delivered_at     TEXT NOT NULL DEFAULT (datetime('now')),
    message_id       TEXT                        -- platform's message ID
);

CREATE TABLE price_alerts (
    id               INTEGER PRIMARY KEY,
    user_id          INTEGER NOT NULL REFERENCES users(id),
    symbol           TEXT NOT NULL,              -- 'BTC', 'ETH', etc.
    condition        TEXT NOT NULL,              -- 'above' | 'below'
    threshold        REAL NOT NULL,              -- price threshold
    triggered        INTEGER NOT NULL DEFAULT 0, -- has alert fired?
    triggered_at     TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_job_runs_job_id ON job_runs(job_id);
CREATE INDEX idx_job_runs_started_at ON job_runs(started_at);
CREATE INDEX idx_job_deliveries_job_run_id ON job_deliveries(job_run_id);
CREATE INDEX idx_price_alerts_user_id ON price_alerts(user_id);
CREATE INDEX idx_price_alerts_triggered ON price_alerts(triggered);
