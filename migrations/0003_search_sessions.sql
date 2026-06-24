CREATE TABLE IF NOT EXISTS search_sessions (
  id TEXT PRIMARY KEY,
  user_id INTEGER,
  query TEXT NOT NULL,
  normalized_query TEXT,
  results_json TEXT NOT NULL,
  total INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_sessions_user_created ON search_sessions(user_id, created_at);
