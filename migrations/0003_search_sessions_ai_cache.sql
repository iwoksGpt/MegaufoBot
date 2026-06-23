CREATE TABLE IF NOT EXISTS search_sessions (
  session_id TEXT PRIMARY KEY,
  user_id INTEGER,
  query TEXT NOT NULL,
  normalized_query TEXT,
  language TEXT DEFAULT 'fa',
  results_json TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_sessions_user_created ON search_sessions(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_cache (
  title_id TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  provider TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
