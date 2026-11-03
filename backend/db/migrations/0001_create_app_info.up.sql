-- Baseline migration: key/value table for application metadata.
CREATE TABLE app_info (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
